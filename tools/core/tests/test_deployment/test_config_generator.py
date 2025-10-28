"""Tests for ConfigGenerator"""

import pytest
import tempfile
import yaml
from pathlib import Path
from cloud_core.deployment.config_generator import ConfigGenerator


@pytest.fixture
def temp_deployment_dir(tmp_path):
    """Create temporary deployment directory"""
    deployment_dir = tmp_path / "deployment-test"
    deployment_dir.mkdir()

    # Create manifest
    manifest = {
        "deployment": {
            "id": "D1TEST1",
            "org": "TestOrg",
            "project": "test-project",
        },
        "stacks": {
            "network": {
                "enabled": True,
                "config": {
                    "vpcCidr": "10.0.0.0/16",
                },
            }
        },
    }

    manifest_file = deployment_dir / "deployment-manifest.yaml"
    with open(manifest_file, 'w') as f:
        yaml.dump(manifest, f)

    return deployment_dir


def test_config_generator_init(temp_deployment_dir):
    """Test ConfigGenerator initialization"""
    generator = ConfigGenerator(temp_deployment_dir)
    assert generator.deployment_dir == temp_deployment_dir
    assert generator.config_dir == temp_deployment_dir / "config"
    assert generator.config_dir.exists()


def test_generate_stack_config(temp_deployment_dir):
    """Test generating stack configuration"""
    generator = ConfigGenerator(temp_deployment_dir)

    manifest = {
        "deployment_id": "D1TEST1",
        "organization": "TestOrg",
        "project": "test-project",
        "domain": "example.com",
        "environments": {
            "dev": {
                "region": "us-east-1",
                "account_id": "123456789012"
            }
        },
        "stacks": {
            "network": {
                "config": {"vpcCidr": "10.0.0.0/16"},
                "layer": 1
            }
        }
    }

    config_path = generator.generate_stack_config(
        manifest=manifest,
        stack_name="network",
        environment="dev"
    )

    # generate_stack_config returns a Path to the generated config file
    assert config_path is not None
    assert config_path.exists()
    assert config_path.is_file()
    # Check it's in config subdirectory
    assert config_path.parent.name == "config"

    # Verify Pulumi format
    with open(config_path, 'r') as f:
        content = f.read()
        assert 'network:vpcCidr: "10.0.0.0/16"' in content
        assert 'aws:region: "us-east-1"' in content


def test_generate_all_configs(temp_deployment_dir):
    """Test generating all stack configs"""
    generator = ConfigGenerator(temp_deployment_dir)

    manifest = {
        "deployment_id": "D1TEST1",
        "organization": "TestOrg",
        "project": "test-project",
        "domain": "example.com",
        "environments": {
            "dev": {
                "region": "us-east-1",
                "account_id": "123456789012"
            }
        },
        "stacks": {
            "network": {
                "enabled": True,
                "config": {"vpcCidr": "10.0.0.0/16"}
            },
            "security": {
                "enabled": True,
                "config": {}
            }
        }
    }

    result = generator.generate_all_configs(manifest)

    assert len(result) == 2
    assert "network" in result
    assert "security" in result


def test_load_stack_config(temp_deployment_dir):
    """Test loading stack config"""
    generator = ConfigGenerator(temp_deployment_dir)

    manifest = {
        "deployment_id": "D1TEST1",
        "organization": "TestOrg",
        "project": "test-project",
        "domain": "example.com",
        "environments": {
            "dev": {
                "region": "us-east-1",
                "account_id": "123456789012"
            }
        },
        "stacks": {
            "network": {
                "enabled": True,
                "config": {"vpcCidr": "10.0.0.0/16"},
                "dependencies": [],
                "layer": 1
            }
        }
    }

    # Generate config first
    generator.generate_stack_config("network", manifest, "dev")

    # Load it back
    config = generator.load_stack_config("network", "dev")

    assert config["deployment_id"] == "D1TEST1"
    assert config["stack_name"] == "network"
    assert config["environment"] == "dev"


def test_update_stack_config(temp_deployment_dir):
    """Test updating stack config"""
    generator = ConfigGenerator(temp_deployment_dir)

    manifest = {
        "deployment_id": "D1TEST1",
        "organization": "TestOrg",
        "project": "test-project",
        "domain": "example.com",
        "environments": {
            "dev": {
                "region": "us-east-1",
                "account_id": "123456789012"
            }
        },
        "stacks": {
            "network": {
                "config": {"vpcCidr": "10.0.0.0/16"},
                "layer": 1
            }
        }
    }

    # Generate initial config
    generator.generate_stack_config("network", manifest, "dev")

    # Update it with new config values
    generator.update_stack_config(
        "network",
        {
            "config": {
                "vpcCidr": "10.0.0.0/16",
                "newParameter": "new_value"
            }
        },
        "dev"
    )

    # Load and verify
    config = generator.load_stack_config("network", "dev")
    assert config["config"]["newParameter"] == "new_value"
    assert config["config"]["vpcCidr"] == "10.0.0.0/16"


def test_delete_stack_config(temp_deployment_dir):
    """Test deleting stack config"""
    generator = ConfigGenerator(temp_deployment_dir)

    manifest = {
        "deployment_id": "D1TEST1",
        "organization": "TestOrg",
        "project": "test-project",
        "domain": "example.com",
        "environments": {
            "dev": {
                "region": "us-east-1",
                "account_id": "123456789012"
            }
        },
        "stacks": {
            "network": {
                "config": {"vpcCidr": "10.0.0.0/16"},
                "layer": 1
            }
        }
    }

    # Generate config
    generator.generate_stack_config("network", manifest, "dev")
    config_file = generator.config_dir / "network.dev.yaml"

    # Delete it
    result = generator.delete_stack_config("network", "dev")

    assert result is True
    assert not config_file.exists()


def test_delete_nonexistent_config(temp_deployment_dir):
    """Test deleting non-existent config"""
    generator = ConfigGenerator(temp_deployment_dir)

    result = generator.delete_stack_config("nonexistent", "dev")

    assert result is False


def test_list_config_files(temp_deployment_dir):
    """Test listing config files"""
    generator = ConfigGenerator(temp_deployment_dir)

    # Create some config files in config directory
    (generator.config_dir / "network.dev.yaml").touch()
    (generator.config_dir / "security.dev.yaml").touch()
    (generator.config_dir / "network.prod.yaml").touch()

    # List all
    all_configs = generator.list_config_files()
    assert len(all_configs) == 3

    # List dev only
    dev_configs = generator.list_config_files("dev")
    assert len(dev_configs) == 2


def test_generate_pulumi_config_values(temp_deployment_dir):
    """Test generating Pulumi config values"""
    generator = ConfigGenerator(temp_deployment_dir)

    manifest = {
        "deployment_id": "D1TEST1",
        "organization": "TestOrg",
        "project": "test-project",
        "domain": "example.com",
        "environments": {
            "dev": {
                "region": "us-east-1",
                "account_id": "123456789012"
            }
        },
        "stacks": {
            "network": {
                "config": {
                    "vpcCidr": "10.0.0.0/16",
                    "maxAzs": 3
                },
                "layer": 1
            }
        }
    }

    # Generate config file
    generator.generate_stack_config("network", manifest, "dev")

    # Generate Pulumi config
    pulumi_config = generator.generate_pulumi_config_values("network", "dev")

    assert pulumi_config["deploymentId"] == "D1TEST1"
    assert pulumi_config["organization"] == "TestOrg"
    assert pulumi_config["aws:region"] == "us-east-1"
    assert pulumi_config["vpcCidr"] == "10.0.0.0/16"


def test_load_manifest_not_found(temp_deployment_dir):
    """Test loading manifest when file doesn't exist"""
    # Create generator with empty dir
    empty_dir = temp_deployment_dir / "empty"
    empty_dir.mkdir()

    generator = ConfigGenerator(empty_dir)

    with pytest.raises(FileNotFoundError):
        generator._load_manifest()


def test_generate_stack_config_stack_not_found(temp_deployment_dir):
    """Test generating config for non-existent stack"""
    generator = ConfigGenerator(temp_deployment_dir)

    manifest = {
        "stacks": {}
    }

    with pytest.raises(ValueError, match="not found in manifest"):
        generator.generate_stack_config("nonexistent", manifest)


def test_generate_stack_config_env_not_found(temp_deployment_dir):
    """Test generating config with non-existent environment"""
    generator = ConfigGenerator(temp_deployment_dir)

    manifest = {
        "stacks": {
            "network": {"enabled": True}
        },
        "environments": {}
    }

    with pytest.raises(ValueError, match="Environment.*not found"):
        generator.generate_stack_config("network", manifest, "dev")
