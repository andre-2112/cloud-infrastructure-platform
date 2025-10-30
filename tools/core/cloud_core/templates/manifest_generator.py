"""
Manifest Generator

Generates deployment manifests from templates with placeholder substitution.
"""

from pathlib import Path
from typing import Dict, Any, Optional
import yaml
from datetime import datetime

from .template_manager import TemplateManager
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ManifestGenerator:
    """Generates deployment manifests from templates"""

    def __init__(self, template_manager: Optional[TemplateManager] = None):
        """
        Initialize manifest generator

        Args:
            template_manager: Template manager instance (creates new if not provided)
        """
        self.template_manager = template_manager or TemplateManager()

    def generate_manifest(
        self,
        template_name: str,
        deployment_id: str,
        organization: str,
        project: str,
        domain: str,
        region: str = "us-east-1",
        accounts: Optional[Dict[str, str]] = None,
        overrides: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate deployment manifest from template

        Args:
            template_name: Name of template to use
            deployment_id: Deployment ID
            organization: Organization name
            project: Project name
            domain: Primary domain
            region: Primary AWS region
            accounts: AWS account IDs by environment
                     E.g., {"dev": "123456789012", "stage": "234567890123"}
            overrides: Optional overrides for stack configurations

        Returns:
            Complete deployment manifest

        Raises:
            TemplateNotFoundError: If template not found
            TemplateValidationError: If template invalid
        """
        logger.info(f"Generating manifest for deployment {deployment_id} from template {template_name}")

        # Load template
        template_data = self.template_manager.load_template(template_name)

        # Start with template as base
        manifest = {
            "version": template_data.get("version", "4.1"),  # Use template version, default to 4.1
            "deployment_id": deployment_id,
            "organization": organization,
            "project": project,
            "domain": domain,
            "template": template_name,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "metadata": {
                "generated_from_template": template_name,
                "generator_version": "0.7.0",
            },
        }

        # Add environments
        manifest["environments"] = self._generate_environments(
            region, accounts or {}
        )

        # Add stacks from template
        template_stacks = template_data.get("stacks", {})
        manifest["stacks"] = {}

        for stack_name, stack_config in template_stacks.items():
            manifest["stacks"][stack_name] = self._process_stack_config(
                stack_config.copy()
            )

        # Apply overrides
        if overrides:
            manifest = self._apply_overrides(manifest, overrides)

        # Add any template metadata
        if "metadata" in template_data:
            manifest["metadata"].update(template_data.get("metadata", {}))

        logger.info(f"Generated manifest with {len(manifest['stacks'])} stacks")
        return manifest

    def _generate_environments(
        self, primary_region: str, accounts: Dict[str, str]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Generate environment configurations

        Args:
            primary_region: Primary AWS region
            accounts: Account IDs by environment

        Returns:
            Environment configurations
        """
        environments = {}

        # Define standard environments
        env_configs = {
            "dev": {"enabled": True},
            "stage": {"enabled": False},  # Disabled by default
            "prod": {"enabled": False},  # Disabled by default
        }

        for env_name, config in env_configs.items():
            account_id = accounts.get(env_name, accounts.get("dev", "000000000000"))

            environments[env_name] = {
                "enabled": config["enabled"],
                "region": primary_region,
                "account_id": account_id,
            }

        return environments

    def _process_stack_config(self, stack_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process stack configuration from template

        Args:
            stack_config: Stack configuration from template

        Returns:
            Processed stack configuration
        """
        # Ensure required fields
        if "enabled" not in stack_config:
            stack_config["enabled"] = True

        if "dependencies" not in stack_config:
            stack_config["dependencies"] = []

        # Don't set a default layer - it should be calculated by LayerCalculator
        # based on dependencies. Setting a default layer of 1 causes validation
        # errors when stacks have dependencies.

        if "config" not in stack_config:
            stack_config["config"] = {}

        return stack_config

    def _apply_overrides(
        self, manifest: Dict[str, Any], overrides: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply overrides to manifest

        Args:
            manifest: Base manifest
            overrides: Override values

        Returns:
            Manifest with overrides applied
        """
        # Deep merge overrides
        for key, value in overrides.items():
            if key == "stacks" and isinstance(value, dict):
                # Merge stack configurations
                for stack_name, stack_overrides in value.items():
                    if stack_name in manifest["stacks"]:
                        manifest["stacks"][stack_name].update(stack_overrides)
            elif key == "environments" and isinstance(value, dict):
                # Merge environment configurations
                for env_name, env_overrides in value.items():
                    if env_name in manifest["environments"]:
                        manifest["environments"][env_name].update(env_overrides)
            else:
                # Direct override
                manifest[key] = value

        return manifest

    def save_manifest(self, manifest: Dict[str, Any], output_path: Path) -> None:
        """
        Save manifest to file

        Args:
            manifest: Manifest data
            output_path: Path to save manifest
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(manifest, f, default_flow_style=False, sort_keys=False)

        logger.info(f"Saved manifest to {output_path}")

    def validate_manifest(self, manifest: Dict[str, Any]) -> bool:
        """
        Validate generated manifest

        Args:
            manifest: Manifest to validate

        Returns:
            True if valid, False otherwise
        """
        # Calculate layers first if not present
        from ..orchestrator.layer_calculator import LayerCalculator

        # Check if layers need to be calculated
        stacks = manifest.get("stacks", {})
        needs_layers = any("layer" not in stack for stack in stacks.values())

        if needs_layers:
            # Calculate layers
            layer_calc = LayerCalculator()
            try:
                # Build dependency graph for LayerCalculator
                dep_graph = {}
                for stack_name, stack_config in stacks.items():
                    dep_graph[stack_name] = stack_config.get("dependencies", [])

                # Calculate layers (returns list of lists)
                layers_list = layer_calc.calculate_layers(dep_graph)

                # Add layer numbers to manifest
                for stack_name in stacks.keys():
                    layer_num = layer_calc.get_layer_for_stack(stack_name)
                    if layer_num > 0 and stack_name in manifest["stacks"]:
                        manifest["stacks"][stack_name]["layer"] = layer_num
            except Exception as e:
                logger.error(f"Failed to calculate layers: {e}")
                return False

        # Use manifest validator
        from ..validation.manifest_validator import ManifestValidator

        # Save to temp file for validation
        import tempfile

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as tf:
            yaml.safe_dump(manifest, tf)
            temp_path = Path(tf.name)

        try:
            validator = ManifestValidator()
            is_valid = validator.validate_file(temp_path)

            if not is_valid:
                logger.error("Manifest validation failed:")
                for error in validator.get_errors():
                    logger.error(f"  - {error}")

            return is_valid
        finally:
            temp_path.unlink()
