"""
Stack Code Validator

Validates that stack TypeScript code matches template parameter declarations.
Ensures template-first enforcement.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field

from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ValidationIssue:
    """Represents a validation issue"""
    severity: str  # "error" or "warning"
    message: str
    location: Optional[str] = None  # e.g., "line 42" or "input:vpcId"


@dataclass
class ValidationResult:
    """Result of stack code validation"""
    valid: bool
    errors: List[ValidationIssue] = field(default_factory=list)
    warnings: List[ValidationIssue] = field(default_factory=list)
    stack_name: Optional[str] = None

    def add_error(self, message: str, location: Optional[str] = None):
        """Add an error"""
        self.errors.append(ValidationIssue("error", message, location))
        self.valid = False

    def add_warning(self, message: str, location: Optional[str] = None):
        """Add a warning"""
        self.warnings.append(ValidationIssue("warning", message, location))

    def has_issues(self) -> bool:
        """Check if there are any issues"""
        return len(self.errors) > 0 or len(self.warnings) > 0

    def get_error_count(self) -> int:
        """Get number of errors"""
        return len(self.errors)

    def get_warning_count(self) -> int:
        """Get number of warnings"""
        return len(self.warnings)


class StackCodeValidator:
    """Validates stack code against template declarations"""

    def __init__(self):
        """Initialize the validator"""
        pass

    def validate(
        self,
        stack_dir: Path,
        template_data: Dict,
        stack_name: Optional[str] = None,
        strict: bool = False
    ) -> ValidationResult:
        """
        Validate stack code against template

        Args:
            stack_dir: Path to stack directory
            template_data: Template data with parameter declarations
            stack_name: Optional stack name
            strict: If True, enforce stricter validation

        Returns:
            ValidationResult with errors and warnings
        """
        result = ValidationResult(valid=True, stack_name=stack_name or stack_dir.name)

        try:
            # Import here to avoid circular dependency
            from cloud_cli.parser.parameter_extractor import ParameterExtractor

            # Extract parameters from code
            extractor = ParameterExtractor()
            extraction = extractor.extract_from_stack(stack_dir, stack_name)

            if not extraction["success"]:
                result.add_error(
                    f"Failed to extract parameters from code: {extraction.get('error', 'Unknown error')}"
                )
                return result

            extracted_params = extraction["parameters"]

            # Get template parameters
            template_params = template_data.get("parameters", {})

            # Validate inputs
            self._validate_inputs(
                extracted_params.get("inputs", {}),
                template_params.get("inputs", {}),
                result,
                strict
            )

            # Validate outputs
            self._validate_outputs(
                extracted_params.get("outputs", {}),
                template_params.get("outputs", {}),
                result,
                strict
            )

        except Exception as e:
            result.add_error(f"Validation failed: {str(e)}")

        return result

    def _validate_inputs(
        self,
        code_inputs: Dict,
        template_inputs: Dict,
        result: ValidationResult,
        strict: bool
    ) -> None:
        """
        Validate input parameters

        Args:
            code_inputs: Inputs extracted from code
            template_inputs: Inputs from template
            result: ValidationResult to add issues to
            strict: Strict mode
        """
        code_input_names = set(code_inputs.keys())
        template_input_names = set(template_inputs.keys())

        # Check for undeclared inputs (used in code but not in template)
        undeclared = code_input_names - template_input_names
        for input_name in undeclared:
            result.add_error(
                f"Input '{input_name}' is used in code but not declared in template",
                location=f"input:{input_name}"
            )

        # Check for unused inputs (in template but not in code)
        unused = template_input_names - code_input_names
        for input_name in unused:
            if strict:
                result.add_error(
                    f"Input '{input_name}' is declared in template but not used in code",
                    location=f"input:{input_name}"
                )
            else:
                result.add_warning(
                    f"Input '{input_name}' is declared in template but not used in code",
                    location=f"input:{input_name}"
                )

        # Validate matching inputs for type consistency
        matching = code_input_names & template_input_names
        for input_name in matching:
            code_config = code_inputs[input_name]
            template_config = template_inputs[input_name]

            # Check type match
            code_type = code_config.get("type", "string")
            template_type = template_config.get("type", "string")

            if code_type != template_type:
                result.add_warning(
                    f"Input '{input_name}' type mismatch: code uses '{code_type}', template declares '{template_type}'",
                    location=f"input:{input_name}"
                )

            # Check required/optional consistency
            code_required = code_config.get("required", True)
            template_required = template_config.get("required", False)

            if code_required and not template_required:
                result.add_warning(
                    f"Input '{input_name}' is required in code but marked optional in template",
                    location=f"input:{input_name}"
                )

            # Check secret flag
            code_secret = code_config.get("secret", False)
            template_secret = template_config.get("secret", False)

            if code_secret != template_secret:
                result.add_warning(
                    f"Input '{input_name}' secret flag mismatch: code={code_secret}, template={template_secret}",
                    location=f"input:{input_name}"
                )

    def _validate_outputs(
        self,
        code_outputs: Dict,
        template_outputs: Dict,
        result: ValidationResult,
        strict: bool
    ) -> None:
        """
        Validate output parameters

        Args:
            code_outputs: Outputs extracted from code
            template_outputs: Outputs from template
            result: ValidationResult to add issues to
            strict: Strict mode
        """
        code_output_names = set(code_outputs.keys())
        template_output_names = set(template_outputs.keys())

        # Check for undeclared outputs (exported in code but not in template)
        undeclared = code_output_names - template_output_names
        for output_name in undeclared:
            if strict:
                result.add_error(
                    f"Output '{output_name}' is exported in code but not declared in template",
                    location=f"output:{output_name}"
                )
            else:
                result.add_warning(
                    f"Output '{output_name}' is exported in code but not declared in template",
                    location=f"output:{output_name}"
                )

        # Check for missing outputs (in template but not exported in code)
        missing = template_output_names - code_output_names
        for output_name in missing:
            result.add_error(
                f"Output '{output_name}' is declared in template but not exported in code",
                location=f"output:{output_name}"
            )

        # Validate matching outputs for type consistency
        matching = code_output_names & template_output_names
        for output_name in matching:
            code_config = code_outputs[output_name]
            template_config = template_outputs[output_name]

            # Check type match
            code_type = code_config.get("type", "string")
            template_type = template_config.get("type", "string")

            if code_type != template_type:
                result.add_warning(
                    f"Output '{output_name}' type mismatch: code infers '{code_type}', template declares '{template_type}'",
                    location=f"output:{output_name}"
                )

    def validate_multiple_stacks(
        self,
        stacks_base_dir: Path,
        templates: Dict[str, Dict],
        strict: bool = False
    ) -> Dict[str, ValidationResult]:
        """
        Validate multiple stacks

        Args:
            stacks_base_dir: Base directory containing stack directories
            templates: Dictionary mapping stack names to template data
            strict: Strict mode

        Returns:
            Dictionary mapping stack names to validation results
        """
        results = {}

        for stack_name, template_data in templates.items():
            stack_dir = stacks_base_dir / stack_name

            if not stack_dir.exists():
                result = ValidationResult(valid=False, stack_name=stack_name)
                result.add_error(f"Stack directory not found: {stack_dir}")
                results[stack_name] = result
                continue

            result = self.validate(stack_dir, template_data, stack_name, strict)
            results[stack_name] = result

        return results

    def validate_deployment(
        self,
        stacks_base_dir: Path,
        manifest: Dict,
        strict: bool = False
    ) -> Tuple[bool, Dict[str, ValidationResult]]:
        """
        Validate all stacks in a deployment manifest

        Args:
            stacks_base_dir: Base directory containing stack directories
            manifest: Deployment manifest with stack configurations
            strict: Strict mode

        Returns:
            Tuple of (all_valid, results_dict)
        """
        # Import here to avoid circular dependency
        from ..templates.stack_template_manager import StackTemplateManager

        template_manager = StackTemplateManager()
        results = {}
        all_valid = True

        stacks_config = manifest.get("stacks", {})

        for stack_name, stack_config in stacks_config.items():
            # Skip if not enabled
            if not stack_config.get("enabled", False):
                continue

            # Check if template exists
            if not template_manager.template_exists(stack_name):
                result = ValidationResult(valid=False, stack_name=stack_name)
                result.add_error(
                    f"Stack template not found. Register stack first with: cloud register-stack {stack_name}"
                )
                results[stack_name] = result
                all_valid = False
                continue

            # Load template
            try:
                template_data = template_manager.load_template(stack_name)
            except Exception as e:
                result = ValidationResult(valid=False, stack_name=stack_name)
                result.add_error(f"Failed to load stack template: {str(e)}")
                results[stack_name] = result
                all_valid = False
                continue

            # Validate
            stack_dir = stacks_base_dir / stack_name
            result = self.validate(stack_dir, template_data, stack_name, strict)
            results[stack_name] = result

            if not result.valid:
                all_valid = False

        return all_valid, results

    def format_validation_result(self, result: ValidationResult) -> str:
        """
        Format validation result as human-readable string

        Args:
            result: ValidationResult to format

        Returns:
            Formatted string
        """
        lines = []

        if result.stack_name:
            lines.append(f"Stack: {result.stack_name}")

        if result.valid and not result.has_issues():
            lines.append("✓ Validation passed")
            return "\n".join(lines)

        # Add errors
        if result.errors:
            lines.append(f"\n✗ {len(result.errors)} Error(s):")
            for issue in result.errors:
                location = f" [{issue.location}]" if issue.location else ""
                lines.append(f"  - {issue.message}{location}")

        # Add warnings
        if result.warnings:
            lines.append(f"\n⚠ {len(result.warnings)} Warning(s):")
            for issue in result.warnings:
                location = f" [{issue.location}]" if issue.location else ""
                lines.append(f"  - {issue.message}{location}")

        return "\n".join(lines)

    def format_multiple_results(
        self,
        results: Dict[str, ValidationResult]
    ) -> str:
        """
        Format multiple validation results

        Args:
            results: Dictionary of validation results

        Returns:
            Formatted string
        """
        lines = []
        lines.append("=" * 60)
        lines.append("Stack Code Validation Results")
        lines.append("=" * 60)

        total_errors = sum(r.get_error_count() for r in results.values())
        total_warnings = sum(r.get_warning_count() for r in results.values())
        valid_count = sum(1 for r in results.values() if r.valid)

        lines.append(f"\nStacks validated: {len(results)}")
        lines.append(f"Valid: {valid_count}/{len(results)}")
        lines.append(f"Total errors: {total_errors}")
        lines.append(f"Total warnings: {total_warnings}")

        for stack_name, result in results.items():
            lines.append(f"\n{'-' * 60}")
            lines.append(self.format_validation_result(result))

        lines.append(f"\n{'=' * 60}")

        return "\n".join(lines)
