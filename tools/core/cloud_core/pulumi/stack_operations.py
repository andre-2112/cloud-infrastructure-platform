"""
Stack Operations

Higher-level stack operations built on PulumiWrapper.
"""

from pathlib import Path
from typing import Dict, Any, Optional
from .pulumi_wrapper import PulumiWrapper, PulumiError
from ..utils.logger import get_logger

logger = get_logger(__name__)


class StackOperations:
    """Higher-level stack operations"""

    def __init__(self, pulumi_wrapper: PulumiWrapper):
        """
        Initialize stack operations

        Args:
            pulumi_wrapper: PulumiWrapper instance
        """
        self.pulumi = pulumi_wrapper

    def deploy_stack(
        self,
        deployment_id: str,
        stack_name: str,
        environment: str,
        stack_dir: Path,
        config: Dict[str, str],
        preview_only: bool = False,
        config_file: Optional[Path] = None,
    ) -> tuple[bool, Optional[str]]:
        """
        Deploy a stack

        Args:
            deployment_id: Deployment ID (included in composite project name)
            stack_name: Stack name
            environment: Environment
            stack_dir: Path to stack directory
            config: Configuration values
            preview_only: If True, only preview changes
            config_file: Path to config file (optional)

        Returns:
            Tuple of (success, error_message)
        """
        # Construct Pulumi stack name (deployment_id is in composite project, not here)
        pulumi_stack_name = f"{stack_name}-{environment}"

        try:
            # Select/create stack
            self.pulumi.select_stack(pulumi_stack_name, create=True, cwd=stack_dir)

            # Set configuration (only if no config file provided)
            if not config_file:
                self.pulumi.set_all_config(config, cwd=stack_dir)

            if preview_only:
                # Preview only
                result = self.pulumi.preview(cwd=stack_dir, config_file=config_file)
                return result.get("success", False), result.get("error")
            else:
                # Deploy
                result = self.pulumi.up(cwd=stack_dir, yes=True, config_file=config_file)
                return result.get("success", False), None

        except PulumiError as e:
            logger.error(f"Error deploying stack {stack_name}: {e}")
            return False, str(e)

    def destroy_stack(
        self,
        deployment_id: str,
        stack_name: str,
        environment: str,
        stack_dir: Path,
    ) -> tuple[bool, Optional[str]]:
        """
        Destroy a stack

        Args:
            deployment_id: Deployment ID (included in composite project name)
            stack_name: Stack name
            environment: Environment
            stack_dir: Path to stack directory

        Returns:
            Tuple of (success, error_message)
        """
        pulumi_stack_name = f"{stack_name}-{environment}"

        try:
            # Select stack
            self.pulumi.select_stack(pulumi_stack_name, create=False, cwd=stack_dir)

            # Destroy
            result = self.pulumi.destroy(cwd=stack_dir, yes=True)
            return result.get("success", False), None

        except PulumiError as e:
            logger.error(f"Error destroying stack {stack_name}: {e}")
            return False, str(e)

    def refresh_stack(
        self,
        deployment_id: str,
        stack_name: str,
        environment: str,
        stack_dir: Path,
    ) -> tuple[bool, Optional[str]]:
        """
        Refresh stack state

        Args:
            deployment_id: Deployment ID (included in composite project name)
            stack_name: Stack name
            environment: Environment
            stack_dir: Path to stack directory

        Returns:
            Tuple of (success, error_message)
        """
        pulumi_stack_name = f"{stack_name}-{environment}"

        try:
            self.pulumi.select_stack(pulumi_stack_name, create=False, cwd=stack_dir)
            result = self.pulumi.refresh(cwd=stack_dir)
            return result.get("success", False), None

        except PulumiError as e:
            logger.error(f"Error refreshing stack {stack_name}: {e}")
            return False, str(e)
