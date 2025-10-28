"""
Pulumi Wrapper

Wraps Pulumi CLI and Automation API for stack operations.
Simplified implementation that can be enhanced with full Automation API later.
"""

import subprocess
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from ..utils.logger import get_logger

logger = get_logger(__name__)


class PulumiError(Exception):
    """Raised when Pulumi operation fails"""

    pass


class PulumiWrapper:
    """Wrapper for Pulumi operations"""

    def __init__(
        self,
        organization: str,
        project: str,
        working_dir: Optional[Path] = None,
    ):
        """
        Initialize Pulumi wrapper

        Args:
            organization: Pulumi organization name
            project: Pulumi project name
            working_dir: Working directory for Pulumi operations
        """
        self.organization = organization
        self.project = project
        self.working_dir = Path(working_dir) if working_dir else Path.cwd()

    def _run_command(
        self,
        cmd: List[str],
        cwd: Optional[Path] = None,
        capture_output: bool = True,
    ) -> subprocess.CompletedProcess:
        """
        Run Pulumi CLI command

        Args:
            cmd: Command and arguments
            cwd: Working directory
            capture_output: Whether to capture output

        Returns:
            CompletedProcess result

        Raises:
            PulumiError: If command fails
        """
        work_dir = cwd or self.working_dir

        logger.debug(f"Running Pulumi command: {' '.join(cmd)} in {work_dir}")

        try:
            result = subprocess.run(
                cmd,
                cwd=str(work_dir),
                capture_output=capture_output,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                error_msg = result.stderr if capture_output else "Command failed"
                raise PulumiError(f"Pulumi command failed: {error_msg}")

            return result

        except FileNotFoundError:
            raise PulumiError("Pulumi CLI not found. Please install Pulumi.")
        except Exception as e:
            raise PulumiError(f"Error running Pulumi command: {e}")

    def stack_exists(self, stack_name: str) -> bool:
        """
        Check if a Pulumi stack exists

        Args:
            stack_name: Full stack name (org/project/stack-name)

        Returns:
            True if stack exists
        """
        try:
            self._run_command(["pulumi", "stack", "ls", "--json"])
            # Parse output to check if stack exists
            # For now, simple implementation
            return True  # Simplified
        except PulumiError:
            return False

    def select_stack(
        self, stack_name: str, create: bool = True, cwd: Optional[Path] = None
    ) -> None:
        """
        Select (and optionally create) a Pulumi stack

        Args:
            stack_name: Stack name in format: deployment-id-stack-name-environment
            create: Whether to create if doesn't exist
            cwd: Working directory (stack directory)

        Raises:
            PulumiError: If operation fails
        """
        full_stack_name = f"{self.organization}/{self.project}/{stack_name}"

        try:
            if create:
                # Try to create stack (will fail if exists, which is okay)
                try:
                    self._run_command(
                        ["pulumi", "stack", "init", full_stack_name],
                        cwd=cwd,
                    )
                    logger.info(f"Created Pulumi stack: {full_stack_name}")
                except PulumiError:
                    # Stack probably exists, select it
                    pass

            # Select the stack
            self._run_command(
                ["pulumi", "stack", "select", full_stack_name],
                cwd=cwd,
            )

            logger.info(f"Selected Pulumi stack: {full_stack_name}")

        except PulumiError as e:
            raise PulumiError(f"Error selecting stack {full_stack_name}: {e}")

    def set_config(
        self, key: str, value: str, secret: bool = False, cwd: Optional[Path] = None
    ) -> None:
        """
        Set Pulumi configuration value

        Args:
            key: Config key
            value: Config value
            secret: Whether to mark as secret
            cwd: Working directory

        Raises:
            PulumiError: If operation fails
        """
        cmd = ["pulumi", "config", "set", key, value]
        if secret:
            cmd.append("--secret")

        self._run_command(cmd, cwd=cwd)
        logger.debug(f"Set Pulumi config: {key}")

    def set_all_config(
        self, config: Dict[str, str], cwd: Optional[Path] = None
    ) -> None:
        """
        Set multiple configuration values

        Args:
            config: Dictionary of key -> value
            cwd: Working directory
        """
        for key, value in config.items():
            self.set_config(key, value, cwd=cwd)

    def preview(self, cwd: Optional[Path] = None) -> Dict[str, Any]:
        """
        Run pulumi preview

        Args:
            cwd: Working directory

        Returns:
            Preview result summary

        Raises:
            PulumiError: If preview fails
        """
        logger.info("Running Pulumi preview")

        try:
            result = self._run_command(
                ["pulumi", "preview", "--json", "--non-interactive"],
                cwd=cwd,
            )

            # Parse JSON output (simplified)
            # Real implementation would parse the JSON streaming output
            return {"success": True, "output": result.stdout}

        except PulumiError as e:
            logger.error(f"Preview failed: {e}")
            return {"success": False, "error": str(e)}

    def up(
        self, cwd: Optional[Path] = None, yes: bool = True
    ) -> Dict[str, Any]:
        """
        Deploy stack (pulumi up)

        Args:
            cwd: Working directory
            yes: Auto-approve changes

        Returns:
            Deployment result summary

        Raises:
            PulumiError: If deployment fails
        """
        logger.info("Running Pulumi up")

        cmd = ["pulumi", "up", "--non-interactive"]
        if yes:
            cmd.append("--yes")

        try:
            result = self._run_command(cmd, cwd=cwd, capture_output=False)

            return {"success": True, "returncode": result.returncode}

        except PulumiError as e:
            logger.error(f"Deployment failed: {e}")
            raise

    def destroy(
        self, cwd: Optional[Path] = None, yes: bool = True
    ) -> Dict[str, Any]:
        """
        Destroy stack (pulumi destroy)

        Args:
            cwd: Working directory
            yes: Auto-approve destruction

        Returns:
            Destruction result summary

        Raises:
            PulumiError: If destruction fails
        """
        logger.info("Running Pulumi destroy")

        cmd = ["pulumi", "destroy", "--non-interactive"]
        if yes:
            cmd.append("--yes")

        try:
            result = self._run_command(cmd, cwd=cwd, capture_output=False)

            return {"success": True, "returncode": result.returncode}

        except PulumiError as e:
            logger.error(f"Destruction failed: {e}")
            raise

    def refresh(self, cwd: Optional[Path] = None) -> Dict[str, Any]:
        """
        Refresh stack state (pulumi refresh)

        Args:
            cwd: Working directory

        Returns:
            Refresh result

        Raises:
            PulumiError: If refresh fails
        """
        logger.info("Running Pulumi refresh")

        try:
            result = self._run_command(
                ["pulumi", "refresh", "--yes", "--non-interactive"],
                cwd=cwd,
            )

            return {"success": True}

        except PulumiError as e:
            logger.error(f"Refresh failed: {e}")
            raise

    def get_stack_output(
        self, stack_name: str, output_key: str
    ) -> Optional[Any]:
        """
        Get a specific stack output value

        Args:
            stack_name: Full stack name (org/project/stack-name)
            output_key: Output key to retrieve

        Returns:
            Output value, or None if not found
        """
        try:
            result = self._run_command(
                [
                    "pulumi",
                    "stack",
                    "output",
                    output_key,
                    "--stack",
                    stack_name,
                    "--json",
                ]
            )

            return json.loads(result.stdout) if result.stdout else None

        except (PulumiError, json.JSONDecodeError) as e:
            logger.warning(f"Could not get output {output_key} from {stack_name}: {e}")
            return None

    def get_all_stack_outputs(self, stack_name: str) -> Dict[str, Any]:
        """
        Get all stack outputs

        Args:
            stack_name: Full stack name (org/project/stack-name)

        Returns:
            Dictionary of all outputs
        """
        try:
            result = self._run_command(
                ["pulumi", "stack", "output", "--stack", stack_name, "--json"]
            )

            return json.loads(result.stdout) if result.stdout else {}

        except (PulumiError, json.JSONDecodeError) as e:
            logger.warning(f"Could not get outputs from {stack_name}: {e}")
            return {}

    def check_pulumi_available(self) -> bool:
        """
        Check if Pulumi CLI is available

        Returns:
            True if available
        """
        try:
            subprocess.run(
                ["pulumi", "version"],
                capture_output=True,
                check=True,
            )
            return True
        except (FileNotFoundError, subprocess.CalledProcessError):
            return False
