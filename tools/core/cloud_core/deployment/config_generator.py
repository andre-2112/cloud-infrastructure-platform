"""
Config Generator

Generates stack configuration files from deployment manifest.
"""

from pathlib import Path
from typing import Dict, Any, Optional, List
import yaml

from ..utils.logger import get_logger

logger = get_logger(__name__)


class ConfigGenerator:
    """Generates stack configuration files"""

    def __init__(self, deployment_dir: Path):
        """
        Initialize config generator

        Args:
            deployment_dir: Path to deployment directory
        """
        self.deployment_dir = Path(deployment_dir)
        self.config_dir = self.deployment_dir / "config"
        self.manifest_path = self.deployment_dir / "deployment-manifest.yaml"

        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def generate_all_configs(
        self, manifest: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Path]:
        """
        Generate configuration files for all stacks

        Args:
            manifest: Optional manifest (loads from file if not provided)

        Returns:
            Dictionary of stack_name -> config_file_path
        """
        if manifest is None:
            manifest = self._load_manifest()

        generated_files = {}

        stacks = manifest.get("stacks", {})

        for stack_name, stack_config in stacks.items():
            if not stack_config.get("enabled", True):
                logger.debug(f"Skipping config for disabled stack: {stack_name}")
                continue

            config_file = self.generate_stack_config(stack_name, manifest)
            generated_files[stack_name] = config_file

        logger.info(f"Generated {len(generated_files)} stack configuration files")
        return generated_files

    def generate_stack_config(
        self,
        stack_name: str,
        manifest: Optional[Dict[str, Any]] = None,
        environment: str = "dev",
    ) -> Path:
        """
        Generate configuration file for a single stack in Pulumi format

        Args:
            stack_name: Name of the stack
            manifest: Optional manifest (loads from file if not provided)
            environment: Environment to generate config for

        Returns:
            Path to generated config file
        """
        if manifest is None:
            manifest = self._load_manifest()

        # Get stack configuration from manifest
        stack_config = manifest.get("stacks", {}).get(stack_name)

        if not stack_config:
            raise ValueError(f"Stack '{stack_name}' not found in manifest")

        # Get environment configuration
        env_config = manifest.get("environments", {}).get(environment)

        if not env_config:
            raise ValueError(f"Environment '{environment}' not found in manifest")

        # Write config file in Pulumi format
        config_file = self.config_dir / f"{stack_name}.{environment}.yaml"

        # Build composite project name: DeploymentID-Organization-Project
        deployment_id = manifest.get("deployment_id", "")
        organization = manifest.get("organization", "")
        project = manifest.get("project", "")
        composite_project = f"{deployment_id}-{organization}-{project}"

        with open(config_file, "w", encoding="utf-8") as f:
            # Write deployment metadata
            f.write(f'{composite_project}:deploymentId: "{deployment_id}"\n')
            f.write(f'{composite_project}:organization: "{organization}"\n')
            f.write(f'{composite_project}:pulumiOrg: "{manifest.get("pulumiOrg", "")}"\n')
            f.write(f'{composite_project}:project: "{project}"\n')
            f.write(f'{composite_project}:domain: "{manifest.get("domain", "")}"\n')

            # Write environment config
            f.write(f'{composite_project}:environment: "{environment}"\n')
            f.write(f'{composite_project}:region: "{env_config.get("region", "")}"\n')
            f.write(f'{composite_project}:accountId: "{env_config.get("account_id", "")}"\n')

            # Write stack metadata
            f.write(f'{composite_project}:stackName: "{stack_name}"\n')
            f.write(f'{composite_project}:layer: "{stack_config.get("layer", 1)}"\n')

            # Write dependencies as JSON array string
            deps = stack_config.get("dependencies", [])
            if deps:
                import json
                f.write(f'{composite_project}:dependencies: \'{json.dumps(deps)}\'\n')

            # Write stack-specific configuration
            stack_specific_config = stack_config.get("config", {})
            for key, value in stack_specific_config.items():
                # Format value appropriately
                if isinstance(value, str):
                    f.write(f'{composite_project}:{key}: "{value}"\n')
                elif isinstance(value, (list, dict)):
                    import json
                    f.write(f'{composite_project}:{key}: \'{json.dumps(value)}\'\n')
                else:
                    f.write(f'{composite_project}:{key}: "{value}"\n')

            # Write AWS region for Pulumi AWS provider
            f.write(f'aws:region: "{env_config.get("region", "us-east-1")}"\n')

        logger.debug(f"Generated config for {stack_name}-{environment}: {config_file}")
        return config_file

    def load_stack_config(
        self, stack_name: str, environment: str = "dev"
    ) -> Dict[str, Any]:
        """
        Load stack configuration file (Pulumi format)

        Args:
            stack_name: Name of the stack
            environment: Environment

        Returns:
            Configuration dictionary (converted from Pulumi format)

        Raises:
            FileNotFoundError: If config file not found
        """
        config_file = self.config_dir / f"{stack_name}.{environment}.yaml"

        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {config_file}")

        with open(config_file, "r", encoding="utf-8") as f:
            pulumi_config = yaml.safe_load(f)

        # Convert Pulumi format back to nested dictionary
        config = {
            "deployment_id": "",
            "organization": "",
            "project": "",
            "domain": "",
            "environment": environment,
            "region": "",
            "account_id": "",
            "stack_name": stack_name,
            "dependencies": [],
            "layer": 1,
            "config": {}
        }

        if pulumi_config:
            for key, value in pulumi_config.items():
                if ":" in key:
                    prefix, suffix = key.split(":", 1)

                    if prefix == stack_name:
                        # Handle known fields
                        if suffix == "deploymentId":
                            config["deployment_id"] = value
                        elif suffix == "organization":
                            config["organization"] = value
                        elif suffix == "project":
                            config["project"] = value
                        elif suffix == "domain":
                            config["domain"] = value
                        elif suffix == "environment":
                            config["environment"] = value
                        elif suffix == "region":
                            config["region"] = value
                        elif suffix == "accountId":
                            config["account_id"] = value
                        elif suffix == "stackName":
                            config["stack_name"] = value
                        elif suffix == "layer":
                            config["layer"] = int(value) if isinstance(value, str) else value
                        elif suffix == "dependencies":
                            import json
                            config["dependencies"] = json.loads(value) if isinstance(value, str) else value
                        else:
                            # Stack-specific config
                            try:
                                import json
                                config["config"][suffix] = json.loads(value) if isinstance(value, str) and (value.startswith('[') or value.startswith('{')) else value
                            except:
                                config["config"][suffix] = value
                    elif prefix == "aws" and suffix == "region":
                        if not config["region"]:
                            config["region"] = value

        return config

    def update_stack_config(
        self,
        stack_name: str,
        updates: Dict[str, Any],
        environment: str = "dev",
    ) -> None:
        """
        Update stack configuration file

        Args:
            stack_name: Name of the stack
            updates: Configuration updates to apply
            environment: Environment
        """
        # Load existing config
        try:
            config = self.load_stack_config(stack_name, environment)
        except FileNotFoundError:
            # Create minimal config if it doesn't exist
            config = {
                "deployment_id": "",
                "organization": "",
                "project": "",
                "domain": "",
                "environment": environment,
                "region": "",
                "account_id": "",
                "stack_name": stack_name,
                "dependencies": [],
                "layer": 1,
                "config": {}
            }

        # Apply updates
        config.update(updates)

        # Save updated config in Pulumi format
        config_file = self.config_dir / f"{stack_name}.{environment}.yaml"

        with open(config_file, "w", encoding="utf-8") as f:
            import json

            # Write in Pulumi format
            f.write(f'{composite_project}:deploymentId: "{config.get("deployment_id", "")}"\n')
            f.write(f'{composite_project}:organization: "{config.get("organization", "")}"\n')
            f.write(f'{composite_project}:project: "{config.get("project", "")}"\n')
            f.write(f'{composite_project}:domain: "{config.get("domain", "")}"\n')
            f.write(f'{composite_project}:environment: "{config.get("environment", "")}"\n')
            f.write(f'{composite_project}:region: "{config.get("region", "")}"\n')
            f.write(f'{composite_project}:accountId: "{config.get("account_id", "")}"\n')
            f.write(f'{composite_project}:stackName: "{stack_name}"\n')
            f.write(f'{composite_project}:layer: "{config.get("layer", 1)}"\n')

            deps = config.get("dependencies", [])
            if deps:
                f.write(f'{composite_project}:dependencies: \'{json.dumps(deps)}\'\n')

            stack_specific_config = config.get("config", {})
            for key, value in stack_specific_config.items():
                if isinstance(value, str):
                    f.write(f'{composite_project}:{key}: "{value}"\n')
                elif isinstance(value, (list, dict)):
                    f.write(f'{composite_project}:{key}: \'{json.dumps(value)}\'\n')
                else:
                    f.write(f'{composite_project}:{key}: "{value}"\n')

            f.write(f'aws:region: "{config.get("region", "us-east-1")}"\n')

        logger.info(f"Updated config for {stack_name}-{environment}")

    def delete_stack_config(
        self, stack_name: str, environment: str = "dev"
    ) -> bool:
        """
        Delete stack configuration file

        Args:
            stack_name: Name of the stack
            environment: Environment

        Returns:
            True if deleted, False if not found
        """
        config_file = self.config_dir / f"{stack_name}.{environment}.yaml"

        if config_file.exists():
            config_file.unlink()
            logger.info(f"Deleted config for {stack_name}-{environment}")
            return True

        return False

    def list_config_files(self, environment: Optional[str] = None) -> List[Path]:
        """
        List all configuration files

        Args:
            environment: Optional environment filter

        Returns:
            List of configuration file paths
        """
        if environment:
            pattern = f"*.{environment}.yaml"
        else:
            pattern = "*.yaml"

        config_files = []

        for file in self.config_dir.glob(pattern):
            # Skip manifest and metadata files
            if file.name.startswith(".") or file.name.startswith("deployment-"):
                continue

            config_files.append(file)

        return sorted(config_files)

    def _load_manifest(self) -> Dict[str, Any]:
        """
        Load deployment manifest

        Returns:
            Manifest dictionary
        """
        if not self.manifest_path.exists():
            raise FileNotFoundError(f"Manifest not found: {self.manifest_path}")

        with open(self.manifest_path, "r", encoding="utf-8") as f:
            manifest = yaml.safe_load(f)

        return manifest

    def generate_pulumi_config_values(
        self, stack_name: str, environment: str = "dev"
    ) -> Dict[str, str]:
        """
        Generate Pulumi config values for a stack

        Args:
            stack_name: Name of the stack
            environment: Environment

        Returns:
            Dictionary of config key -> value for Pulumi
        """
        config = self.load_stack_config(stack_name, environment)

        # Build Pulumi config values
        pulumi_config = {
            "deploymentId": config.get("deployment_id", ""),
            "organization": config.get("organization", ""),
            "project": config.get("project", ""),
            "domain": config.get("domain", ""),
            "environment": environment,
            "stackName": stack_name,
            "aws:region": config.get("region", "us-east-1"),
        }

        # Add stack-specific config
        stack_config = config.get("config", {})
        for key, value in stack_config.items():
            pulumi_config[key] = str(value)

        return pulumi_config
