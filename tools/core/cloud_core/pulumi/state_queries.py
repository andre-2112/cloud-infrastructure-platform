"""
State Queries

Query Pulumi state for stack outputs and information.
"""

from typing import Dict, Any, Optional
from .pulumi_wrapper import PulumiWrapper
from ..utils.logger import get_logger

logger = get_logger(__name__)


class StateQueries:
    """Query Pulumi state"""

    def __init__(self, pulumi_wrapper: PulumiWrapper):
        """
        Initialize state queries

        Args:
            pulumi_wrapper: PulumiWrapper instance
        """
        self.pulumi = pulumi_wrapper

    def get_output(
        self, deployment_id: str, stack_name: str, environment: str, output_key: str
    ) -> Optional[Any]:
        """
        Get specific output from a stack

        Args:
            deployment_id: Deployment ID
            stack_name: Stack name
            environment: Environment
            output_key: Output key

        Returns:
            Output value, or None if not found
        """
        full_stack_name = (
            f"{self.pulumi.organization}/{self.pulumi.project}/"
            f"{deployment_id}-{stack_name}-{environment}"
        )

        return self.pulumi.get_stack_output(full_stack_name, output_key)

    def get_all_outputs(
        self, deployment_id: str, stack_name: str, environment: str
    ) -> Dict[str, Any]:
        """
        Get all outputs from a stack

        Args:
            deployment_id: Deployment ID
            stack_name: Stack name
            environment: Environment

        Returns:
            Dictionary of all outputs
        """
        full_stack_name = (
            f"{self.pulumi.organization}/{self.pulumi.project}/"
            f"{deployment_id}-{stack_name}-{environment}"
        )

        return self.pulumi.get_all_stack_outputs(full_stack_name)
