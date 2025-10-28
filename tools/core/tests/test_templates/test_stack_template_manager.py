"""Tests for StackTemplateManager"""

import pytest
from pathlib import Path
import yaml
from cloud_core.templates.stack_template_manager import (
    StackTemplateManager,
    StackTemplateNotFoundError,
    StackTemplateValidationError
)


@pytest.fixture
def tmp_config_dir(tmp_path):
    """Create temporary config directory"""
    config_dir = tmp_path / "templates" / "config"
    config_dir.mkdir(parents=True)
    return config_dir


@pytest.fixture
def template_manager(tmp_config_dir):
    """Create StackTemplateManager with temporary directory"""
    return StackTemplateManager(config_root=tmp_config_dir)


@pytest.fixture
def sample_template():
    """Sample stack template data"""
    return {
        "name": "network",
        "description": "Network infrastructure",
        "dependencies": [],
        "priority": 100,
        "parameters": {
            "inputs": {
                "vpcCidr": {
                    "type": "string",
                    "required": True,
                    "description": "VPC CIDR block"
                },
                "region": {
                    "type": "string",
                    "required": False,
                    "default": "us-east-1"
                }
            },
            "outputs": {
                "vpcId": {
                    "type": "string",
                    "description": "VPC ID"
                }
            }
        }
    }


def test_stack_template_manager_init(tmp_config_dir):
    """Test StackTemplateManager initialization"""
    manager = StackTemplateManager(config_root=tmp_config_dir)
    assert manager.config_root == tmp_config_dir
    assert manager.config_root.exists()


def test_stack_template_manager_init_creates_directory(tmp_path):
    """Test that initialization creates config directory"""
    config_dir = tmp_path / "new_config"
    manager = StackTemplateManager(config_root=config_dir)
    assert config_dir.exists()


def test_list_templates_empty(template_manager):
    """Test listing templates when none exist"""
    templates = template_manager.list_templates()
    assert len(templates) == 0


def test_list_templates_with_templates(template_manager, tmp_config_dir, sample_template):
    """Test listing templates"""
    # Create template files
    for name in ["network", "security", "database"]:
        template_path = tmp_config_dir / f"{name}.yaml"
        with open(template_path, 'w') as f:
            yaml.dump(sample_template, f)

    templates = template_manager.list_templates()

    assert len(templates) == 3
    assert "network" in templates
    assert "security" in templates
    assert "database" in templates


def test_template_exists_true(template_manager, tmp_config_dir, sample_template):
    """Test template_exists when template exists"""
    # Create template
    template_path = tmp_config_dir / "network.yaml"
    with open(template_path, 'w') as f:
        yaml.dump(sample_template, f)

    assert template_manager.template_exists("network") is True


def test_template_exists_false(template_manager):
    """Test template_exists when template doesn't exist"""
    assert template_manager.template_exists("nonexistent") is False


def test_load_template_success(template_manager, tmp_config_dir, sample_template):
    """Test loading a template successfully"""
    # Create template
    template_path = tmp_config_dir / "network.yaml"
    with open(template_path, 'w') as f:
        yaml.dump(sample_template, f)

    loaded = template_manager.load_template("network")

    assert loaded["name"] == "network"
    assert "parameters" in loaded
    assert "inputs" in loaded["parameters"]
    assert "outputs" in loaded["parameters"]


def test_load_template_not_found(template_manager):
    """Test loading non-existent template"""
    with pytest.raises(StackTemplateNotFoundError):
        template_manager.load_template("nonexistent")


def test_load_template_empty(template_manager, tmp_config_dir):
    """Test loading empty template file"""
    # Create empty template
    template_path = tmp_config_dir / "empty.yaml"
    template_path.write_text("")

    with pytest.raises(StackTemplateValidationError, match="empty"):
        template_manager.load_template("empty")


def test_load_template_invalid_yaml(template_manager, tmp_config_dir):
    """Test loading template with invalid YAML"""
    template_path = tmp_config_dir / "invalid.yaml"
    template_path.write_text("invalid: yaml: content: [")

    with pytest.raises(StackTemplateValidationError, match="invalid YAML"):
        template_manager.load_template("invalid")


def test_validate_template_success(template_manager, sample_template):
    """Test validating a valid template"""
    # Should not raise an exception
    template_manager.validate_template(sample_template, "network")


def test_validate_template_missing_name(template_manager):
    """Test validation fails without name"""
    template = {"description": "Test"}

    with pytest.raises(StackTemplateValidationError, match="missing required field: name"):
        template_manager.validate_template(template, "test")


def test_validate_template_invalid_dependencies(template_manager):
    """Test validation fails with invalid dependencies"""
    template = {
        "name": "test",
        "dependencies": "should-be-list"  # Should be list
    }

    with pytest.raises(StackTemplateValidationError, match="dependencies must be a list"):
        template_manager.validate_template(template, "test")


def test_validate_template_invalid_priority(template_manager):
    """Test validation fails with invalid priority"""
    template = {
        "name": "test",
        "priority": "should-be-int"
    }

    with pytest.raises(StackTemplateValidationError, match="priority must be a positive integer"):
        template_manager.validate_template(template, "test")


def test_validate_template_invalid_parameters_type(template_manager):
    """Test validation fails when parameters is not a dict"""
    template = {
        "name": "test",
        "parameters": "should-be-dict"
    }

    with pytest.raises(StackTemplateValidationError, match="parameters must be a dict"):
        template_manager.validate_template(template, "test")


def test_validate_template_invalid_inputs_type(template_manager):
    """Test validation fails when inputs is not a dict"""
    template = {
        "name": "test",
        "parameters": {
            "inputs": "should-be-dict"
        }
    }

    with pytest.raises(StackTemplateValidationError, match="inputs must be a dict"):
        template_manager.validate_template(template, "test")


def test_validate_template_invalid_input_parameter(template_manager):
    """Test validation fails with invalid input parameter"""
    template = {
        "name": "test",
        "parameters": {
            "inputs": {
                "vpcId": "should-be-dict"
            }
        }
    }

    with pytest.raises(StackTemplateValidationError, match="input 'vpcId' must be a dict"):
        template_manager.validate_template(template, "test")


def test_validate_template_invalid_input_type(template_manager):
    """Test validation fails with invalid input type"""
    template = {
        "name": "test",
        "parameters": {
            "inputs": {
                "vpcId": {
                    "type": "invalid_type"
                }
            }
        }
    }

    with pytest.raises(StackTemplateValidationError, match="has invalid type"):
        template_manager.validate_template(template, "test")


def test_validate_template_strict_mode(template_manager):
    """Test strict validation requires type and required fields"""
    template = {
        "name": "test",
        "parameters": {
            "inputs": {
                "vpcId": {
                    # Missing type and required in strict mode
                }
            }
        }
    }

    with pytest.raises(StackTemplateValidationError, match="strict mode"):
        template_manager.validate_template(template, "test", strict=True)


def test_save_template_success(template_manager, sample_template):
    """Test saving a template"""
    template_path = template_manager.save_template("network", sample_template)

    assert template_path.exists()
    assert template_path.name == "network.yaml"


def test_save_template_overwrite(template_manager, tmp_config_dir, sample_template):
    """Test overwriting existing template"""
    # Create initial template
    template_manager.save_template("network", sample_template)

    # Modify and save with overwrite
    modified = sample_template.copy()
    modified["description"] = "Modified description"

    template_path = template_manager.save_template("network", modified, overwrite=True)

    # Verify overwrite
    with open(template_path, 'r') as f:
        loaded = yaml.safe_load(f)

    assert loaded["description"] == "Modified description"


def test_save_template_no_overwrite(template_manager, sample_template):
    """Test that save fails without overwrite flag"""
    template_manager.save_template("network", sample_template)

    with pytest.raises(FileExistsError):
        template_manager.save_template("network", sample_template, overwrite=False)


def test_save_template_invalid(template_manager):
    """Test saving invalid template fails"""
    invalid_template = {"description": "Missing name"}

    with pytest.raises(StackTemplateValidationError):
        template_manager.save_template("invalid", invalid_template)


def test_delete_template_success(template_manager, tmp_config_dir, sample_template):
    """Test deleting a template"""
    # Create template
    template_manager.save_template("network", sample_template)

    assert template_manager.delete_template("network") is True
    assert not template_manager.template_exists("network")


def test_delete_template_not_found(template_manager):
    """Test deleting non-existent template"""
    assert template_manager.delete_template("nonexistent") is False


def test_get_template_path(template_manager, tmp_config_dir):
    """Test getting template path"""
    path = template_manager.get_template_path("network")
    assert path == tmp_config_dir / "network.yaml"


def test_get_inputs(template_manager, tmp_config_dir, sample_template):
    """Test getting inputs from template"""
    template_manager.save_template("network", sample_template)

    inputs = template_manager.get_inputs("network")

    assert "vpcCidr" in inputs
    assert "region" in inputs
    assert inputs["vpcCidr"]["type"] == "string"


def test_get_outputs(template_manager, tmp_config_dir, sample_template):
    """Test getting outputs from template"""
    template_manager.save_template("network", sample_template)

    outputs = template_manager.get_outputs("network")

    assert "vpcId" in outputs
    assert outputs["vpcId"]["type"] == "string"


def test_get_required_inputs(template_manager, tmp_config_dir, sample_template):
    """Test getting required inputs"""
    template_manager.save_template("network", sample_template)

    required = template_manager.get_required_inputs("network")

    assert "vpcCidr" in required
    assert "region" not in required  # Optional


def test_get_optional_inputs(template_manager, tmp_config_dir, sample_template):
    """Test getting optional inputs"""
    template_manager.save_template("network", sample_template)

    optional = template_manager.get_optional_inputs("network")

    assert "region" in optional
    assert "vpcCidr" not in optional  # Required


def test_merge_with_defaults(template_manager, tmp_config_dir, sample_template):
    """Test merging config values with defaults"""
    template_manager.save_template("network", sample_template)

    # Provide only vpcCidr, region should get default
    config = {"vpcCidr": "10.0.0.0/16"}

    merged = template_manager.merge_with_defaults("network", config)

    assert merged["vpcCidr"] == "10.0.0.0/16"
    assert merged["region"] == "us-east-1"  # From default


def test_merge_with_defaults_overrides(template_manager, tmp_config_dir, sample_template):
    """Test that provided values override defaults"""
    template_manager.save_template("network", sample_template)

    config = {
        "vpcCidr": "10.0.0.0/16",
        "region": "us-west-2"  # Override default
    }

    merged = template_manager.merge_with_defaults("network", config)

    assert merged["region"] == "us-west-2"


def test_validate_template_invalid_output_type(template_manager):
    """Test validation fails with invalid output type"""
    template = {
        "name": "test",
        "parameters": {
            "outputs": {
                "vpcId": {
                    "type": "invalid_type"
                }
            }
        }
    }

    with pytest.raises(StackTemplateValidationError, match="has invalid type"):
        template_manager.validate_template(template, "test")


def test_validate_template_outputs_not_dict(template_manager):
    """Test validation fails when outputs is not a dict"""
    template = {
        "name": "test",
        "parameters": {
            "outputs": "should-be-dict"
        }
    }

    with pytest.raises(StackTemplateValidationError, match="outputs must be a dict"):
        template_manager.validate_template(template, "test")


def test_validate_template_invalid_output_parameter(template_manager):
    """Test validation fails with invalid output parameter"""
    template = {
        "name": "test",
        "parameters": {
            "outputs": {
                "vpcId": "should-be-dict"
            }
        }
    }

    with pytest.raises(StackTemplateValidationError, match="output 'vpcId' must be a dict"):
        template_manager.validate_template(template, "test")
