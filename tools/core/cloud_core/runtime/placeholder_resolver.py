"""
Placeholder Resolver

Resolves runtime placeholders in configuration values.
Supports: {{deployment.id}}, ${stack.network.vpcId}, {{aws.vpc.default}}, etc.
Both {{...}} and ${...} syntaxes are supported.
"""

import re
from typing import Dict, Any, Optional, Callable
from ..utils.logger import get_logger

logger = get_logger(__name__)


class PlaceholderResolver:
    """Resolves runtime placeholders in configuration"""

    # Pattern for placeholders: {{type.path.to.value}} or ${type.path.to.value}
    # Supports both {{...}} and ${...} syntax
    PLACEHOLDER_PATTERN = re.compile(r"(?:\{\{([a-zA-Z0-9_\.]+)\}\}|\$\{([a-zA-Z0-9_\.]+)\})")

    def __init__(self):
        """Initialize placeholder resolver"""
        # Resolvers for different placeholder types
        self.resolvers: Dict[str, Callable] = {}
        self.cache: Dict[str, Any] = {}
        self.strict_mode = False

    def register_resolver(
        self, prefix: str, resolver_func: Callable[[str], Optional[Any]]
    ) -> None:
        """
        Register a resolver for a placeholder prefix

        Args:
            prefix: Placeholder prefix (e.g., "deployment", "stack", "aws")
            resolver_func: Function to resolve placeholders with this prefix
                          Takes full placeholder path, returns value or None
        """
        self.resolvers[prefix] = resolver_func
        logger.debug(f"Registered resolver for prefix: {prefix}")

    def resolve(
        self, value: Any, context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Resolve placeholders in a value

        Args:
            value: Value to resolve (can be string, dict, list, or primitive)
            context: Optional context dictionary for resolving

        Returns:
            Value with placeholders resolved
        """
        if isinstance(value, str):
            return self._resolve_string(value, context)
        elif isinstance(value, dict):
            return self._resolve_dict(value, context)
        elif isinstance(value, list):
            return self._resolve_list(value, context)
        else:
            # Primitive value, return as-is
            return value

    def _resolve_string(
        self, text: str, context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Resolve placeholders in a string

        Args:
            text: String with potential placeholders
            context: Optional context

        Returns:
            String with placeholders resolved
        """

        def replace_placeholder(match):
            # Get placeholder from either group ({{...}} or ${...})
            placeholder = match.group(1) if match.group(1) else match.group(2)

            # Check cache first
            if placeholder in self.cache:
                logger.debug(f"Resolved placeholder '{placeholder}' from cache")
                return str(self.cache[placeholder])

            # Try to resolve
            value = self._resolve_placeholder(placeholder, context)

            if value is not None:
                # Cache the result
                self.cache[placeholder] = value
                logger.debug(f"Resolved placeholder '{placeholder}' = {value}")
                return str(value)

            # Not resolved
            if self.strict_mode:
                raise ValueError(f"Unable to resolve placeholder: {match.group(0)}")

            # Leave placeholder as-is in non-strict mode
            logger.warning(f"Unable to resolve placeholder: {match.group(0)}")
            return match.group(0)

        return self.PLACEHOLDER_PATTERN.sub(replace_placeholder, text)

    def _resolve_dict(
        self, data: Dict[str, Any], context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Resolve placeholders in all dict values"""
        result = {}
        for key, value in data.items():
            result[key] = self.resolve(value, context)
        return result

    def _resolve_list(
        self, items: list, context: Optional[Dict[str, Any]] = None
    ) -> list:
        """Resolve placeholders in all list items"""
        return [self.resolve(item, context) for item in items]

    def _resolve_placeholder(
        self, placeholder: str, context: Optional[Dict[str, Any]] = None
    ) -> Optional[Any]:
        """
        Resolve a single placeholder

        Args:
            placeholder: Placeholder path (e.g., "deployment.id", "stack.network.vpcId")
            context: Optional context

        Returns:
            Resolved value, or None if not resolved
        """
        # Check context first (simple key-value lookup)
        if context and placeholder in context:
            return context[placeholder]

        # Check for nested context access
        if context and "." in placeholder:
            value = self._get_nested_value(context, placeholder)
            if value is not None:
                return value

        # Try registered resolvers by prefix
        if "." in placeholder:
            prefix = placeholder.split(".")[0]
            if prefix in self.resolvers:
                resolver_func = self.resolvers[prefix]
                try:
                    return resolver_func(placeholder)
                except Exception as e:
                    logger.error(f"Error resolving {{{{{placeholder}}}}}: {e}")
                    return None

        return None

    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Optional[Any]:
        """
        Get nested value from dictionary using dot notation

        Args:
            data: Dictionary to search
            path: Dot-separated path (e.g., "deployment.id")

        Returns:
            Value if found, None otherwise
        """
        parts = path.split(".")
        current = data

        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None

        return current

    def has_placeholders(self, value: Any) -> bool:
        """
        Check if value contains placeholders

        Args:
            value: Value to check

        Returns:
            True if placeholders found
        """
        if isinstance(value, str):
            return bool(self.PLACEHOLDER_PATTERN.search(value))
        elif isinstance(value, dict):
            return any(self.has_placeholders(v) for v in value.values())
        elif isinstance(value, list):
            return any(self.has_placeholders(item) for item in value)
        else:
            return False

    def get_placeholders(self, value: Any) -> list[str]:
        """
        Extract all placeholders from value

        Args:
            value: Value to extract from

        Returns:
            List of placeholder paths
        """
        placeholders = []

        if isinstance(value, str):
            matches = self.PLACEHOLDER_PATTERN.findall(value)
            # Each match is a tuple (group1, group2) - take non-empty one
            for match in matches:
                placeholder = match[0] if match[0] else match[1]
                placeholders.append(placeholder)
        elif isinstance(value, dict):
            for v in value.values():
                placeholders.extend(self.get_placeholders(v))
        elif isinstance(value, list):
            for item in value:
                placeholders.extend(self.get_placeholders(item))

        return list(set(placeholders))  # Remove duplicates

    def clear_cache(self) -> None:
        """Clear the resolution cache"""
        self.cache.clear()
        logger.debug("Cleared placeholder cache")

    def set_strict_mode(self, strict: bool) -> None:
        """
        Set strict mode

        Args:
            strict: If True, raise error for unresolved placeholders
        """
        self.strict_mode = strict


def create_deployment_resolver(deployment_context: Dict[str, Any]) -> PlaceholderResolver:
    """
    Create resolver with deployment context

    Args:
        deployment_context: Deployment context with keys like:
                           deployment_id, organization, project, domain, environment, etc.

    Returns:
        PlaceholderResolver with deployment resolver registered
    """
    resolver = PlaceholderResolver()

    # Register deployment resolver
    def deployment_resolver(placeholder: str) -> Optional[Any]:
        # Remove "deployment." prefix
        if placeholder.startswith("deployment."):
            key = placeholder.replace("deployment.", "", 1)
            return deployment_context.get(key)
        return None

    resolver.register_resolver("deployment", deployment_resolver)

    # Also register "env" resolver for environment context
    def env_resolver(placeholder: str) -> Optional[Any]:
        if placeholder.startswith("env."):
            key = placeholder.replace("env.", "", 1)
            return deployment_context.get(key)
        return None

    resolver.register_resolver("env", env_resolver)

    return resolver
