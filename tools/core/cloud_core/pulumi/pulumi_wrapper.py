"""
Pulumi Wrapper

Wraps Pulumi CLI and Automation API for stack operations.
Simplified implementation that can be enhanced with full Automation API later.
"""

import subprocess
import json
import shutil
import time
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from contextlib import contextmanager
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

    def preview(self, cwd: Optional[Path] = None, config_file: Optional[Path] = None) -> Dict[str, Any]:
        """
        Run pulumi preview

        Args:
            cwd: Working directory
            config_file: Path to config file (relative to cwd or absolute)

        Returns:
            Preview result summary

        Raises:
            PulumiError: If preview fails
        """
        logger.info("Running Pulumi preview")

        try:
            cmd = ["pulumi", "preview", "--json", "--non-interactive"]
            if config_file:
                cmd.extend(["--config-file", str(config_file)])

                result = self._run_command(cmd, cwd=cwd)

                # Parse JSON output (simplified)
                # Real implementation would parse the JSON streaming output
                return {"success": True, "output": result.stdout}

        except PulumiError as e:
            logger.error(f"Preview failed: {e}")
            return {"success": False, "error": str(e)}

    def up(
        self, cwd: Optional[Path] = None, yes: bool = True, config_file: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Deploy stack (pulumi up)

        Args:
            cwd: Working directory
            yes: Auto-approve changes
            config_file: Path to config file (relative to cwd or absolute)

        Returns:
            Deployment result summary

        Raises:
            PulumiError: If deployment fails
        """
        logger.info("Running Pulumi up")

        cmd = ["pulumi", "up", "--non-interactive"]
        if yes:
            cmd.append("--yes")
        if config_file:
            cmd.extend(["--config-file", str(config_file)])

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

    def _backup_pulumi_yaml(self, stack_dir: Path) -> Optional[Path]:
        """
        Backup original Pulumi.yaml

        Args:
            stack_dir: Stack directory containing Pulumi.yaml

        Returns:
            Path to backup file, or None if no backup created
        """
        pulumi_yaml = stack_dir / "Pulumi.yaml"
        if not pulumi_yaml.exists():
            logger.warning(f"No Pulumi.yaml found in {stack_dir}")
            return None

        backup_path = stack_dir / f"Pulumi.yaml.backup.{self.project}"

        # Clean up stale backup from previous run
        if backup_path.exists():
            logger.warning(f"Found stale backup {backup_path}, removing")
            backup_path.unlink()

        # Retry up to 3 times with exponential backoff
        for attempt in range(3):
            try:
                shutil.copy2(pulumi_yaml, backup_path)
                logger.debug(f"Backed up Pulumi.yaml to {backup_path}")
                return backup_path
            except (PermissionError, IOError) as e:
                if attempt < 2:
                    wait_time = 2 ** attempt  # 1s, 2s
                    logger.warning(f"Backup failed, retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                else:
                    raise PulumiError(f"Cannot backup Pulumi.yaml after 3 attempts: {e}")

        return None

    def _restore_pulumi_yaml(self, stack_dir: Path, backup_path: Optional[Path]) -> None:
        """
        Restore original Pulumi.yaml from backup

        Args:
            stack_dir: Stack directory
            backup_path: Path to backup file
        """
        if not backup_path or not backup_path.exists():
            return

        pulumi_yaml = stack_dir / "Pulumi.yaml"

        # Retry up to 3 times
        for attempt in range(3):
            try:
                shutil.move(str(backup_path), str(pulumi_yaml))
                logger.debug(f"Restored Pulumi.yaml from backup")
                return
            except (PermissionError, IOError) as e:
                if attempt < 2:
                    wait_time = 2 ** attempt
                    logger.warning(f"Restore failed, retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Cannot restore Pulumi.yaml after 3 attempts: {e}")
                    # Don't raise - we're in cleanup, best effort

    def _generate_pulumi_yaml(self, stack_dir: Path, manifest: Dict[str, Any], deployment_dir: Optional[Path] = None) -> None:
        """
        Generate deployment-specific Pulumi.yaml with composite project naming

        Args:
            stack_dir: Stack directory path
            manifest: Deployment manifest with organization, project, deployment_id
            deployment_dir: Optional deployment directory to store authoritative copy
        """
        # Build composite project name: DeploymentID-Organization-Project
        deployment_id = manifest.get("deployment_id", "")
        organization = manifest.get("organization", "")
        project = manifest.get("project", "")
        composite_project = f"{deployment_id}-{organization}-{project}"

        logger.info(f"Generating Pulumi.yaml with composite project: {composite_project}")

        pulumi_yaml = stack_dir / "Pulumi.yaml"

        # Read original to preserve runtime and description
        original_content = {}
        if pulumi_yaml.exists():
            try:
                with open(pulumi_yaml, 'r') as f:
                    original_content = yaml.safe_load(f) or {}
            except Exception as e:
                logger.warning(f"Could not read original Pulumi.yaml: {e}")

        # Generate new content with deployment project name
        new_content = {
            'name': composite_project,  # Use composite project name
            'runtime': original_content.get('runtime', 'nodejs'),
            'description': original_content.get('description', f'Deployment {composite_project} stack'),
        }

        # Write deployment-specific Pulumi.yaml
        try:
            with open(pulumi_yaml, 'w') as f:
                yaml.safe_dump(new_content, f, default_flow_style=False)
            logger.info(f"Generated Pulumi.yaml with composite project: {composite_project}")
        except Exception as e:
            raise PulumiError(f"Cannot generate Pulumi.yaml: {e}")

    @contextmanager
    def deployment_context(self, stack_dir: Path, manifest: Dict[str, Any], deployment_dir: Optional[Path] = None):
        """
        Context manager for deployment-specific Pulumi.yaml

        This ensures that Pulumi operations use the correct project name
        by temporarily replacing Pulumi.yaml in the stack directory.

        Usage:
            with pulumi_wrapper.deployment_context(stack_dir, manifest, deployment_dir):
                # Pulumi operations here
                pulumi_wrapper.select_stack(...)
                pulumi_wrapper.up(...)

        Args:
            stack_dir: Stack directory path
            manifest: Deployment manifest with organization, project, deployment_id
            deployment_dir: Optional deployment directory to store authoritative copy

        Yields:
            None - Context for operations
        """
        backup_path = None
        try:
            # Backup and generate
            backup_path = self._backup_pulumi_yaml(stack_dir)
            self._generate_pulumi_yaml(stack_dir, manifest, deployment_dir)
            logger.debug("Generated deployment-specific Pulumi.yaml")

            yield

        finally:
            # Always restore original
            self._restore_pulumi_yaml(stack_dir, backup_path)
