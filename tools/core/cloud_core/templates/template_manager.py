"""
Template Manager

Loads, validates, and manages deployment templates from tools/templates/ directory.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
import yaml

from ..utils.logger import get_logger
from ..utils.path_utils import get_templates_dir

logger = get_logger(__name__)


class TemplateNotFoundError(FileNotFoundError):
    """Raised when template not found"""

    pass


class TemplateValidationError(Exception):
    """Raised when template fails validation"""

    pass


class TemplateManager:
    """Manages deployment templates"""

    def __init__(self, templates_root: Optional[Path] = None):
        """
        Initialize template manager

        Args:
            templates_root: Root directory for templates
                           Defaults to tools/templates/ relative to CWD or installation path
        """
        if templates_root:
            self.templates_root = Path(templates_root)
        else:
            # Use path utility to find templates directory from anywhere
            try:
                self.templates_root = get_templates_dir()
            except RuntimeError:
                # Fallback: use __file__ relative path
                cli_root = Path(__file__).parent.parent.parent.parent.parent
                self.templates_root = cli_root / "templates"

        self.default_templates_dir = self.templates_root / "default"
        self.custom_templates_dir = self.templates_root / "custom"

        logger.debug(f"Template manager initialized with root: {self.templates_root}")

    def list_templates(self, include_custom: bool = True) -> List[str]:
        """
        List available templates

        Args:
            include_custom: Whether to include custom templates

        Returns:
            List of template names
        """
        templates = []

        # List default templates
        if self.default_templates_dir.exists():
            for template_file in self.default_templates_dir.glob("*.yaml"):
                templates.append(template_file.stem)

        # List custom templates
        if include_custom and self.custom_templates_dir.exists():
            for template_file in self.custom_templates_dir.glob("*.yaml"):
                name = f"custom:{template_file.stem}"
                templates.append(name)

        return sorted(templates)

    def template_exists(self, template_name: str) -> bool:
        """
        Check if template exists

        Args:
            template_name: Name of template (e.g., "default" or "custom:my-template")

        Returns:
            True if exists, False otherwise
        """
        template_path = self._get_template_path(template_name)
        return template_path is not None and template_path.exists()

    def load_template(self, template_name: str) -> Dict[str, Any]:
        """
        Load a template

        Args:
            template_name: Name of template (e.g., "default" or "custom:my-template")

        Returns:
            Template data as dictionary

        Raises:
            TemplateNotFoundError: If template not found
            TemplateValidationError: If template invalid
        """
        logger.info(f"Loading template: {template_name}")

        template_path = self._get_template_path(template_name)

        if not template_path or not template_path.exists():
            raise TemplateNotFoundError(f"Template '{template_name}' not found")

        try:
            with open(template_path, "r", encoding="utf-8") as f:
                template_data = yaml.safe_load(f)

            if not template_data:
                raise TemplateValidationError(f"Template '{template_name}' is empty")

            # Basic validation
            self._validate_template(template_data, template_name)

            logger.info(f"Template '{template_name}' loaded successfully")
            return template_data

        except yaml.YAMLError as e:
            raise TemplateValidationError(
                f"Template '{template_name}' has invalid YAML: {e}"
            )
        except Exception as e:
            raise TemplateValidationError(
                f"Error loading template '{template_name}': {e}"
            )

    def _get_template_path(self, template_name: str) -> Optional[Path]:
        """
        Get path to template file

        Args:
            template_name: Name of template

        Returns:
            Path to template file, or None if not found
        """
        # Check if custom template
        if template_name.startswith("custom:"):
            name = template_name.replace("custom:", "")
            path = self.custom_templates_dir / f"{name}.yaml"
            return path if path.exists() else None

        # Check default templates
        path = self.default_templates_dir / f"{template_name}.yaml"
        return path if path.exists() else None

    def _validate_template(self, template_data: Dict[str, Any], template_name: str) -> None:
        """
        Validate template structure

        Args:
            template_data: Template data
            template_name: Name of template (for error messages)

        Raises:
            TemplateValidationError: If validation fails
        """
        # Check required top-level fields (minimal validation)
        # Only require deployment and stacks - version and template_name are optional
        if "stacks" not in template_data:
            raise TemplateValidationError(
                f"Template '{template_name}' missing required field: stacks"
            )

        # Validate version (if present)
        version = template_data.get("version")
        if version and not (version.startswith("3.") or version.startswith("4.")):
            raise TemplateValidationError(
                f"Template '{template_name}' has unsupported version: {version}"
            )

        # Validate stacks section
        stacks = template_data.get("stacks", {})
        if not isinstance(stacks, dict):
            raise TemplateValidationError(
                f"Template '{template_name}' has invalid stacks section (must be dict)"
            )

        # Validate each stack configuration
        for stack_name, stack_config in stacks.items():
            if not isinstance(stack_config, dict):
                raise TemplateValidationError(
                    f"Template '{template_name}' has invalid config for stack '{stack_name}'"
                )

            # Check required stack fields
            if "enabled" not in stack_config:
                raise TemplateValidationError(
                    f"Template '{template_name}' stack '{stack_name}' missing 'enabled' field"
                )

            if "dependencies" not in stack_config:
                raise TemplateValidationError(
                    f"Template '{template_name}' stack '{stack_name}' missing 'dependencies' field"
                )

    def get_template_info(self, template_name: str) -> Dict[str, Any]:
        """
        Get template metadata

        Args:
            template_name: Name of template

        Returns:
            Dictionary with template metadata

        Raises:
            TemplateNotFoundError: If template not found
        """
        template_data = self.load_template(template_name)

        return {
            "name": template_name,
            "version": template_data.get("version"),
            "description": template_data.get("description", ""),
            "template_name": template_data.get("template_name"),
            "stack_count": len(template_data.get("stacks", {})),
            "stacks": list(template_data.get("stacks", {}).keys()),
            "metadata": template_data.get("metadata", {}),
        }

    def create_custom_template(
        self,
        template_name: str,
        template_data: Dict[str, Any],
        overwrite: bool = False,
    ) -> Path:
        """
        Create a custom template

        Args:
            template_name: Name for the template (without 'custom:' prefix)
            template_data: Template data
            overwrite: Whether to overwrite if exists

        Returns:
            Path to created template file

        Raises:
            FileExistsError: If template exists and overwrite=False
            TemplateValidationError: If template data invalid
        """
        # Validate template data
        self._validate_template(template_data, template_name)

        # Ensure custom templates directory exists
        self.custom_templates_dir.mkdir(parents=True, exist_ok=True)

        template_path = self.custom_templates_dir / f"{template_name}.yaml"

        if template_path.exists() and not overwrite:
            raise FileExistsError(
                f"Custom template '{template_name}' already exists. Use overwrite=True to replace."
            )

        # Write template
        with open(template_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(template_data, f, default_flow_style=False, sort_keys=False)

        logger.info(f"Created custom template: {template_name}")
        return template_path

    def delete_custom_template(self, template_name: str) -> bool:
        """
        Delete a custom template

        Args:
            template_name: Name of template (with or without 'custom:' prefix)

        Returns:
            True if deleted, False if not found
        """
        # Remove 'custom:' prefix if present
        if template_name.startswith("custom:"):
            template_name = template_name.replace("custom:", "")

        template_path = self.custom_templates_dir / f"{template_name}.yaml"

        if template_path.exists():
            template_path.unlink()
            logger.info(f"Deleted custom template: {template_name}")
            return True

        return False

    def get_template_path(self, template_name: str) -> Optional[Path]:
        """
        Get full path to template file

        Args:
            template_name: Name of template

        Returns:
            Path to template file, or None if not found
        """
        return self._get_template_path(template_name)
