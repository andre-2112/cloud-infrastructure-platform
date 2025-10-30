"""
Protocol definitions for cloud_core API contracts.

This module defines the expected interfaces for cloud_core components
that the CLI depends on. These protocols serve as documentation and
can be used for type checking.

Architecture: 4.1
"""

from typing import Protocol, Dict, Any, Optional, Tuple, List
from pathlib import Path


class StateManagerProtocol(Protocol):
    """Protocol for StateManager from cloud_core.deployment"""

    def update_stack_status(
        self,
        deployment_id: str,
        environment: str,
        stack_name: str,
        status: str
    ) -> None:
        """
        Update the status of a stack in the deployment state.

        Args:
            deployment_id: Deployment identifier
            environment: Environment name (dev/stage/prod)
            stack_name: Name of the stack
            status: New status value (e.g., "deploying", "deployed", "failed")
        """
        ...

    def get_stack_status(
        self,
        deployment_id: str,
        environment: str,
        stack_name: str
    ) -> Optional[str]:
        """
        Get the current status of a stack.

        Args:
            deployment_id: Deployment identifier
            environment: Environment name
            stack_name: Name of the stack

        Returns:
            Current status string, or None if not found
        """
        ...

    def record_operation(
        self,
        deployment_id: str,
        environment: str,
        operation_type: str,
        details: Dict[str, Any]
    ) -> str:
        """
        Record a deployment operation for auditing and rollback.

        Args:
            deployment_id: Deployment identifier
            environment: Environment name
            operation_type: Type of operation (deploy, destroy, etc.)
            details: Operation details

        Returns:
            Operation ID
        """
        ...


class StackOperationsProtocol(Protocol):
    """Protocol for StackOperations from cloud_core.orchestrator"""

    def deploy_stack(
        self,
        stack_name: str,
        environment: str,
        config: Dict[str, Any],
        preview: bool = False
    ) -> Tuple[bool, Optional[str]]:
        """
        Deploy a single stack.

        IMPORTANT: Method name is 'deploy_stack', not 'deploy'.

        Args:
            stack_name: Name of the stack to deploy
            environment: Target environment
            config: Stack configuration
            preview: If True, only preview changes without deploying

        Returns:
            Tuple of (success: bool, error_message: Optional[str])
            - (True, None) on success
            - (False, error_message) on failure
        """
        ...

    def destroy_stack(
        self,
        stack_name: str,
        environment: str,
        config: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """
        Destroy a single stack.

        IMPORTANT: Method name is 'destroy_stack', not 'destroy'.

        Args:
            stack_name: Name of the stack to destroy
            environment: Target environment
            config: Stack configuration

        Returns:
            Tuple of (success: bool, error_message: Optional[str])
            - (True, None) on success
            - (False, error_message) on failure
        """
        ...

    def get_stack_outputs(
        self,
        stack_name: str,
        environment: str
    ) -> Dict[str, Any]:
        """
        Get outputs from a deployed stack.

        Args:
            stack_name: Name of the stack
            environment: Target environment

        Returns:
            Dictionary of stack outputs
        """
        ...


class PulumiWrapperProtocol(Protocol):
    """Protocol for PulumiWrapper from cloud_core.pulumi"""

    def __init__(
        self,
        organization: str,
        project: str,
        stack_dir: Optional[Path] = None
    ) -> None:
        """
        Initialize PulumiWrapper.

        CRITICAL: Must use named parameters, not positional.
        CRITICAL: organization parameter must be Pulumi Cloud org (manifest.pulumiOrg),
                  NOT deployment organization (manifest.organization).

        Args:
            organization: Pulumi Cloud organization name (from manifest.pulumiOrg)
            project: Pulumi project name
            stack_dir: Optional path to stack directory
        """
        ...

    def up(
        self,
        stack_name: str,
        environment: str,
        config: Dict[str, Any],
        preview: bool = False
    ) -> Tuple[bool, Optional[str]]:
        """
        Run pulumi up on a stack.

        Args:
            stack_name: Name of the stack
            environment: Target environment
            config: Stack configuration
            preview: If True, only preview changes

        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        ...

    def destroy(
        self,
        stack_name: str,
        environment: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Run pulumi destroy on a stack.

        Args:
            stack_name: Name of the stack
            environment: Target environment

        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        ...

    def get_outputs(
        self,
        stack_name: str,
        environment: str
    ) -> Dict[str, Any]:
        """
        Get stack outputs.

        Args:
            stack_name: Name of the stack
            environment: Target environment

        Returns:
            Dictionary of outputs
        """
        ...


class DeploymentManagerProtocol(Protocol):
    """Protocol for DeploymentManager from cloud_core.deployment"""

    def get_deployment_dir(self, deployment_id: str) -> Path:
        """
        Get the directory path for a deployment.

        Args:
            deployment_id: Deployment identifier

        Returns:
            Path to deployment directory
        """
        ...

    def load_manifest(self, deployment_id: str) -> Dict[str, Any]:
        """
        Load the deployment manifest.

        IMPORTANT: Returns v4.1 flat format manifest.
        Required fields:
        - version: "4.1"
        - deployment_id: str
        - organization: str (deployment org)
        - pulumiOrg: str (Pulumi Cloud org) - CRITICAL
        - project: str
        - domain: str
        - environments: Dict[str, Dict]
        - stacks: Dict[str, Dict]

        Args:
            deployment_id: Deployment identifier

        Returns:
            Manifest dictionary in v4.1 format
        """
        ...

    def create_deployment(
        self,
        deployment_id: str,
        manifest: Dict[str, Any]
    ) -> bool:
        """
        Create a new deployment.

        Args:
            deployment_id: Deployment identifier
            manifest: Deployment manifest in v4.1 format

        Returns:
            True on success, False on failure
        """
        ...

    def list_deployments(self) -> List[Dict[str, Any]]:
        """
        List all deployments.

        Returns:
            List of deployment metadata dictionaries
        """
        ...


class OrchestratorProtocol(Protocol):
    """Protocol for Orchestrator from cloud_core.orchestrator"""

    def create_plan(
        self,
        manifest: Dict[str, Any],
        environment: str
    ) -> Any:  # Returns DeploymentPlan
        """
        Create a deployment plan based on stack dependencies.

        Args:
            manifest: Deployment manifest in v4.1 format
            environment: Target environment

        Returns:
            DeploymentPlan object with layers of stacks to deploy
        """
        ...

    def create_destroy_plan(
        self,
        manifest: Dict[str, Any],
        environment: str
    ) -> Any:  # Returns DeploymentPlan
        """
        Create a destroy plan (reverse order of deployment).

        Args:
            manifest: Deployment manifest in v4.1 format
            environment: Target environment

        Returns:
            DeploymentPlan object with layers in reverse order
        """
        ...

    async def execute_plan(
        self,
        plan: Any,  # DeploymentPlan
        stack_operations: StackOperationsProtocol,
        state_manager: StateManagerProtocol,
        max_parallel: int = 3
    ) -> bool:
        """
        Execute a deployment plan asynchronously.

        Args:
            plan: DeploymentPlan to execute
            stack_operations: StackOperations instance
            state_manager: StateManager instance
            max_parallel: Maximum parallel stack deployments

        Returns:
            True if all operations succeeded, False otherwise
        """
        ...

    async def execute_destroy(
        self,
        plan: Any,  # DeploymentPlan
        stack_operations: StackOperationsProtocol,
        state_manager: StateManagerProtocol
    ) -> bool:
        """
        Execute a destroy plan asynchronously.

        Args:
            plan: DeploymentPlan to execute
            stack_operations: StackOperations instance
            state_manager: StateManager instance

        Returns:
            True if all operations succeeded, False otherwise
        """
        ...


class ManifestValidatorProtocol(Protocol):
    """Protocol for ManifestValidator from cloud_core.validation"""

    def validate_file(self, manifest_path: Path) -> bool:
        """
        Validate a manifest file.

        Args:
            manifest_path: Path to manifest file

        Returns:
            True if valid, False otherwise
        """
        ...

    def validate(self, manifest: Dict[str, Any]) -> bool:
        """
        Validate a manifest dictionary.

        IMPORTANT: Validates v4.1 format including required pulumiOrg field.

        Args:
            manifest: Manifest dictionary

        Returns:
            True if valid, False otherwise
        """
        ...

    def get_errors(self) -> List[str]:
        """
        Get validation errors from the last validation.

        Returns:
            List of error messages
        """
        ...


class DependencyValidatorProtocol(Protocol):
    """Protocol for DependencyValidator from cloud_core.validation"""

    def validate(self, manifest: Dict[str, Any]) -> bool:
        """
        Validate stack dependencies for cycles and missing stacks.

        Args:
            manifest: Deployment manifest

        Returns:
            True if dependencies are valid, False otherwise
        """
        ...

    def get_errors(self) -> List[str]:
        """
        Get validation errors.

        Returns:
            List of error messages
        """
        ...


class ConfigGeneratorProtocol(Protocol):
    """Protocol for ConfigGenerator from cloud_core.pulumi"""

    def generate_stack_config(
        self,
        stack_name: str,
        environment: str,
        manifest: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate Pulumi configuration for a stack.

        Args:
            stack_name: Name of the stack
            environment: Target environment
            manifest: Deployment manifest

        Returns:
            Dictionary of Pulumi config values
        """
        ...


# Export all protocols
__all__ = [
    "StateManagerProtocol",
    "StackOperationsProtocol",
    "PulumiWrapperProtocol",
    "DeploymentManagerProtocol",
    "OrchestratorProtocol",
    "ManifestValidatorProtocol",
    "DependencyValidatorProtocol",
    "ConfigGeneratorProtocol",
]
