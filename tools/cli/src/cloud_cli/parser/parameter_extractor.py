"""Parameter extractor for stack directories"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import yaml

from .typescript_parser import TypeScriptParser, InputParameter, OutputParameter, ParseResult


class ParameterExtractor:
    """Extract parameters from stack directory"""

    def __init__(self):
        """Initialize the extractor"""
        self.parser = TypeScriptParser()

    def extract_from_stack(
        self,
        stack_dir: Path,
        stack_name: Optional[str] = None
    ) -> Dict:
        """
        Extract parameters from a stack directory

        Args:
            stack_dir: Path to the stack directory
            stack_name: Optional stack name (defaults to directory name)

        Returns:
            Dictionary with extracted parameter information
        """
        if not stack_dir.exists():
            return {
                "success": False,
                "error": f"Stack directory not found: {stack_dir}"
            }

        if stack_name is None:
            stack_name = stack_dir.name

        # Find the main TypeScript file (index.ts or <stack-name>.ts)
        ts_file = self._find_main_typescript_file(stack_dir, stack_name)
        if ts_file is None:
            return {
                "success": False,
                "error": f"No TypeScript file found in {stack_dir}"
            }

        # Parse the TypeScript file
        result = self.parser.parse_file(ts_file)

        if not self.parser.validate_extraction():
            return {
                "success": False,
                "error": f"Failed to parse {ts_file}",
                "errors": result.errors
            }

        # Convert to template format
        template_data = self._convert_to_template_format(result)

        return {
            "success": True,
            "stack_name": stack_name,
            "source_file": str(ts_file),
            "parameters": template_data,
            "warnings": result.warnings
        }

    def _find_main_typescript_file(
        self,
        stack_dir: Path,
        stack_name: str
    ) -> Optional[Path]:
        """
        Find the main TypeScript file in the stack directory

        Looks for:
        1. index.ts
        2. <stack-name>.ts
        3. First .ts file found
        """
        # Check for index.ts
        index_file = stack_dir / "index.ts"
        if index_file.exists():
            return index_file

        # Check for <stack-name>.ts
        named_file = stack_dir / f"{stack_name}.ts"
        if named_file.exists():
            return named_file

        # Find first .ts file
        ts_files = list(stack_dir.glob("*.ts"))
        if ts_files:
            return ts_files[0]

        return None

    def _convert_to_template_format(self, result: ParseResult) -> Dict:
        """
        Convert ParseResult to template format

        Args:
            result: ParseResult from parser

        Returns:
            Dictionary in template format with inputs and outputs
        """
        template = {
            "inputs": {},
            "outputs": {}
        }

        # Convert inputs
        for input_param in result.inputs:
            template["inputs"][input_param.name] = {
                "type": input_param.type,
                "required": input_param.required,
                "secret": input_param.secret
            }

            if input_param.default is not None:
                template["inputs"][input_param.name]["default"] = input_param.default

            if input_param.description:
                template["inputs"][input_param.name]["description"] = input_param.description

        # Convert outputs
        for output_param in result.outputs:
            template["outputs"][output_param.name] = {
                "type": output_param.type
            }

            if output_param.description:
                template["outputs"][output_param.name]["description"] = output_param.description

        return template

    def extract_from_multiple_stacks(
        self,
        stacks_base_dir: Path,
        stack_names: Optional[List[str]] = None
    ) -> Dict[str, Dict]:
        """
        Extract parameters from multiple stacks

        Args:
            stacks_base_dir: Base directory containing stack directories
            stack_names: Optional list of stack names to process (defaults to all)

        Returns:
            Dictionary mapping stack names to extraction results
        """
        results = {}

        if stack_names is None:
            # Process all subdirectories
            stack_names = [
                d.name for d in stacks_base_dir.iterdir()
                if d.is_dir() and not d.name.startswith('.')
            ]

        for stack_name in stack_names:
            stack_dir = stacks_base_dir / stack_name
            result = self.extract_from_stack(stack_dir, stack_name)
            results[stack_name] = result

        return results

    def generate_template_file(
        self,
        stack_dir: Path,
        output_path: Path,
        stack_name: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Generate a template YAML file from stack code

        Args:
            stack_dir: Path to the stack directory
            output_path: Path where to write the template YAML
            stack_name: Optional stack name

        Returns:
            Tuple of (success, error_message)
        """
        extraction_result = self.extract_from_stack(stack_dir, stack_name)

        if not extraction_result["success"]:
            return False, extraction_result.get("error", "Unknown error")

        # Create template structure
        template = {
            "name": extraction_result["stack_name"],
            "parameters": extraction_result["parameters"]
        }

        # Write to YAML file
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                yaml.dump(template, f, default_flow_style=False, sort_keys=False)
            return True, None
        except Exception as e:
            return False, f"Failed to write template: {str(e)}"

    def compare_with_template(
        self,
        stack_dir: Path,
        template_path: Path,
        stack_name: Optional[str] = None
    ) -> Dict:
        """
        Compare extracted parameters with existing template

        Args:
            stack_dir: Path to stack directory
            template_path: Path to existing template
            stack_name: Optional stack name

        Returns:
            Dictionary with comparison results
        """
        # Extract from code
        extraction = self.extract_from_stack(stack_dir, stack_name)
        if not extraction["success"]:
            return {
                "success": False,
                "error": extraction.get("error", "Extraction failed")
            }

        # Load existing template
        try:
            with open(template_path, 'r') as f:
                template = yaml.safe_load(f)
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to load template: {str(e)}"
            }

        # Compare
        extracted_params = extraction["parameters"]
        template_params = template.get("parameters", {})

        differences = {
            "missing_in_template": [],
            "missing_in_code": [],
            "type_mismatches": [],
            "matches": []
        }

        # Check inputs
        extracted_inputs = set(extracted_params.get("inputs", {}).keys())
        template_inputs = set(template_params.get("inputs", {}).keys())

        differences["missing_in_template"].extend(
            [f"input:{name}" for name in extracted_inputs - template_inputs]
        )
        differences["missing_in_code"].extend(
            [f"input:{name}" for name in template_inputs - extracted_inputs]
        )

        # Check outputs
        extracted_outputs = set(extracted_params.get("outputs", {}).keys())
        template_outputs = set(template_params.get("outputs", {}).keys())

        differences["missing_in_template"].extend(
            [f"output:{name}" for name in extracted_outputs - template_outputs]
        )
        differences["missing_in_code"].extend(
            [f"output:{name}" for name in template_outputs - extracted_outputs]
        )

        # Check type mismatches for matching parameters
        for name in extracted_inputs & template_inputs:
            ext_type = extracted_params["inputs"][name].get("type", "string")
            tmpl_type = template_params["inputs"][name].get("type", "string")
            if ext_type != tmpl_type:
                differences["type_mismatches"].append({
                    "parameter": f"input:{name}",
                    "code_type": ext_type,
                    "template_type": tmpl_type
                })
            else:
                differences["matches"].append(f"input:{name}")

        for name in extracted_outputs & template_outputs:
            ext_type = extracted_params["outputs"][name].get("type", "string")
            tmpl_type = template_params["outputs"][name].get("type", "string")
            if ext_type != tmpl_type:
                differences["type_mismatches"].append({
                    "parameter": f"output:{name}",
                    "code_type": ext_type,
                    "template_type": tmpl_type
                })
            else:
                differences["matches"].append(f"output:{name}")

        return {
            "success": True,
            "differences": differences,
            "is_synchronized": (
                len(differences["missing_in_template"]) == 0 and
                len(differences["missing_in_code"]) == 0 and
                len(differences["type_mismatches"]) == 0
            )
        }
