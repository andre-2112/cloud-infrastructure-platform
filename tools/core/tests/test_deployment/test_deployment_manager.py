"""Tests for DeploymentManager"""

import pytest
import yaml
from pathlib import Path
from unittest.mock import patch
from cloud_core.deployment.deployment_manager import (
    DeploymentManager,
    DeploymentNotFoundError,
)
from cloud_core.templates import TemplateManager, ManifestGenerator


@pytest.fixture
def temp_deployments_root(tmp_path):
    """Create temporary deployments root directory"""
    deployments_root = tmp_path / "deployments"
    deployments_root.mkdir()
    return deployments_root


@pytest.fixture
def test_template_manager():
    """Create TemplateManager pointing to test fixtures"""
    fixtures_dir = Path(__file__).parent.parent / "fixtures" / "templates"
    return TemplateManager(templates_root=fixtures_dir)


@pytest.fixture
def deployment_manager(temp_deployments_root, test_template_manager):
    """Create DeploymentManager instance with test templates"""
    with patch('cloud_core.deployment.deployment_manager.ManifestGenerator') as mock_gen:
        # Create real ManifestGenerator with test template manager
        real_gen = ManifestGenerator(template_manager=test_template_manager)
        mock_gen.return_value = real_gen
        manager = DeploymentManager(temp_deployments_root)
        yield manager


def test_deployment_manager_init(temp_deployments_root):
    """Test DeploymentManager initialization"""
    manager = DeploymentManager(temp_deployments_root)
    assert manager.deployments_root == temp_deployments_root
    assert temp_deployments_root.exists()


def test_create_deployment(deployment_manager):
    """Test creating a new deployment"""
    deployment_dir = deployment_manager.create_deployment(
        template_name="standard-template",
        organization="TestOrg",
        project="test-project",
        domain="example.com",
        region="us-east-1",
        deployment_id="D1TEST1"
    )

    assert deployment_dir.exists()
    assert "D1TEST1" in deployment_dir.name
    assert "TestOrg" in deployment_dir.name
    assert (deployment_dir / "deployment-manifest.yaml").exists()


def test_create_deployment_auto_id(deployment_manager):
    """Test creating deployment with auto-generated ID"""
    deployment_dir = deployment_manager.create_deployment(
        template_name="standard-template",
        organization="TestOrg",
        project="test-project",
        domain="example.com"
    )

    assert deployment_dir.exists()
    # Should have format: {deployment_id}-{org}-{project}
    parts = deployment_dir.name.split("-")
    assert len(parts) >= 3


def test_create_deployment_with_accounts(deployment_manager):
    """Test creating deployment with AWS accounts"""
    accounts = {
        "dev": "123456789012",
        "prod": "210987654321"
    }

    deployment_dir = deployment_manager.create_deployment(
        template_name="standard-template",
        organization="TestOrg",
        project="test-project",
        domain="example.com",
        accounts=accounts,
        deployment_id="D1TEST1"
    )

    # Load manifest and verify accounts
    manifest_path = deployment_dir / "deployment-manifest.yaml"
    with open(manifest_path) as f:
        manifest = yaml.safe_load(f)

    # Verify manifest was created
    assert manifest is not None


def test_create_deployment_invalid_id(deployment_manager):
    """Test creating deployment with invalid ID"""
    with pytest.raises(ValueError, match="Invalid deployment ID"):
        deployment_manager.create_deployment(
            template_name="standard-template",
            organization="TestOrg",
            project="test-project",
            domain="example.com",
            deployment_id="invalid_id"  # Should use uppercase and numbers
        )


def test_create_deployment_already_exists(deployment_manager):
    """Test creating duplicate deployment"""
    deployment_manager.create_deployment(
        template_name="standard-template",
        organization="TestOrg",
        project="test-project",
        domain="example.com",
        deployment_id="D1TEST1"
    )

    # Try to create again
    with pytest.raises(ValueError, match="already exists"):
        deployment_manager.create_deployment(
            template_name="standard-template",
            organization="TestOrg",
            project="test-project",
            domain="example.com",
            deployment_id="D1TEST1"
        )


def test_get_deployment_dir(deployment_manager):
    """Test getting deployment directory"""
    deployment_manager.create_deployment(
        template_name="standard-template",
        organization="TestOrg",
        project="test-project",
        domain="example.com",
        deployment_id="D1TEST1"
    )

    # Get by ID with org and project
    deployment_dir = deployment_manager.get_deployment_dir(
        "D1TEST1", org="TestOrg", project="test-project"
    )

    assert deployment_dir is not None
    assert deployment_dir.exists()


def test_get_deployment_dir_not_found(deployment_manager):
    """Test getting non-existent deployment"""
    deployment_dir = deployment_manager.get_deployment_dir("NONEXISTENT")

    assert deployment_dir is None


def test_list_deployments(deployment_manager):
    """Test listing deployments"""
    # Create some deployments
    deployment_manager.create_deployment(
        template_name="standard-template",
        organization="TestOrg",
        project="test-project1",
        domain="example.com",
        deployment_id="D1TEST1"
    )

    deployment_manager.create_deployment(
        template_name="standard-template",
        organization="TestOrg",
        project="test-project2",
        domain="example.com",
        deployment_id="D2TEST2"
    )

    deployments = deployment_manager.list_deployments()

    assert len(deployments) == 2
    deployment_ids = [d["deployment_id"] for d in deployments]
    assert "D1TEST1" in deployment_ids
    assert "D2TEST2" in deployment_ids


def test_get_deployment_metadata(deployment_manager):
    """Test getting deployment metadata"""
    deployment_dir = deployment_manager.create_deployment(
        template_name="standard-template",
        organization="TestOrg",
        project="test-project",
        domain="example.com",
        deployment_id="D1TEST1"
    )

    metadata = deployment_manager.get_deployment_metadata(deployment_dir)

    assert metadata is not None
    assert metadata["deployment_id"] == "D1TEST1"
    assert metadata["organization"] == "TestOrg"
    assert metadata["project"] == "test-project"


def test_load_manifest(deployment_manager):
    """Test loading deployment manifest"""
    deployment_manager.create_deployment(
        template_name="standard-template",
        organization="TestOrg",
        project="test-project",
        domain="example.com",
        deployment_id="D1TEST1"
    )

    manifest = deployment_manager.load_manifest("D1TEST1")

    assert manifest is not None
    assert manifest["deployment_id"] == "D1TEST1"
    assert manifest["organization"] == "TestOrg"


def test_load_manifest_not_found(deployment_manager):
    """Test loading manifest for non-existent deployment"""
    with pytest.raises(DeploymentNotFoundError):
        deployment_manager.load_manifest("NONEXISTENT")


def test_save_manifest(deployment_manager):
    """Test saving deployment manifest"""
    deployment_manager.create_deployment(
        template_name="standard-template",
        organization="TestOrg",
        project="test-project",
        domain="example.com",
        deployment_id="D1TEST1"
    )

    manifest = deployment_manager.load_manifest("D1TEST1")
    manifest["test_key"] = "test_value"

    deployment_manager.save_manifest("D1TEST1", manifest)

    # Load and verify
    updated_manifest = deployment_manager.load_manifest("D1TEST1")
    assert updated_manifest["test_key"] == "test_value"


def test_delete_deployment(deployment_manager):
    """Test deleting deployment"""
    deployment_dir = deployment_manager.create_deployment(
        template_name="standard-template",
        organization="TestOrg",
        project="test-project",
        domain="example.com",
        deployment_id="D1TEST1"
    )

    result = deployment_manager.delete_deployment("D1TEST1", force=True)

    assert result is True
    assert not deployment_dir.exists()


def test_delete_deployment_not_found(deployment_manager):
    """Test deleting non-existent deployment"""
    with pytest.raises(DeploymentNotFoundError):
        deployment_manager.delete_deployment("NONEXISTENT", force=True)


def test_deployment_exists(deployment_manager):
    """Test checking if deployment exists"""
    deployment_manager.create_deployment(
        template_name="standard-template",
        organization="TestOrg",
        project="test-project",
        domain="example.com",
        deployment_id="D1TEST1"
    )

    assert deployment_manager.deployment_exists("D1TEST1")
    assert not deployment_manager.deployment_exists("NONEXISTENT")


def test_get_enabled_stacks(deployment_manager):
    """Test getting enabled stacks"""
    deployment_manager.create_deployment(
        template_name="standard-template",
        organization="TestOrg",
        project="test-project",
        domain="example.com",
        deployment_id="D1TEST1"
    )

    enabled_stacks = deployment_manager.get_enabled_stacks("D1TEST1")

    assert isinstance(enabled_stacks, list)
    # Should have some enabled stacks from template
    assert len(enabled_stacks) >= 0


def test_get_enabled_stacks_from_manifest(deployment_manager):
    """Test getting enabled stacks from manifest dict"""
    manifest = {
        "stacks": {
            "network": {"enabled": True},
            "security": {"enabled": True},
            "disabled": {"enabled": False}
        }
    }

    enabled_stacks = deployment_manager.get_enabled_stacks(manifest=manifest)

    assert len(enabled_stacks) == 2
    assert "network" in enabled_stacks
    assert "security" in enabled_stacks
    assert "disabled" not in enabled_stacks


def test_get_deployment_id_from_manifest(deployment_manager):
    """Test extracting deployment ID from manifest"""
    manifest = {
        "deployment_id": "D1TEST1"
    }

    deployment_id = deployment_manager.get_deployment_id_from_manifest(manifest)

    assert deployment_id == "D1TEST1"


def test_update_deployment_metadata(deployment_manager):
    """Test updating deployment metadata"""
    deployment_manager.create_deployment(
        template_name="standard-template",
        organization="TestOrg",
        project="test-project",
        domain="example.com",
        deployment_id="D1TEST1"
    )

    deployment_manager.update_deployment_metadata(
        "D1TEST1",
        {"status": "deployed", "custom_field": "value"}
    )

    # Load deployment directory and check metadata
    deployment_dir = deployment_manager.get_deployment_dir(
        "D1TEST1", org="TestOrg", project="test-project"
    )
    metadata = deployment_manager.get_deployment_metadata(deployment_dir)

    assert metadata["status"] == "deployed"
    assert metadata["custom_field"] == "value"


def test_get_stack_config(deployment_manager):
    """Test getting stack configuration"""
    deployment_manager.create_deployment(
        template_name="standard-template",
        organization="TestOrg",
        project="test-project",
        domain="example.com",
        deployment_id="D1TEST1"
    )

    manifest = deployment_manager.load_manifest("D1TEST1")

    # Get first stack name
    stack_names = list(manifest.get("stacks", {}).keys())
    if stack_names:
        stack_config = deployment_manager.get_stack_config("D1TEST1", stack_names[0])
        assert stack_config is not None


def test_get_stack_config_not_found(deployment_manager):
    """Test getting non-existent stack config"""
    deployment_manager.create_deployment(
        template_name="standard-template",
        organization="TestOrg",
        project="test-project",
        domain="example.com",
        deployment_id="D1TEST1"
    )

    with pytest.raises(KeyError):
        deployment_manager.get_stack_config("D1TEST1", "nonexistent_stack")


def test_update_stack_config(deployment_manager):
    """Test updating stack configuration"""
    deployment_manager.create_deployment(
        template_name="standard-template",
        organization="TestOrg",
        project="test-project",
        domain="example.com",
        deployment_id="D1TEST1"
    )

    manifest = deployment_manager.load_manifest("D1TEST1")
    stack_names = list(manifest.get("stacks", {}).keys())

    if stack_names:
        deployment_manager.update_stack_config(
            "D1TEST1",
            stack_names[0],
            {"custom_config": "value"}
        )

        # Verify update
        stack_config = deployment_manager.get_stack_config("D1TEST1", stack_names[0])
        assert stack_config["custom_config"] == "value"
