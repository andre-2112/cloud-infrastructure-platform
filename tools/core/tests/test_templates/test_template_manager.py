"""Tests for TemplateManager"""

import pytest
import tempfile
import yaml
from pathlib import Path
from cloud_core.templates.template_manager import TemplateManager


@pytest.fixture
def temp_template_dir(tmp_path):
    """Create temporary template directory"""
    template_dir = tmp_path / "tools" / "templates" / "default"
    template_dir.mkdir(parents=True)

    # Create a test template
    template = {
        "deployment": {
            "org": "TestOrg",
            "project": "test-project",
        },
        "stacks": {
            "network": {"enabled": True, "dependencies": []},
        },
    }

    template_file = template_dir / "test-template.yaml"
    with open(template_file, 'w') as f:
        yaml.dump(template, f)

    return tmp_path


def test_template_manager_list_templates(temp_template_dir, monkeypatch):
    """Test listing templates"""
    monkeypatch.chdir(temp_template_dir)

    manager = TemplateManager()
    templates = manager.list_templates()

    assert len(templates) > 0
    assert "test-template" in templates


def test_template_manager_template_exists(temp_template_dir, monkeypatch):
    """Test checking if template exists"""
    monkeypatch.chdir(temp_template_dir)

    manager = TemplateManager()
    assert manager.template_exists("test-template") is True
    assert manager.template_exists("nonexistent") is False


def test_template_manager_load_template(temp_template_dir, monkeypatch):
    """Test loading a template"""
    monkeypatch.chdir(temp_template_dir)

    manager = TemplateManager()
    template = manager.load_template("test-template")

    assert template is not None
    assert "deployment" in template
    assert "stacks" in template


def test_template_manager_load_nonexistent():
    """Test loading nonexistent template"""
    manager = TemplateManager()

    with pytest.raises(FileNotFoundError):
        manager.load_template("nonexistent-template")


def test_template_manager_list_custom_templates(temp_template_dir, monkeypatch):
    """Test listing custom templates"""
    monkeypatch.chdir(temp_template_dir)

    # Create custom templates directory and template
    custom_dir = temp_template_dir / "tools" / "templates" / "custom"
    custom_dir.mkdir(parents=True)

    custom_template = {
        "stacks": {
            "custom-stack": {"enabled": True, "dependencies": []},
        },
    }

    custom_file = custom_dir / "my-custom.yaml"
    with open(custom_file, 'w') as f:
        yaml.dump(custom_template, f)

    manager = TemplateManager()
    templates = manager.list_templates(include_custom=True)

    assert "custom:my-custom" in templates


def test_template_manager_list_default_only(temp_template_dir, monkeypatch):
    """Test listing only default templates"""
    monkeypatch.chdir(temp_template_dir)

    # Create custom template
    custom_dir = temp_template_dir / "tools" / "templates" / "custom"
    custom_dir.mkdir(parents=True)

    custom_template = {
        "stacks": {
            "custom-stack": {"enabled": True, "dependencies": []},
        },
    }

    custom_file = custom_dir / "my-custom.yaml"
    with open(custom_file, 'w') as f:
        yaml.dump(custom_template, f)

    manager = TemplateManager()
    templates = manager.list_templates(include_custom=False)

    # Should not include custom templates
    assert not any(t.startswith("custom:") for t in templates)


def test_template_manager_load_custom_template(temp_template_dir, monkeypatch):
    """Test loading custom template"""
    monkeypatch.chdir(temp_template_dir)

    # Create custom template
    custom_dir = temp_template_dir / "tools" / "templates" / "custom"
    custom_dir.mkdir(parents=True)

    custom_template = {
        "stacks": {
            "custom-stack": {"enabled": True, "dependencies": []},
        },
    }

    custom_file = custom_dir / "my-custom.yaml"
    with open(custom_file, 'w') as f:
        yaml.dump(custom_template, f)

    manager = TemplateManager()
    template = manager.load_template("custom:my-custom")

    assert template is not None
    assert "custom-stack" in template["stacks"]


def test_template_manager_load_empty_template(temp_template_dir, monkeypatch):
    """Test loading empty template"""
    monkeypatch.chdir(temp_template_dir)

    # Create empty template file
    template_dir = temp_template_dir / "tools" / "templates" / "default"
    empty_file = template_dir / "empty.yaml"
    empty_file.write_text("")

    manager = TemplateManager()

    from cloud_core.templates.template_manager import TemplateValidationError
    with pytest.raises(TemplateValidationError, match="empty"):
        manager.load_template("empty")


def test_template_manager_load_invalid_yaml(temp_template_dir, monkeypatch):
    """Test loading template with invalid YAML"""
    monkeypatch.chdir(temp_template_dir)

    # Create invalid YAML
    template_dir = temp_template_dir / "tools" / "templates" / "default"
    invalid_file = template_dir / "invalid.yaml"
    invalid_file.write_text("invalid: yaml: content: [unclosed")

    manager = TemplateManager()

    from cloud_core.templates.template_manager import TemplateValidationError
    with pytest.raises(TemplateValidationError, match="invalid YAML"):
        manager.load_template("invalid")


def test_template_manager_validate_missing_stacks(temp_template_dir, monkeypatch):
    """Test validation of template missing stacks field"""
    monkeypatch.chdir(temp_template_dir)

    # Create template without stacks
    template_dir = temp_template_dir / "tools" / "templates" / "default"
    invalid_template = {"deployment": {"org": "Test"}}

    invalid_file = template_dir / "no-stacks.yaml"
    with open(invalid_file, 'w') as f:
        yaml.dump(invalid_template, f)

    manager = TemplateManager()

    from cloud_core.templates.template_manager import TemplateValidationError
    with pytest.raises(TemplateValidationError, match="missing required field: stacks"):
        manager.load_template("no-stacks")


def test_template_manager_validate_unsupported_version(temp_template_dir, monkeypatch):
    """Test validation of unsupported version"""
    monkeypatch.chdir(temp_template_dir)

    # Create template with unsupported version
    template_dir = temp_template_dir / "tools" / "templates" / "default"
    invalid_template = {
        "version": "2.0",  # Unsupported version
        "stacks": {
            "network": {"enabled": True, "dependencies": []},
        },
    }

    invalid_file = template_dir / "old-version.yaml"
    with open(invalid_file, 'w') as f:
        yaml.dump(invalid_template, f)

    manager = TemplateManager()

    from cloud_core.templates.template_manager import TemplateValidationError
    with pytest.raises(TemplateValidationError, match="unsupported version"):
        manager.load_template("old-version")


def test_template_manager_validate_invalid_stacks_section(temp_template_dir, monkeypatch):
    """Test validation of invalid stacks section"""
    monkeypatch.chdir(temp_template_dir)

    # Create template with invalid stacks (not a dict)
    template_dir = temp_template_dir / "tools" / "templates" / "default"
    invalid_template = {
        "stacks": ["not", "a", "dict"],
    }

    invalid_file = template_dir / "invalid-stacks.yaml"
    with open(invalid_file, 'w') as f:
        yaml.dump(invalid_template, f)

    manager = TemplateManager()

    from cloud_core.templates.template_manager import TemplateValidationError
    with pytest.raises(TemplateValidationError, match="invalid stacks section"):
        manager.load_template("invalid-stacks")


def test_template_manager_validate_invalid_stack_config(temp_template_dir, monkeypatch):
    """Test validation of invalid stack config"""
    monkeypatch.chdir(temp_template_dir)

    # Create template with invalid stack config (not a dict)
    template_dir = temp_template_dir / "tools" / "templates" / "default"
    invalid_template = {
        "stacks": {
            "network": "not a dict",
        },
    }

    invalid_file = template_dir / "invalid-config.yaml"
    with open(invalid_file, 'w') as f:
        yaml.dump(invalid_template, f)

    manager = TemplateManager()

    from cloud_core.templates.template_manager import TemplateValidationError
    with pytest.raises(TemplateValidationError, match="invalid config for stack"):
        manager.load_template("invalid-config")


def test_template_manager_validate_missing_enabled(temp_template_dir, monkeypatch):
    """Test validation of stack missing enabled field"""
    monkeypatch.chdir(temp_template_dir)

    # Create template with stack missing enabled
    template_dir = temp_template_dir / "tools" / "templates" / "default"
    invalid_template = {
        "stacks": {
            "network": {
                "dependencies": [],
            },
        },
    }

    invalid_file = template_dir / "no-enabled.yaml"
    with open(invalid_file, 'w') as f:
        yaml.dump(invalid_template, f)

    manager = TemplateManager()

    from cloud_core.templates.template_manager import TemplateValidationError
    with pytest.raises(TemplateValidationError, match="missing 'enabled' field"):
        manager.load_template("no-enabled")


def test_template_manager_validate_missing_dependencies(temp_template_dir, monkeypatch):
    """Test validation of stack missing dependencies field"""
    monkeypatch.chdir(temp_template_dir)

    # Create template with stack missing dependencies
    template_dir = temp_template_dir / "tools" / "templates" / "default"
    invalid_template = {
        "stacks": {
            "network": {
                "enabled": True,
            },
        },
    }

    invalid_file = template_dir / "no-deps.yaml"
    with open(invalid_file, 'w') as f:
        yaml.dump(invalid_template, f)

    manager = TemplateManager()

    from cloud_core.templates.template_manager import TemplateValidationError
    with pytest.raises(TemplateValidationError, match="missing 'dependencies' field"):
        manager.load_template("no-deps")


def test_template_manager_get_template_info(temp_template_dir, monkeypatch):
    """Test getting template info"""
    monkeypatch.chdir(temp_template_dir)

    # Create template with metadata
    template_dir = temp_template_dir / "tools" / "templates" / "default"
    template = {
        "version": "3.1",
        "description": "Test template",
        "template_name": "test-info",
        "stacks": {
            "network": {"enabled": True, "dependencies": []},
            "security": {"enabled": True, "dependencies": ["network"]},
        },
        "metadata": {"author": "Test"},
    }

    template_file = template_dir / "test-info.yaml"
    with open(template_file, 'w') as f:
        yaml.dump(template, f)

    manager = TemplateManager()
    info = manager.get_template_info("test-info")

    assert info["name"] == "test-info"
    assert info["version"] == "3.1"
    assert info["description"] == "Test template"
    assert info["stack_count"] == 2
    assert "network" in info["stacks"]
    assert "security" in info["stacks"]
    assert info["metadata"]["author"] == "Test"


def test_template_manager_create_custom_template(temp_template_dir, monkeypatch):
    """Test creating custom template"""
    monkeypatch.chdir(temp_template_dir)

    manager = TemplateManager()

    template_data = {
        "stacks": {
            "new-stack": {"enabled": True, "dependencies": []},
        },
    }

    path = manager.create_custom_template("my-template", template_data)

    assert path.exists()
    assert path.name == "my-template.yaml"

    # Verify it can be loaded
    loaded = manager.load_template("custom:my-template")
    assert "new-stack" in loaded["stacks"]


def test_template_manager_create_custom_template_overwrite(temp_template_dir, monkeypatch):
    """Test overwriting custom template"""
    monkeypatch.chdir(temp_template_dir)

    manager = TemplateManager()

    template_data = {
        "stacks": {
            "stack1": {"enabled": True, "dependencies": []},
        },
    }

    # Create initial template
    manager.create_custom_template("overwrite-test", template_data)

    # Try to create again without overwrite - should fail
    with pytest.raises(FileExistsError):
        manager.create_custom_template("overwrite-test", template_data, overwrite=False)

    # Create again with overwrite - should succeed
    new_template_data = {
        "stacks": {
            "stack2": {"enabled": True, "dependencies": []},
        },
    }

    path = manager.create_custom_template("overwrite-test", new_template_data, overwrite=True)
    assert path.exists()

    # Verify it was overwritten
    loaded = manager.load_template("custom:overwrite-test")
    assert "stack2" in loaded["stacks"]
    assert "stack1" not in loaded["stacks"]


def test_template_manager_create_custom_template_invalid(temp_template_dir, monkeypatch):
    """Test creating custom template with invalid data"""
    monkeypatch.chdir(temp_template_dir)

    manager = TemplateManager()

    # Invalid template data (missing stacks)
    invalid_data = {"deployment": {"org": "Test"}}

    from cloud_core.templates.template_manager import TemplateValidationError
    with pytest.raises(TemplateValidationError):
        manager.create_custom_template("invalid", invalid_data)


def test_template_manager_delete_custom_template(temp_template_dir, monkeypatch):
    """Test deleting custom template"""
    monkeypatch.chdir(temp_template_dir)

    manager = TemplateManager()

    # Create custom template
    template_data = {
        "stacks": {
            "stack": {"enabled": True, "dependencies": []},
        },
    }

    manager.create_custom_template("to-delete", template_data)

    # Verify it exists
    assert manager.template_exists("custom:to-delete")

    # Delete it
    result = manager.delete_custom_template("custom:to-delete")
    assert result is True

    # Verify it's gone
    assert not manager.template_exists("custom:to-delete")


def test_template_manager_delete_custom_template_without_prefix(temp_template_dir, monkeypatch):
    """Test deleting custom template without 'custom:' prefix"""
    monkeypatch.chdir(temp_template_dir)

    manager = TemplateManager()

    # Create custom template
    template_data = {
        "stacks": {
            "stack": {"enabled": True, "dependencies": []},
        },
    }

    manager.create_custom_template("to-delete2", template_data)

    # Delete without prefix
    result = manager.delete_custom_template("to-delete2")
    assert result is True

    assert not manager.template_exists("custom:to-delete2")


def test_template_manager_delete_nonexistent_template(temp_template_dir, monkeypatch):
    """Test deleting non-existent template"""
    monkeypatch.chdir(temp_template_dir)

    manager = TemplateManager()
    result = manager.delete_custom_template("nonexistent")

    assert result is False


def test_template_manager_get_template_path(temp_template_dir, monkeypatch):
    """Test get_template_path method"""
    monkeypatch.chdir(temp_template_dir)

    manager = TemplateManager()

    # Get path for existing template
    path = manager.get_template_path("test-template")
    assert path is not None
    assert path.exists()
    assert path.name == "test-template.yaml"

    # Get path for non-existent template
    path = manager.get_template_path("nonexistent")
    assert path is None
