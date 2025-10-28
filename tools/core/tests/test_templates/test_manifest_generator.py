"""Tests for ManifestGenerator"""

import pytest
import yaml
from pathlib import Path
from cloud_core.templates.manifest_generator import ManifestGenerator
from cloud_core.templates.template_manager import TemplateManager


@pytest.fixture
def test_template_manager():
    """Create TemplateManager pointing to test fixtures"""
    fixtures_dir = Path(__file__).parent.parent / "fixtures" / "templates"
    return TemplateManager(templates_root=fixtures_dir)


@pytest.fixture
def manifest_generator(test_template_manager):
    """Create ManifestGenerator instance with test templates"""
    return ManifestGenerator(template_manager=test_template_manager)


def test_manifest_generator_init():
    """Test ManifestGenerator initialization"""
    generator = ManifestGenerator()
    assert generator.template_manager is not None
    assert isinstance(generator.template_manager, TemplateManager)


def test_manifest_generator_with_custom_manager(test_template_manager):
    """Test ManifestGenerator with custom template manager"""
    generator = ManifestGenerator(template_manager=test_template_manager)
    assert generator.template_manager is test_template_manager


def test_generate_manifest(manifest_generator):
    """Test generating manifest from template"""
    manifest = manifest_generator.generate_manifest(
        template_name="standard-template",
        deployment_id="D1TEST1",
        organization="TestOrg",
        project="test-project",
        domain="example.com",
        region="us-east-1"
    )

    assert manifest is not None
    assert manifest["deployment_id"] == "D1TEST1"
    assert manifest["organization"] == "TestOrg"
    assert manifest["project"] == "test-project"
    assert manifest["domain"] == "example.com"
    assert manifest["version"] == "3.1"
    assert "stacks" in manifest
    assert "environments" in manifest


def test_generate_manifest_with_accounts(manifest_generator):
    """Test generating manifest with AWS accounts"""
    accounts = {
        "dev": "123456789012",
        "stage": "234567890123",
        "prod": "345678901234"
    }

    manifest = manifest_generator.generate_manifest(
        template_name="standard-template",
        deployment_id="D1TEST1",
        organization="TestOrg",
        project="test-project",
        domain="example.com",
        accounts=accounts
    )

    assert manifest["environments"]["dev"]["account_id"] == "123456789012"
    assert manifest["environments"]["stage"]["account_id"] == "234567890123"
    assert manifest["environments"]["prod"]["account_id"] == "345678901234"


def test_generate_manifest_with_overrides(manifest_generator):
    """Test generating manifest with overrides"""
    overrides = {
        "domain": "override.com",
        "stacks": {
            "network": {
                "enabled": False
            }
        }
    }

    manifest = manifest_generator.generate_manifest(
        template_name="standard-template",
        deployment_id="D1TEST1",
        organization="TestOrg",
        project="test-project",
        domain="example.com",
        overrides=overrides
    )

    assert manifest["domain"] == "override.com"
    # Check if network stack exists and apply override
    if "network" in manifest["stacks"]:
        assert manifest["stacks"]["network"]["enabled"] is False


def test_generate_environments(manifest_generator):
    """Test generating environment configurations"""
    accounts = {
        "dev": "123456789012",
        "prod": "345678901234"
    }

    environments = manifest_generator._generate_environments("us-east-1", accounts)

    assert "dev" in environments
    assert "stage" in environments
    assert "prod" in environments
    assert environments["dev"]["enabled"] is True
    assert environments["stage"]["enabled"] is False  # Disabled by default
    assert environments["prod"]["enabled"] is False  # Disabled by default
    assert environments["dev"]["region"] == "us-east-1"
    assert environments["dev"]["account_id"] == "123456789012"


def test_generate_environments_default_account(manifest_generator):
    """Test generating environments with default account fallback"""
    accounts = {
        "dev": "123456789012"
    }

    environments = manifest_generator._generate_environments("us-west-2", accounts)

    # Stage and prod should fall back to dev account
    assert environments["stage"]["account_id"] == "123456789012"
    assert environments["prod"]["account_id"] == "123456789012"


def test_process_stack_config(manifest_generator):
    """Test processing stack configuration"""
    stack_config = {
        "name": "network",
        "custom_field": "value"
    }

    processed = manifest_generator._process_stack_config(stack_config)

    # Should add default fields
    assert processed["enabled"] is True
    assert processed["dependencies"] == []
    # Layer should NOT be set by _process_stack_config (it's calculated by LayerCalculator)
    assert "layer" not in processed or processed.get("layer") is None
    assert processed["config"] == {}
    # Should preserve existing fields
    assert processed["custom_field"] == "value"


def test_process_stack_config_with_existing_fields(manifest_generator):
    """Test processing stack config that already has fields"""
    stack_config = {
        "enabled": False,
        "dependencies": ["network"],
        "layer": 2,
        "config": {"key": "value"}
    }

    processed = manifest_generator._process_stack_config(stack_config)

    # Should preserve existing values
    assert processed["enabled"] is False
    assert processed["dependencies"] == ["network"]
    assert processed["layer"] == 2
    assert processed["config"] == {"key": "value"}


def test_apply_overrides_simple(manifest_generator):
    """Test applying simple overrides"""
    manifest = {
        "domain": "example.com",
        "project": "test"
    }

    overrides = {
        "domain": "override.com"
    }

    result = manifest_generator._apply_overrides(manifest, overrides)

    assert result["domain"] == "override.com"
    assert result["project"] == "test"


def test_apply_overrides_stacks(manifest_generator):
    """Test applying stack overrides"""
    manifest = {
        "stacks": {
            "network": {
                "enabled": True,
                "config": {"vpcCidr": "10.0.0.0/16"}
            },
            "security": {
                "enabled": True
            }
        }
    }

    overrides = {
        "stacks": {
            "network": {
                "enabled": False,
                "config": {"vpcCidr": "172.16.0.0/16"}
            }
        }
    }

    result = manifest_generator._apply_overrides(manifest, overrides)

    assert result["stacks"]["network"]["enabled"] is False
    assert result["stacks"]["network"]["config"]["vpcCidr"] == "172.16.0.0/16"
    assert result["stacks"]["security"]["enabled"] is True


def test_apply_overrides_environments(manifest_generator):
    """Test applying environment overrides"""
    manifest = {
        "environments": {
            "dev": {
                "enabled": True,
                "region": "us-east-1"
            }
        }
    }

    overrides = {
        "environments": {
            "dev": {
                "enabled": False,
                "region": "us-west-2"
            }
        }
    }

    result = manifest_generator._apply_overrides(manifest, overrides)

    assert result["environments"]["dev"]["enabled"] is False
    assert result["environments"]["dev"]["region"] == "us-west-2"


def test_save_manifest(manifest_generator, tmp_path):
    """Test saving manifest to file"""
    manifest = {
        "version": "3.1",
        "deployment_id": "D1TEST1"
    }

    output_path = tmp_path / "deployment" / "manifest.yaml"

    manifest_generator.save_manifest(manifest, output_path)

    assert output_path.exists()

    # Load and verify
    with open(output_path) as f:
        loaded = yaml.safe_load(f)

    assert loaded["version"] == "3.1"
    assert loaded["deployment_id"] == "D1TEST1"


def test_validate_manifest(manifest_generator):
    """Test validating manifest"""
    # Generate a valid manifest
    manifest = manifest_generator.generate_manifest(
        template_name="standard-template",
        deployment_id="D1TEST1",
        organization="TestOrg",
        project="test-project",
        domain="example.com"
    )

    # Validate it
    is_valid = manifest_generator.validate_manifest(manifest)

    # Should be valid
    assert is_valid is True


def test_manifest_has_metadata(manifest_generator):
    """Test that generated manifest has metadata"""
    manifest = manifest_generator.generate_manifest(
        template_name="standard-template",
        deployment_id="D1TEST1",
        organization="TestOrg",
        project="test-project",
        domain="example.com"
    )

    assert "metadata" in manifest
    assert "generated_from_template" in manifest["metadata"]
    assert manifest["metadata"]["generated_from_template"] == "standard-template"
    assert "generator_version" in manifest["metadata"]


def test_manifest_has_timestamp(manifest_generator):
    """Test that generated manifest has creation timestamp"""
    manifest = manifest_generator.generate_manifest(
        template_name="standard-template",
        deployment_id="D1TEST1",
        organization="TestOrg",
        project="test-project",
        domain="example.com"
    )

    assert "created_at" in manifest
    assert isinstance(manifest["created_at"], str)
    assert "Z" in manifest["created_at"]  # UTC timestamp


def test_generate_with_custom_region(manifest_generator):
    """Test generating manifest with custom region"""
    manifest = manifest_generator.generate_manifest(
        template_name="standard-template",
        deployment_id="D1TEST1",
        organization="TestOrg",
        project="test-project",
        domain="example.com",
        region="eu-west-1"
    )

    assert manifest["environments"]["dev"]["region"] == "eu-west-1"


def test_apply_overrides_nonexistent_stack(manifest_generator):
    """Test applying overrides to non-existent stack"""
    manifest = {
        "stacks": {
            "network": {"enabled": True}
        }
    }

    overrides = {
        "stacks": {
            "nonexistent": {"enabled": False}
        }
    }

    result = manifest_generator._apply_overrides(manifest, overrides)

    # Should not crash, just skip non-existent stack
    assert "network" in result["stacks"]
