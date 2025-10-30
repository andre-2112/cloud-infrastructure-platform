"""
Manifest Validator

Validates deployment manifest syntax and structure according to Architecture 4.1
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
import yaml
from pydantic import BaseModel, Field, ValidationError


class StackConfig(BaseModel):
    """Stack configuration in manifest"""

    enabled: bool = Field(default=True, description="Whether stack is enabled")
    layer: int = Field(..., ge=1, le=10, description="Execution layer (1-10)")
    dependencies: List[str] = Field(default_factory=list, description="Stack dependencies")
    config: Dict[str, Any] = Field(default_factory=dict, description="Stack-specific configuration")


class EnvironmentConfig(BaseModel):
    """Environment configuration"""

    enabled: bool = Field(default=True, description="Whether environment is enabled")
    region: str = Field(..., description="AWS region")
    account_id: str = Field(..., pattern=r"^\d{12}$", description="AWS account ID")


class DeploymentManifest(BaseModel):
    """Deployment manifest structure for v4.1"""

    version: str = Field(default="4.1", pattern=r"^4\.\d+$", description="Architecture version")
    deployment_id: str = Field(..., pattern=r"^D[A-Z0-9]{6}$", description="Deployment ID")
    organization: str = Field(..., min_length=1, description="Organization name")
    project: str = Field(..., min_length=1, description="Project name")
    domain: str = Field(..., description="Primary domain")
    template: str = Field(default="custom", description="Template name (optional)")

    environments: Dict[str, EnvironmentConfig] = Field(
        ..., description="Environment configurations"
    )

    stacks: Dict[str, StackConfig] = Field(..., description="Stack configurations")

    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ManifestValidator:
    """Validates deployment manifests"""

    def __init__(self) -> None:
        """Initialize validator"""
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.manifest: Optional[Dict[str, Any]] = None


    def validate(self, manifest_path: str) -> bool:
        """
        Validate a manifest file (convenience method)

        Args:
            manifest_path: Path to manifest YAML file (string)

        Returns:
            bool: True if valid, False otherwise
        """
        self.errors = []
        self.warnings = []
        self.manifest = None

        # Convert string to Path
        path = Path(manifest_path)

        # Check file exists
        if not path.exists():
            self.errors.append(f"Manifest file not found: {manifest_path}")
            return False

        # Load YAML
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            self.errors.append(f"YAML syntax error: {e}")
            return False
        except Exception as e:
            self.errors.append(f"Error reading manifest: {e}")
            return False

        # Store manifest
        self.manifest = data

        # Validate basic structure
        is_valid = self._validate_basic_structure(data)
        
        # If basic structure is valid, do additional checks
        if is_valid:
            self._validate_dependencies(data)

        return len(self.errors) == 0

    def _validate_basic_structure(self, data: Dict[str, Any]) -> bool:
        """Validate basic manifest structure (v4.1 flat format)"""
        # Check for required top-level keys (v4.1 flat format)
        required_fields = ["deployment_id", "organization", "project", "domain"]
        for field in required_fields:
            if field not in data:
                self.errors.append(f"Missing required field: {field}")

        # Check for environments
        if "environments" not in data:
            self.errors.append("Missing required field: environments")
            return False

        # Check for stacks
        if "stacks" not in data:
            self.errors.append("Missing required field: stacks")
            return False

        return len(self.errors) == 0

    def validate_file(self, manifest_path: Path) -> bool:
        """
        Validate a manifest file

        Args:
            manifest_path: Path to manifest YAML file

        Returns:
            bool: True if valid, False otherwise
        """
        self.errors = []
        self.warnings = []

        # Check file exists
        if not manifest_path.exists():
            self.errors.append(f"Manifest file not found: {manifest_path}")
            return False

        # Load YAML
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            self.errors.append(f"YAML syntax error: {e}")
            return False
        except Exception as e:
            self.errors.append(f"Error reading manifest: {e}")
            return False

        # Validate structure with Pydantic
        try:
            DeploymentManifest(**data)
        except ValidationError as e:
            for error in e.errors():
                field = ".".join(str(loc) for loc in error["loc"])
                self.errors.append(f"{field}: {error['msg']}")
            return False

        # Additional validation checks
        self._validate_dependencies(data)
        self._validate_layers(data)

        return len(self.errors) == 0

    def _validate_dependencies(self, data: Dict[str, Any]) -> None:
        """Validate stack dependencies"""
        stacks = data.get("stacks", {})
        stack_names = set(stacks.keys())

        for stack_name, stack_config in stacks.items():
            dependencies = stack_config.get("dependencies", [])
            for dep in dependencies:
                if dep not in stack_names:
                    self.errors.append(
                        f"Stack '{stack_name}' depends on unknown stack '{dep}'"
                    )

    def _validate_layers(self, data: Dict[str, Any]) -> None:
        """Validate layer assignments"""
        stacks = data.get("stacks", {})

        for stack_name, stack_config in stacks.items():
            layer = stack_config.get("layer")
            dependencies = stack_config.get("dependencies", [])

            # Dependencies must be in earlier layers
            for dep in dependencies:
                dep_layer = stacks[dep].get("layer")
                if dep_layer >= layer:
                    self.errors.append(
                        f"Stack '{stack_name}' (layer {layer}) depends on '{dep}' "
                        f"(layer {dep_layer}), but dependency must be in earlier layer"
                    )

    def get_errors(self) -> List[str]:
        """Get validation errors"""
        return self.errors

    def get_warnings(self) -> List[str]:
        """Get validation warnings"""
        return self.warnings
