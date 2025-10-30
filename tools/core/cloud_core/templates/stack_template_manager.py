"""
Stack Template Manager

Manages stack-specific templates with enhanced parameter format.
Stack templates are stored in tools/templates/config/{stack-name}.yaml
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
import yaml

from ..utils.logger import get_logger

logger = get_logger(__name__)


class StackTemplateNotFoundError(FileNotFoundError):
    """Raised when stack template not found"""
    pass


class StackTemplateValidationError(Exception):
    """Raised when stack template fails validation"""
    pass


class StackTemplateManager:
    """Manages stack-specific templates with enhanced format"""

    def __init__(self, config_root: Optional[Path] = None):
        """
        Initialize stack template manager

        Args:
            config_root: Root directory for stack config templates
                        Defaults to tools/templates/config/
        """
        if config_root:
            self.config_root = Path(config_root)
        else:
            # Try CWD first
            cwd_config = Path.cwd() / "tools" / "templates" / "config"
            if cwd_config.exists():
                self.config_root = cwd_config
            else:
                # Default: cloud/tools/templates/config/
                # Path: cloud/tools/core/cloud_core/templates/stack_template_manager.py
                # Go up 3 levels: cloud_core/templates → cloud_core → core → tools
                tools_root = Path(__file__).parent.parent.parent.parent
                self.config_root = tools_root / "templates" / "config"

        # Ensure config directory exists
        self.config_root.mkdir(parents=True, exist_ok=True)

        logger.debug(f"Stack template manager initialized with root: {self.config_root}")

    def list_templates(self) -> List[str]:
        """
        List all registered stack templates

        Returns:
            List of stack names
        """
        templates = []

        if self.config_root.exists():
            for template_file in self.config_root.glob("*.yaml"):
                templates.append(template_file.stem)

        return sorted(templates)

    def template_exists(self, stack_name: str) -> bool:
        """
        Check if stack template exists

        Args:
            stack_name: Name of stack

        Returns:
            True if exists
        """
        template_path = self.config_root / f"{stack_name}.yaml"
        return template_path.exists()

    def load_template(self, stack_name: str) -> Dict[str, Any]:
        """
        Load a stack template

        Args:
            stack_name: Name of stack

        Returns:
            Template data as dictionary

        Raises:
            StackTemplateNotFoundError: If template not found
            StackTemplateValidationError: If template invalid
        """
        logger.info(f"Loading stack template: {stack_name}")

        template_path = self.config_root / f"{stack_name}.yaml"

        if not template_path.exists():
            raise StackTemplateNotFoundError(
                f"Stack template '{stack_name}' not found at {template_path}"
            )

        try:
            with open(template_path, "r", encoding="utf-8") as f:
                template_data = yaml.safe_load(f)

            if not template_data:
                raise StackTemplateValidationError(
                    f"Stack template '{stack_name}' is empty"
                )

            # Validate template structure
            self.validate_template(template_data, stack_name)

            logger.info(f"Stack template '{stack_name}' loaded successfully")
            return template_data

        except yaml.YAMLError as e:
            raise StackTemplateValidationError(
                f"Stack template '{stack_name}' has invalid YAML: {e}"
            )
        except Exception as e:
            if isinstance(e, (StackTemplateNotFoundError, StackTemplateValidationError)):
                raise
            raise StackTemplateValidationError(
                f"Error loading stack template '{stack_name}': {e}"
            )

    def validate_template(
        self,
        template_data: Dict[str, Any],
        stack_name: str,
        strict: bool = False
    ) -> None:
        """
        Validate stack template structure

        Args:
            template_data: Template data
            stack_name: Stack name (for error messages)
            strict: If True, enforce stricter validation

        Raises:
            StackTemplateValidationError: If validation fails
        """
        # Check required fields
        if "name" not in template_data:
            raise StackTemplateValidationError(
                f"Stack template '{stack_name}' missing required field: name"
            )

        # Validate parameters section if present
        if "parameters" in template_data:
            self._validate_parameters_section(
                template_data["parameters"],
                stack_name,
                strict
            )

        # Validate other optional fields
        if "dependencies" in template_data:
            deps = template_data["dependencies"]
            if not isinstance(deps, list):
                raise StackTemplateValidationError(
                    f"Stack template '{stack_name}' dependencies must be a list"
                )

        if "priority" in template_data:
            priority = template_data["priority"]
            if not isinstance(priority, int) or priority < 0:
                raise StackTemplateValidationError(
                    f"Stack template '{stack_name}' priority must be a positive integer"
                )

    def _validate_parameters_section(
        self,
        parameters: Dict[str, Any],
        stack_name: str,
        strict: bool
    ) -> None:
        """
        Validate parameters section (inputs and outputs)

        Args:
            parameters: Parameters section from template
            stack_name: Stack name for error messages
            strict: Whether to enforce strict validation
        """
        if not isinstance(parameters, dict):
            raise StackTemplateValidationError(
                f"Stack template '{stack_name}' parameters must be a dict"
            )

        # Validate inputs section
        if "inputs" in parameters:
            inputs = parameters["inputs"]
            if not isinstance(inputs, dict):
                raise StackTemplateValidationError(
                    f"Stack template '{stack_name}' parameters.inputs must be a dict"
                )

            for input_name, input_config in inputs.items():
                self._validate_input_parameter(
                    input_name,
                    input_config,
                    stack_name,
                    strict
                )

        # Validate outputs section
        if "outputs" in parameters:
            outputs = parameters["outputs"]
            if not isinstance(outputs, dict):
                raise StackTemplateValidationError(
                    f"Stack template '{stack_name}' parameters.outputs must be a dict"
                )

            for output_name, output_config in outputs.items():
                self._validate_output_parameter(
                    output_name,
                    output_config,
                    stack_name,
                    strict
                )

    def _validate_input_parameter(
        self,
        name: str,
        config: Dict[str, Any],
        stack_name: str,
        strict: bool
    ) -> None:
        """Validate an input parameter definition"""
        if not isinstance(config, dict):
            raise StackTemplateValidationError(
                f"Stack template '{stack_name}' input '{name}' must be a dict"
            )

        # Validate type
        if "type" in config:
            valid_types = ["string", "number", "boolean", "object", "array"]
            if config["type"] not in valid_types:
                raise StackTemplateValidationError(
                    f"Stack template '{stack_name}' input '{name}' has invalid type: {config['type']}"
                )

        # Validate required field
        if "required" in config:
            if not isinstance(config["required"], bool):
                raise StackTemplateValidationError(
                    f"Stack template '{stack_name}' input '{name}' required field must be boolean"
                )

        # Validate secret field
        if "secret" in config:
            if not isinstance(config["secret"], bool):
                raise StackTemplateValidationError(
                    f"Stack template '{stack_name}' input '{name}' secret field must be boolean"
                )

        # In strict mode, require type and required fields
        if strict:
            if "type" not in config:
                raise StackTemplateValidationError(
                    f"Stack template '{stack_name}' input '{name}' missing required field: type (strict mode)"
                )
            if "required" not in config:
                raise StackTemplateValidationError(
                    f"Stack template '{stack_name}' input '{name}' missing required field: required (strict mode)"
                )

    def _validate_output_parameter(
        self,
        name: str,
        config: Dict[str, Any],
        stack_name: str,
        strict: bool
    ) -> None:
        """Validate an output parameter definition"""
        if not isinstance(config, dict):
            raise StackTemplateValidationError(
                f"Stack template '{stack_name}' output '{name}' must be a dict"
            )

        # Validate type
        if "type" in config:
            valid_types = ["string", "number", "boolean", "object", "array"]
            if config["type"] not in valid_types:
                raise StackTemplateValidationError(
                    f"Stack template '{stack_name}' output '{name}' has invalid type: {config['type']}"
                )

        # In strict mode, require type field
        if strict and "type" not in config:
            raise StackTemplateValidationError(
                f"Stack template '{stack_name}' output '{name}' missing required field: type (strict mode)"
            )

    def save_template(
        self,
        stack_name: str,
        template_data: Dict[str, Any],
        overwrite: bool = False
    ) -> Path:
        """
        Save a stack template

        Args:
            stack_name: Name of stack
            template_data: Template data
            overwrite: Whether to overwrite if exists

        Returns:
            Path to saved template

        Raises:
            FileExistsError: If exists and overwrite=False
            StackTemplateValidationError: If template invalid
        """
        # Validate before saving
        self.validate_template(template_data, stack_name)

        template_path = self.config_root / f"{stack_name}.yaml"

        if template_path.exists() and not overwrite:
            raise FileExistsError(
                f"Stack template '{stack_name}' already exists. Use overwrite=True to replace."
            )

        # Ensure directory exists
        self.config_root.mkdir(parents=True, exist_ok=True)

        # Write template
        with open(template_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(
                template_data,
                f,
                default_flow_style=False,
                sort_keys=False
            )

        logger.info(f"Saved stack template: {stack_name}")
        return template_path

    def delete_template(self, stack_name: str) -> bool:
        """
        Delete a stack template

        Args:
            stack_name: Name of stack

        Returns:
            True if deleted, False if not found
        """
        template_path = self.config_root / f"{stack_name}.yaml"

        if template_path.exists():
            template_path.unlink()
            logger.info(f"Deleted stack template: {stack_name}")
            return True

        return False

    def get_template_path(self, stack_name: str) -> Path:
        """
        Get path to stack template file

        Args:
            stack_name: Name of stack

        Returns:
            Path to template file
        """
        return self.config_root / f"{stack_name}.yaml"

    def get_inputs(self, stack_name: str) -> Dict[str, Any]:
        """
        Get input parameters for a stack

        Args:
            stack_name: Name of stack

        Returns:
            Dictionary of input parameters

        Raises:
            StackTemplateNotFoundError: If template not found
        """
        template = self.load_template(stack_name)
        return template.get("parameters", {}).get("inputs", {})

    def get_outputs(self, stack_name: str) -> Dict[str, Any]:
        """
        Get output parameters for a stack

        Args:
            stack_name: Name of stack

        Returns:
            Dictionary of output parameters

        Raises:
            StackTemplateNotFoundError: If template not found
        """
        template = self.load_template(stack_name)
        return template.get("parameters", {}).get("outputs", {})

    def get_required_inputs(self, stack_name: str) -> List[str]:
        """
        Get list of required input parameter names

        Args:
            stack_name: Name of stack

        Returns:
            List of required input names
        """
        inputs = self.get_inputs(stack_name)
        return [
            name for name, config in inputs.items()
            if config.get("required", False)
        ]

    def get_optional_inputs(self, stack_name: str) -> List[str]:
        """
        Get list of optional input parameter names

        Args:
            stack_name: Name of stack

        Returns:
            List of optional input names
        """
        inputs = self.get_inputs(stack_name)
        return [
            name for name, config in inputs.items()
            if not config.get("required", False)
        ]

    def merge_with_defaults(
        self,
        stack_name: str,
        config_values: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge provided config values with template defaults

        Args:
            stack_name: Name of stack
            config_values: User-provided config values

        Returns:
            Merged configuration

        Raises:
            StackTemplateNotFoundError: If template not found
        """
        template = self.load_template(stack_name)
        inputs = template.get("parameters", {}).get("inputs", {})

        merged = dict(config_values)

        # Apply defaults for missing values
        for name, config in inputs.items():
            if name not in merged and "default" in config:
                merged[name] = config["default"]

        return merged
