"""TypeScript parser for extracting parameters from Pulumi stack code"""

import re
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
import esprima


@dataclass
class InputParameter:
    """Represents an input parameter extracted from stack code"""
    name: str
    type: str = "string"  # string, number, boolean, object, array
    required: bool = True
    secret: bool = False
    default: Optional[Any] = None
    description: Optional[str] = None
    line_number: Optional[int] = None


@dataclass
class OutputParameter:
    """Represents an output parameter extracted from stack code"""
    name: str
    type: str = "string"
    description: Optional[str] = None
    line_number: Optional[int] = None


@dataclass
class ParseResult:
    """Result of parsing a TypeScript stack file"""
    inputs: List[InputParameter] = field(default_factory=list)
    outputs: List[OutputParameter] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class TypeScriptParser:
    """Parse TypeScript stack code to extract parameters"""

    # Patterns for different config access methods
    # Updated to match with or without default values (e.g., config.get("param", "default"))
    CONFIG_PATTERNS = {
        'require': r"config\.require\(['\"](\w+)['\"](?:\s*,\s*[^)]+)?\)",
        'get': r"config\.get\(['\"](\w+)['\"](?:\s*,\s*[^)]+)?\)",
        'requireSecret': r"config\.requireSecret\(['\"](\w+)['\"](?:\s*,\s*[^)]+)?\)",
        'getSecret': r"config\.getSecret\(['\"](\w+)['\"](?:\s*,\s*[^)]+)?\)",
        'requireBoolean': r"config\.requireBoolean\(['\"](\w+)['\"](?:\s*,\s*[^)]+)?\)",
        'getBoolean': r"config\.getBoolean\(['\"](\w+)['\"](?:\s*,\s*[^)]+)?\)",
        'requireNumber': r"config\.requireNumber\(['\"](\w+)['\"](?:\s*,\s*[^)]+)?\)",
        'getNumber': r"config\.getNumber\(['\"](\w+)['\"](?:\s*,\s*[^)]+)?\)",
        'requireObject': r"config\.requireObject\(['\"](\w+)['\"](?:\s*,\s*[^)]+)?\)",
        'getObject': r"config\.getObject\(['\"](\w+)['\"](?:\s*,\s*[^)]+)?\)",
    }

    # Pattern for export statements
    EXPORT_PATTERN = r"export\s+(?:const|let|var)\s+(\w+)\s*[=:]"

    def __init__(self):
        """Initialize the parser"""
        self.result = ParseResult()

    def parse_file(self, file_path: Path) -> ParseResult:
        """
        Parse a TypeScript stack file and extract parameters

        Args:
            file_path: Path to the TypeScript file

        Returns:
            ParseResult with extracted inputs and outputs
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()

            return self.parse_source(source_code)

        except Exception as e:
            self.result.errors.append(f"Failed to parse file: {str(e)}")
            return self.result

    def parse_source(self, source_code: str) -> ParseResult:
        """
        Parse TypeScript source code and extract parameters

        Args:
            source_code: TypeScript source code as string

        Returns:
            ParseResult with extracted inputs and outputs
        """
        self.result = ParseResult()

        try:
            # Extract inputs using regex patterns
            self._extract_inputs(source_code)

            # Extract outputs using regex patterns
            self._extract_outputs(source_code)

            # Try to use esprima for more detailed analysis if possible
            try:
                self._enhance_with_ast_analysis(source_code)
            except Exception as e:
                # AST parsing is optional enhancement, don't fail if it doesn't work
                self.result.warnings.append(f"AST analysis failed: {str(e)}")

        except Exception as e:
            self.result.errors.append(f"Parsing failed: {str(e)}")

        return self.result

    def _extract_inputs(self, source_code: str) -> None:
        """Extract input parameters from config access calls"""
        lines = source_code.split('\n')

        for line_num, line in enumerate(lines, start=1):
            # Check each config pattern
            for method_name, pattern in self.CONFIG_PATTERNS.items():
                matches = re.finditer(pattern, line)
                for match in matches:
                    param_name = match.group(1)

                    # Determine parameter properties based on method
                    input_param = self._create_input_from_method(
                        param_name, method_name, line, line_num
                    )

                    # Check if already exists
                    if not any(inp.name == param_name for inp in self.result.inputs):
                        self.result.inputs.append(input_param)

    def _create_input_from_method(
        self,
        name: str,
        method: str,
        line: str,
        line_num: int
    ) -> InputParameter:
        """Create InputParameter based on config method type"""

        # Determine if required or optional
        required = 'require' in method.lower()

        # Determine if secret
        secret = 'secret' in method.lower()

        # Determine type from method name
        param_type = "string"  # default
        if 'Boolean' in method:
            param_type = "boolean"
        elif 'Number' in method:
            param_type = "number"
        elif 'Object' in method:
            param_type = "object"

        # Try to extract default value for get() methods
        default = None
        if not required:
            # Look for default value in get() call
            default_match = re.search(
                rf"config\.{method}\(['\"](\w+)['\"]\s*,\s*(.+?)\)",
                line
            )
            if default_match:
                default_str = default_match.group(2).strip()
                # Try to parse simple defaults
                if default_str.startswith('"') or default_str.startswith("'"):
                    default = default_str.strip('"\'')
                elif default_str.isdigit():
                    default = int(default_str)
                elif default_str in ['true', 'false']:
                    default = default_str == 'true'

        # Try to extract description from comments
        description = self._extract_description_from_line(line)

        return InputParameter(
            name=name,
            type=param_type,
            required=required,
            secret=secret,
            default=default,
            description=description,
            line_number=line_num
        )

    def _extract_outputs(self, source_code: str) -> None:
        """Extract output parameters from export statements"""
        lines = source_code.split('\n')

        for line_num, line in enumerate(lines, start=1):
            matches = re.finditer(self.EXPORT_PATTERN, line)
            for match in matches:
                output_name = match.group(1)

                # Try to infer type from the assignment
                output_type = self._infer_output_type(line)

                # Extract description from comments
                description = self._extract_description_from_line(line)

                output_param = OutputParameter(
                    name=output_name,
                    type=output_type,
                    description=description,
                    line_number=line_num
                )

                # Check if already exists
                if not any(out.name == output_name for out in self.result.outputs):
                    self.result.outputs.append(output_param)

    def _infer_output_type(self, line: str) -> str:
        """Infer output type from assignment line"""
        # Simple heuristics for type inference
        if '.id' in line or 'Id' in line:
            return "string"
        elif '.arn' in line or 'Arn' in line:
            return "string"
        elif '.apply(' in line:
            return "string"  # Pulumi Output type, default to string
        elif 'Output.create' in line:
            return "string"
        else:
            return "string"  # default

    def _extract_description_from_line(self, line: str) -> Optional[str]:
        """Extract description from inline or nearby comments"""
        # Look for inline comments
        comment_match = re.search(r'//\s*(.+)$', line)
        if comment_match:
            return comment_match.group(1).strip()
        return None

    def _enhance_with_ast_analysis(self, source_code: str) -> None:
        """
        Use esprima to perform AST-based analysis for better accuracy

        This enhances the regex-based extraction with type information
        and better handling of complex expressions.
        """
        try:
            # Esprima can parse JavaScript, which is close enough for basic analysis
            # Note: This won't work for TypeScript-specific syntax, but helps with basic JS
            ast = esprima.parseScript(source_code, {'tolerant': True, 'loc': True})

            # Walk the AST to find config calls and exports
            self._walk_ast(ast)

        except Exception as e:
            # If parsing fails, the regex extraction is still valid
            raise Exception(f"AST parsing not available: {str(e)}")

    def _walk_ast(self, node: Any) -> None:
        """Walk the AST to find relevant nodes"""
        # This is a simplified implementation
        # In production, you'd want more sophisticated AST walking
        if not hasattr(node, 'type'):
            return

        # Handle different node types
        if node.type == 'CallExpression':
            self._process_call_expression(node)
        elif node.type == 'ExportNamedDeclaration':
            self._process_export_declaration(node)

        # Recursively walk child nodes
        for key in dir(node):
            if key.startswith('_'):
                continue
            child = getattr(node, key)
            if isinstance(child, list):
                for item in child:
                    self._walk_ast(item)
            elif hasattr(child, 'type'):
                self._walk_ast(child)

    def _process_call_expression(self, node: Any) -> None:
        """Process CallExpression nodes for config calls"""
        # Check if this is a config.require/get call
        # This is a simplified check
        pass  # Already handled by regex, this is for enhancement

    def _process_export_declaration(self, node: Any) -> None:
        """Process export declarations"""
        # Already handled by regex, this is for enhancement
        pass

    def extract_inputs(self, source_code: str) -> List[InputParameter]:
        """
        Convenience method to extract only inputs

        Args:
            source_code: TypeScript source code

        Returns:
            List of InputParameter objects
        """
        result = self.parse_source(source_code)
        return result.inputs

    def extract_outputs(self, source_code: str) -> List[OutputParameter]:
        """
        Convenience method to extract only outputs

        Args:
            source_code: TypeScript source code

        Returns:
            List of OutputParameter objects
        """
        result = self.parse_source(source_code)
        return result.outputs

    def validate_extraction(self) -> bool:
        """
        Validate that extraction was successful

        Returns:
            True if no errors occurred
        """
        return len(self.result.errors) == 0

    def get_errors(self) -> List[str]:
        """Get list of errors from parsing"""
        return self.result.errors

    def get_warnings(self) -> List[str]:
        """Get list of warnings from parsing"""
        return self.result.warnings
