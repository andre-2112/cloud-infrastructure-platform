"""
Deployment Manager

Manages deployment lifecycle: creation, configuration, deletion, and discovery.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
import yaml
from datetime import datetime

from ..templates import TemplateManager, ManifestGenerator
from ..utils.logger import get_logger
from ..utils.deployment_id import generate_deployment_id, validate_deployment_id

logger = get_logger(__name__)


class DeploymentNotFoundError(Exception):
    """Raised when deployment not found"""

    pass


class DeploymentManager:
    """Manages deployments"""

    def __init__(self, deployments_root: Optional[Path] = None):
        """
        Initialize deployment manager

        Args:
            deployments_root: Root directory for deployments
                             Defaults to cloud/deploy/
        """
        if deployments_root:
            self.deployments_root = Path(deployments_root)
        else:
            # Default: cloud/deploy/
            # Assuming CLI is at cloud/tools/cli/, go up to cloud root
            cli_root = Path(__file__).parent.parent.parent.parent.parent
            self.deployments_root = cli_root / "deploy"

        self.deployments_root.mkdir(parents=True, exist_ok=True)

        logger.debug(f"Deployment manager initialized with root: {self.deployments_root}")

    def create_deployment(
        self,
        template_name: str,
        organization: str,
        project: str,
        domain: str,
        region: str = "us-east-1",
        accounts: Optional[Dict[str, str]] = None,
        deployment_id: Optional[str] = None,
        overrides: Optional[Dict[str, Any]] = None,
    ) -> Path:
        """
        Create a new deployment from template

        Args:
            template_name: Name of template to use
            organization: Organization name
            project: Project name
            domain: Primary domain
            region: Primary AWS region
            accounts: AWS account IDs by environment
            deployment_id: Optional deployment ID (auto-generated if not provided)
            overrides: Optional manifest overrides

        Returns:
            Path to deployment directory

        Raises:
            ValueError: If deployment_id invalid or deployment exists
        """
        # Generate deployment ID if not provided
        if not deployment_id:
            deployment_id = generate_deployment_id()
        elif not validate_deployment_id(deployment_id):
            raise ValueError(f"Invalid deployment ID format: {deployment_id}")

        logger.info(
            f"Creating deployment {deployment_id} for {organization}/{project}"
        )

        # Create deployment directory
        # Format: {deployment_id}-{organization}-{project}/
        deployment_dir = self._get_deployment_dir(deployment_id, organization, project)

        if deployment_dir.exists():
            raise ValueError(
                f"Deployment {deployment_id} already exists at {deployment_dir}"
            )

        deployment_dir.mkdir(parents=True)

        # Generate manifest
        manifest_gen = ManifestGenerator()
        manifest = manifest_gen.generate_manifest(
            template_name=template_name,
            deployment_id=deployment_id,
            organization=organization,
            project=project,
            domain=domain,
            region=region,
            accounts=accounts or {},
            overrides=overrides,
        )

        # Save manifest at deployment root (per Architecture 3.1)
        manifest_path = deployment_dir / "deployment-manifest.yaml"
        manifest_gen.save_manifest(manifest, manifest_path)

        # Create deployment metadata
        metadata = {
            "deployment_id": deployment_id,
            "organization": organization,
            "project": project,
            "domain": domain,
            "template": template_name,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "status": "initialized",
        }

        metadata_path = deployment_dir / ".deployment-metadata.yaml"
        with open(metadata_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(metadata, f)

        logger.info(f"Deployment {deployment_id} created at {deployment_dir}")
        return deployment_dir

    def get_deployment_dir(
        self, deployment_id: str, org: Optional[str] = None, project: Optional[str] = None
    ) -> Optional[Path]:
        """
        Get deployment directory

        Args:
            deployment_id: Deployment ID
            org: Optional organization name (for direct path construction)
            project: Optional project name (for direct path construction)

        Returns:
            Path to deployment directory, or None if not found
        """
        # If org and project provided, construct path directly
        if org and project:
            deployment_dir = self._get_deployment_dir(deployment_id, org, project)
            return deployment_dir if deployment_dir.exists() else None

        # Otherwise, search for deployment
        return self._find_deployment_dir(deployment_id)

    def _get_deployment_dir(
        self, deployment_id: str, org: str, project: str
    ) -> Path:
        """
        Construct deployment directory path

        Args:
            deployment_id: Deployment ID
            org: Organization name
            project: Project name

        Returns:
            Path to deployment directory
        """
        dir_name = f"{deployment_id}-{org}-{project}"
        return self.deployments_root / dir_name

    def _find_deployment_dir(self, deployment_id: str) -> Optional[Path]:
        """
        Find deployment directory by ID

        Args:
            deployment_id: Deployment ID

        Returns:
            Path to deployment directory, or None if not found
        """
        # Search for directories starting with deployment ID
        pattern = f"{deployment_id}-*"
        matches = list(self.deployments_root.glob(pattern))

        if matches:
            return matches[0]  # Return first match

        return None

    def list_deployments(self) -> List[Dict[str, Any]]:
        """
        List all deployments

        Returns:
            List of deployment info dictionaries
        """
        deployments = []

        for deployment_dir in self.deployments_root.iterdir():
            if not deployment_dir.is_dir():
                continue

            # Skip hidden directories
            if deployment_dir.name.startswith("."):
                continue

            try:
                metadata = self.get_deployment_metadata(deployment_dir)
                if metadata:
                    deployments.append(metadata)
            except Exception as e:
                logger.warning(
                    f"Error reading deployment {deployment_dir.name}: {e}"
                )

        return sorted(deployments, key=lambda d: d.get("created_at", ""), reverse=True)

    def get_deployment_metadata(self, deployment_dir: Path) -> Optional[Dict[str, Any]]:
        """
        Get deployment metadata

        Args:
            deployment_dir: Path to deployment directory

        Returns:
            Metadata dictionary, or None if not found
        """
        metadata_path = deployment_dir / ".deployment-metadata.yaml"

        if not metadata_path.exists():
            # Try to extract from directory name
            return self._extract_metadata_from_dir_name(deployment_dir)

        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                metadata = yaml.safe_load(f)
            return metadata
        except Exception as e:
            logger.error(f"Error reading metadata from {metadata_path}: {e}")
            return None

    def _extract_metadata_from_dir_name(self, deployment_dir: Path) -> Dict[str, Any]:
        """
        Extract basic metadata from directory name

        Args:
            deployment_dir: Path to deployment directory

        Returns:
            Metadata dictionary
        """
        # Directory name format: {deployment_id}-{org}-{project}
        parts = deployment_dir.name.split("-", 2)

        if len(parts) >= 3:
            return {
                "deployment_id": parts[0],
                "organization": parts[1],
                "project": parts[2],
                "deployment_dir": str(deployment_dir),
                "status": "unknown",
            }

        return {
            "deployment_id": "unknown",
            "deployment_dir": str(deployment_dir),
            "status": "unknown",
        }

    def load_manifest(self, deployment_id: str) -> Dict[str, Any]:
        """
        Load deployment manifest

        Args:
            deployment_id: Deployment ID

        Returns:
            Manifest dictionary

        Raises:
            DeploymentNotFoundError: If deployment not found
        """
        deployment_dir = self._find_deployment_dir(deployment_id)

        if not deployment_dir:
            raise DeploymentNotFoundError(f"Deployment {deployment_id} not found")

        manifest_path = deployment_dir / "deployment-manifest.yaml"

        if not manifest_path.exists():
            raise FileNotFoundError(
                f"Manifest not found for deployment {deployment_id}"
            )

        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = yaml.safe_load(f)

        return manifest

    def save_manifest(
        self, deployment_id: str, manifest: Dict[str, Any]
    ) -> None:
        """
        Save deployment manifest

        Args:
            deployment_id: Deployment ID
            manifest: Manifest data

        Raises:
            DeploymentNotFoundError: If deployment not found
        """
        deployment_dir = self._find_deployment_dir(deployment_id)

        if not deployment_dir:
            raise DeploymentNotFoundError(f"Deployment {deployment_id} not found")

        manifest_path = deployment_dir / "deployment-manifest.yaml"

        with open(manifest_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(manifest, f, default_flow_style=False, sort_keys=False)

        logger.info(f"Saved manifest for deployment {deployment_id}")

    def delete_deployment(self, deployment_id: str, force: bool = False) -> bool:
        """
        Delete a deployment

        Args:
            deployment_id: Deployment ID
            force: Force deletion even if stacks are deployed

        Returns:
            True if deleted

        Raises:
            DeploymentNotFoundError: If deployment not found
            ValueError: If deployment has active stacks and force=False
        """
        deployment_dir = self._find_deployment_dir(deployment_id)

        if not deployment_dir:
            raise DeploymentNotFoundError(f"Deployment {deployment_id} not found")

        # TODO: Check if stacks are deployed (requires Pulumi state check)
        # For now, just delete if force=True or assume safe to delete

        if not force:
            logger.warning(
                f"Deleting deployment {deployment_id} - use force=True to skip checks"
            )

        import shutil

        shutil.rmtree(deployment_dir)

        logger.info(f"Deleted deployment {deployment_id}")
        return True

    def deployment_exists(self, deployment_id: str) -> bool:
        """
        Check if deployment exists

        Args:
            deployment_id: Deployment ID

        Returns:
            True if exists
        """
        return self._find_deployment_dir(deployment_id) is not None

    def get_enabled_stacks(self, deployment_id: str = None, manifest: Dict[str, Any] = None) -> List[str]:
        """
        Get list of enabled stacks
        
        Args:
            deployment_id: Optional deployment ID (if manifest not provided)
            manifest: Optional manifest dict (if deployment_id not provided)
            
        Returns:
            List of enabled stack names
        """
        if manifest is None:
            if deployment_id is None:
                raise ValueError("Must provide either deployment_id or manifest")
            manifest = self.load_manifest(deployment_id)
        
        enabled_stacks = []
        stacks = manifest.get("stacks", {})
        
        for stack_name, stack_config in stacks.items():
            if stack_config.get("enabled", True):
                enabled_stacks.append(stack_name)
        
        return enabled_stacks

    def get_deployment_id_from_manifest(self, manifest: Dict[str, Any]) -> str:
        """
        Extract deployment ID from manifest

        Args:
            manifest: Manifest dictionary

        Returns:
            Deployment ID

        Raises:
            KeyError: If deployment_id not found in manifest
        """
        return manifest["deployment_id"]

    def update_deployment_metadata(
        self, 
        deployment_id: str, 
        metadata: Dict[str, Any]
    ) -> None:
        """
        Update deployment metadata
        
        Args:
            deployment_id: Deployment ID
            metadata: Metadata to update
            
        Raises:
            DeploymentNotFoundError: If deployment not found
        """
        deployment_dir = self._find_deployment_dir(deployment_id)
        
        if not deployment_dir:
            raise DeploymentNotFoundError(f"Deployment {deployment_id} not found")
        
        metadata_path = deployment_dir / ".deployment-metadata.yaml"
        
        # Load existing metadata
        existing_metadata = {}
        if metadata_path.exists():
            with open(metadata_path, "r", encoding="utf-8") as f:
                existing_metadata = yaml.safe_load(f) or {}
        
        # Update with new metadata
        existing_metadata.update(metadata)
        
        # Add timestamp
        existing_metadata["updated_at"] = datetime.now().isoformat()
        
        # Save
        with open(metadata_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(existing_metadata, f, default_flow_style=False)
        
        logger.info(f"Updated metadata for deployment {deployment_id}")

    def get_stack_config(
        self, 
        deployment_id: str, 
        stack_name: str
    ) -> Dict[str, Any]:
        """
        Get configuration for a specific stack
        
        Args:
            deployment_id: Deployment ID
            stack_name: Stack name
            
        Returns:
            Stack configuration dict
            
        Raises:
            DeploymentNotFoundError: If deployment not found
            KeyError: If stack not found in manifest
        """
        manifest = self.load_manifest(deployment_id)
        stacks = manifest.get("stacks", {})
        
        if stack_name not in stacks:
            raise KeyError(f"Stack {stack_name} not found in deployment {deployment_id}")
        
        return stacks[stack_name]

    def update_stack_config(
        self,
        deployment_id: str,
        stack_name: str,
        config: Dict[str, Any]
    ) -> None:
        """
        Update configuration for a specific stack
        
        Args:
            deployment_id: Deployment ID
            stack_name: Stack name
            config: Configuration to update
            
        Raises:
            DeploymentNotFoundError: If deployment not found
            KeyError: If stack not found
        """
        manifest = self.load_manifest(deployment_id)
        stacks = manifest.get("stacks", {})
        
        if stack_name not in stacks:
            raise KeyError(f"Stack {stack_name} not found in deployment {deployment_id}")
        
        # Update stack config
        stacks[stack_name].update(config)
        
        # Save manifest
        self.save_manifest(deployment_id, manifest)
        
        logger.info(f"Updated config for stack {stack_name} in deployment {deployment_id}")
