"""
Template Renderer

Renders templates with placeholder substitution using {{variable}} syntax.
"""

import re
from typing import Dict, Any, Optional
from ..utils.logger import get_logger

logger = get_logger(__name__)


class TemplateRenderer:
    """Renders templates with placeholder substitution"""

    # Pattern for placeholders: {{variable}} or {{namespace.variable}}
    PLACEHOLDER_PATTERN = re.compile(r"\{\{([a-zA-Z0-9_\.]+)\}\}")

    def __init__(self, variables: Optional[Dict[str, Any]] = None):
        """
        Initialize template renderer

        Args:
            variables: Dictionary of variables for substitution
        """
        self.variables = variables or {}

    def add_variable(self, name: str, value: Any) -> None:
        """
        Add a variable

        Args:
            name: Variable name (can include dots for nested access)
            value: Variable value
        """
        self.variables[name] = value

    def add_variables(self, variables: Dict[str, Any]) -> None:
        """
        Add multiple variables

        Args:
            variables: Dictionary of variables
        """
        self.variables.update(variables)

    def render(self, template_str: str, strict: bool = False) -> str:
        """
        Render template string with variable substitution

        Args:
            template_str: Template string with {{placeholders}}
            strict: If True, raise error for missing variables.
                   If False, leave placeholder as-is for missing variables.

        Returns:
            Rendered string

        Raises:
            ValueError: If strict=True and variable not found
        """

        def replace_placeholder(match):
            var_name = match.group(1)
            value = self._get_variable_value(var_name)

            if value is None:
                if strict:
                    raise ValueError(f"Variable '{var_name}' not found in template context")
                # Keep placeholder as-is
                return match.group(0)

            return str(value)

        return self.PLACEHOLDER_PATTERN.sub(replace_placeholder, template_str)

    def render_dict(
        self, template_dict: Dict[str, Any], strict: bool = False
    ) -> Dict[str, Any]:
        """
        Render all string values in a dictionary

        Args:
            template_dict: Dictionary with potential {{placeholders}} in string values
            strict: Whether to raise error for missing variables

        Returns:
            Dictionary with rendered values
        """
        result = {}

        for key, value in template_dict.items():
            if isinstance(value, str):
                result[key] = self.render(value, strict)
            elif isinstance(value, dict):
                result[key] = self.render_dict(value, strict)
            elif isinstance(value, list):
                result[key] = self.render_list(value, strict)
            else:
                result[key] = value

        return result

    def render_list(self, template_list: list, strict: bool = False) -> list:
        """
        Render all string values in a list

        Args:
            template_list: List with potential {{placeholders}} in string values
            strict: Whether to raise error for missing variables

        Returns:
            List with rendered values
        """
        result = []

        for item in template_list:
            if isinstance(item, str):
                result.append(self.render(item, strict))
            elif isinstance(item, dict):
                result.append(self.render_dict(item, strict))
            elif isinstance(item, list):
                result.append(self.render_list(item, strict))
            else:
                result.append(item)

        return result

    def _get_variable_value(self, var_name: str) -> Optional[Any]:
        """
        Get variable value with support for nested access

        Args:
            var_name: Variable name (e.g., "deployment.id" or "region")

        Returns:
            Variable value, or None if not found
        """
        # Check direct match first
        if var_name in self.variables:
            return self.variables[var_name]

        # Check nested access (e.g., "deployment.id")
        if "." in var_name:
            parts = var_name.split(".")
            current = self.variables

            for part in parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    return None

            return current

        return None

    def has_placeholders(self, text: str) -> bool:
        """
        Check if text contains placeholders

        Args:
            text: Text to check

        Returns:
            True if placeholders found
        """
        return bool(self.PLACEHOLDER_PATTERN.search(text))

    def get_placeholders(self, text: str) -> list[str]:
        """
        Extract all placeholder names from text

        Args:
            text: Text to extract from

        Returns:
            List of placeholder names
        """
        return self.PLACEHOLDER_PATTERN.findall(text)

    def validate_all_variables_defined(
        self, template_str: str
    ) -> tuple[bool, list[str]]:
        """
        Check if all placeholders have defined variables

        Args:
            template_str: Template string to check

        Returns:
            Tuple of (all_defined: bool, missing_vars: list[str])
        """
        placeholders = self.get_placeholders(template_str)
        missing = []

        for placeholder in placeholders:
            if self._get_variable_value(placeholder) is None:
                missing.append(placeholder)

        return len(missing) == 0, missing

    @staticmethod
    def create_from_deployment_context(
        deployment_id: str,
        organization: str,
        project: str,
        domain: str,
        environment: str,
        region: str,
        account_id: str,
    ) -> "TemplateRenderer":
        """
        Create renderer with standard deployment variables

        Args:
            deployment_id: Deployment ID
            organization: Organization name
            project: Project name
            domain: Primary domain
            environment: Environment name (dev/stage/prod)
            region: AWS region
            account_id: AWS account ID

        Returns:
            TemplateRenderer with variables set
        """
        variables = {
            "deployment_id": deployment_id,
            "organization": organization,
            "project": project,
            "domain": domain,
            "environment": environment,
            "region": region,
            "account_id": account_id,
            # Nested access support
            "deployment": {
                "id": deployment_id,
                "org": organization,
                "project": project,
                "domain": domain,
            },
            "env": {
                "name": environment,
                "region": region,
                "account_id": account_id,
            },
        }

        return TemplateRenderer(variables)
