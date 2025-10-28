"""
Stack Reference Resolver

Resolves cross-stack references by querying Pulumi state.
Handles placeholders like: {{stack.network.vpcId}}, {{stack.security.sgId}}
"""

from typing import Dict, Any, Optional, Callable
from ..utils.logger import get_logger

logger = get_logger(__name__)


class StackReferenceResolver:
    """Resolves cross-stack references from Pulumi state"""

    def __init__(
        self,
        deployment_id: str,
        environment: str,
        organization: str,
        project: str,
    ):
        """
        Initialize stack reference resolver

        Args:
            deployment_id: Deployment ID
            environment: Environment name (dev/stage/prod)
            organization: Organization name (for Pulumi stack name)
            project: Project name (for Pulumi stack name)
        """
        self.deployment_id = deployment_id
        self.environment = environment
        self.organization = organization
        self.project = project

        # Cache for resolved values
        self.cache: Dict[str, Any] = {}

        # Pulumi query function (injected)
        self.pulumi_query_func: Optional[Callable[[str, str], Dict[str, Any]]] = None

    def set_pulumi_query_func(
        self, func: Callable[[str, str], Dict[str, Any]]
    ) -> None:
        """
        Set function to query Pulumi stack outputs

        Args:
            func: Function that takes (stack_name, output_key) and returns output value
                 Should return None if output not found
        """
        self.pulumi_query_func = func
        logger.debug("Pulumi query function registered")

    def resolve(self, placeholder: str) -> Optional[Any]:
        """
        Resolve stack reference placeholder

        Args:
            placeholder: Placeholder in format "stack.{stack_name}.{output_key}"
                        E.g., "stack.network.vpcId"

        Returns:
            Resolved value, or None if not found
        """
        # Check cache first
        if placeholder in self.cache:
            logger.debug(f"Resolved {placeholder} from cache")
            return self.cache[placeholder]

        # Parse placeholder
        if not placeholder.startswith("stack."):
            return None

        parts = placeholder.split(".", 2)

        if len(parts) < 3:
            logger.warning(f"Invalid stack reference format: {placeholder}")
            return None

        stack_name = parts[1]
        output_key = parts[2]

        # Query Pulumi state
        value = self._query_stack_output(stack_name, output_key)

        if value is not None:
            # Cache the result
            self.cache[placeholder] = value
            logger.debug(f"Resolved {placeholder} = {value}")

        return value

    def _query_stack_output(self, stack_name: str, output_key: str) -> Optional[Any]:
        """
        Query Pulumi stack for output value

        Args:
            stack_name: Name of the stack (e.g., "network")
            output_key: Output key to retrieve (e.g., "vpcId")

        Returns:
            Output value, or None if not found
        """
        if not self.pulumi_query_func:
            logger.error("Pulumi query function not configured")
            return None

        # Construct full Pulumi stack name
        # Format: {org}/{project}/{deployment_id}-{stack_name}-{environment}
        pulumi_stack_name = (
            f"{self.organization}/{self.project}/"
            f"{self.deployment_id}-{stack_name}-{self.environment}"
        )

        try:
            # Query using injected function
            outputs = self.pulumi_query_func(pulumi_stack_name, output_key)
            return outputs.get(output_key) if outputs else None

        except Exception as e:
            logger.error(
                f"Error querying Pulumi stack {pulumi_stack_name} for {output_key}: {e}"
            )
            return None

    def resolve_all_from_stack(self, stack_name: str) -> Dict[str, Any]:
        """
        Resolve all outputs from a stack

        Args:
            stack_name: Name of the stack

        Returns:
            Dictionary of all stack outputs
        """
        if not self.pulumi_query_func:
            logger.error("Pulumi query function not configured")
            return {}

        pulumi_stack_name = (
            f"{self.organization}/{self.project}/"
            f"{self.deployment_id}-{stack_name}-{self.environment}"
        )

        try:
            # Query all outputs (passing None as output_key convention)
            outputs = self.pulumi_query_func(pulumi_stack_name, None)
            return outputs or {}

        except Exception as e:
            logger.error(f"Error querying all outputs from {pulumi_stack_name}: {e}")
            return {}

    def clear_cache(self) -> None:
        """Clear the resolution cache"""
        self.cache.clear()
        logger.debug("Cleared stack reference cache")

    def preload_stack_outputs(self, stack_name: str) -> int:
        """
        Preload all outputs from a stack into cache

        Args:
            stack_name: Name of the stack

        Returns:
            Number of outputs cached
        """
        outputs = self.resolve_all_from_stack(stack_name)

        count = 0
        for output_key, value in outputs.items():
            placeholder = f"stack.{stack_name}.{output_key}"
            self.cache[placeholder] = value
            count += 1

        logger.debug(f"Preloaded {count} outputs from stack {stack_name}")
        return count

    def get_stack_name_from_placeholder(self, placeholder: str) -> Optional[str]:
        """
        Extract stack name from placeholder

        Args:
            placeholder: Stack reference placeholder

        Returns:
            Stack name, or None if not a valid stack reference
        """
        if not placeholder.startswith("stack."):
            return None

        parts = placeholder.split(".", 2)
        if len(parts) >= 2:
            return parts[1]

        return None

    def is_stack_reference(self, placeholder: str) -> bool:
        """
        Check if placeholder is a stack reference

        Args:
            placeholder: Placeholder to check

        Returns:
            True if stack reference format
        """
        return placeholder.startswith("stack.") and len(placeholder.split(".")) >= 3


def create_resolver_with_pulumi(
    deployment_id: str,
    environment: str,
    organization: str,
    project: str,
    pulumi_wrapper: Any,  # Type will be PulumiWrapper from pulumi module
) -> StackReferenceResolver:
    """
    Create stack reference resolver with Pulumi wrapper

    Args:
        deployment_id: Deployment ID
        environment: Environment
        organization: Organization name
        project: Project name
        pulumi_wrapper: PulumiWrapper instance

    Returns:
        Configured StackReferenceResolver
    """
    resolver = StackReferenceResolver(
        deployment_id=deployment_id,
        environment=environment,
        organization=organization,
        project=project,
    )

    # Create query function that uses Pulumi wrapper
    def query_func(stack_name: str, output_key: Optional[str]) -> Dict[str, Any]:
        """Query Pulumi stack outputs"""
        try:
            if output_key:
                # Query specific output
                value = pulumi_wrapper.get_stack_output(stack_name, output_key)
                return {output_key: value} if value is not None else {}
            else:
                # Query all outputs
                return pulumi_wrapper.get_all_stack_outputs(stack_name)
        except Exception as e:
            logger.error(f"Error querying Pulumi: {e}")
            return {}

    resolver.set_pulumi_query_func(query_func)

    return resolver
