"""Tests for StackCodeValidator"""

import pytest
from pathlib import Path
from cloud_core.validation.stack_code_validator import (
    StackCodeValidator,
    ValidationIssue,
    ValidationResult
)


@pytest.fixture
def validator():
    """Create a StackCodeValidator instance"""
    return StackCodeValidator()


@pytest.fixture
def tmp_stack_dir(tmp_path):
    """Create a temporary stack directory with TypeScript code"""
    stack_dir = tmp_path / "test-stack"
    stack_dir.mkdir()

    (stack_dir / "index.ts").write_text("""
    import * as pulumi from "@pulumi/pulumi";
    const config = new pulumi.Config();

    const vpcCidr = config.require("vpcCidr");
    const region = config.get("region", "us-east-1");

    export const vpcId = "vpc-12345";
    export const vpcArn = "arn:aws:vpc:us-east-1:123456789012:vpc/vpc-12345";
    """)

    return stack_dir


@pytest.fixture
def matching_template():
    """Template that matches the stack code"""
    return {
        "name": "test-stack",
        "parameters": {
            "inputs": {
                "vpcCidr": {"type": "string", "required": True},
                "region": {"type": "string", "required": False}
            },
            "outputs": {
                "vpcId": {"type": "string"},
                "vpcArn": {"type": "string"}
            }
        }
    }


def test_validation_issue_dataclass():
    """Test ValidationIssue dataclass"""
    issue = ValidationIssue("error", "Test error", "input:vpcId")

    assert issue.severity == "error"
    assert issue.message == "Test error"
    assert issue.location == "input:vpcId"


def test_validation_result_init():
    """Test ValidationResult initialization"""
    result = ValidationResult(valid=True)

    assert result.valid is True
    assert len(result.errors) == 0
    assert len(result.warnings) == 0


def test_validation_result_add_error():
    """Test adding error to result"""
    result = ValidationResult(valid=True)

    result.add_error("Test error", "input:vpcId")

    assert result.valid is False
    assert len(result.errors) == 1
    assert result.errors[0].message == "Test error"


def test_validation_result_add_warning():
    """Test adding warning to result"""
    result = ValidationResult(valid=True)

    result.add_warning("Test warning", "input:region")

    assert result.valid is True  # Warnings don't affect validity
    assert len(result.warnings) == 1


def test_validation_result_has_issues():
    """Test has_issues method"""
    result = ValidationResult(valid=True)

    assert result.has_issues() is False

    result.add_warning("Warning")
    assert result.has_issues() is True


def test_validation_result_get_counts():
    """Test error and warning count methods"""
    result = ValidationResult(valid=True)

    result.add_error("Error 1")
    result.add_error("Error 2")
    result.add_warning("Warning 1")

    assert result.get_error_count() == 2
    assert result.get_warning_count() == 1


def test_validator_init(validator):
    """Test StackCodeValidator initialization"""
    assert validator is not None


def test_validate_matching_code_and_template(validator, tmp_stack_dir, matching_template):
    """Test validation when code matches template"""
    # Mock the ParameterExtractor import inside validate()
    import unittest.mock as mock
    with mock.patch('cloud_cli.parser.ParameterExtractor') as mock_extractor:
        mock_instance = mock_extractor.return_value
        mock_instance.extract_from_stack.return_value = {
            "success": True,
            "parameters": matching_template["parameters"],
            "warnings": []
        }

        result = validator.validate(tmp_stack_dir, matching_template, "test-stack")

        assert result.valid is True
        assert len(result.errors) == 0


def test_validate_undeclared_input(validator, tmp_path):
    """Test validation detects undeclared input"""
    # Create stack with undeclared input
    stack_dir = tmp_path / "stack"
    stack_dir.mkdir()
    (stack_dir / "index.ts").write_text("""
    const config = new pulumi.Config();
    const undeclaredParam = config.require("undeclaredParam");
    """)

    template = {
        "name": "stack",
        "parameters": {
            "inputs": {},
            "outputs": {}
        }
    }

    result = validator.validate(stack_dir, template, "stack")

    assert result.valid is False
    assert len(result.errors) > 0
    assert any("undeclaredParam" in e.message and "not declared" in e.message for e in result.errors)


def test_validate_unused_input_strict(validator, tmp_path):
    """Test validation detects unused input in strict mode"""
    # Create stack without using all template inputs
    stack_dir = tmp_path / "stack"
    stack_dir.mkdir()
    (stack_dir / "index.ts").write_text("""
    const config = new pulumi.Config();
    const vpcId = config.require("vpcId");
    """)

    template = {
        "name": "stack",
        "parameters": {
            "inputs": {
                "vpcId": {"type": "string", "required": True},
                "unusedParam": {"type": "string", "required": True}
            },
            "outputs": {}
        }
    }

    result = validator.validate(stack_dir, template, "stack", strict=True)

    assert result.valid is False
    assert any("unusedParam" in e.message and "not used" in e.message for e in result.errors)


def test_validate_unused_input_non_strict(validator, tmp_path):
    """Test validation gives warning for unused input in non-strict mode"""
    stack_dir = tmp_path / "stack"
    stack_dir.mkdir()
    (stack_dir / "index.ts").write_text("""
    const config = new pulumi.Config();
    const vpcId = config.require("vpcId");
    """)

    template = {
        "name": "stack",
        "parameters": {
            "inputs": {
                "vpcId": {"type": "string", "required": True},
                "unusedParam": {"type": "string", "required": True}
            },
            "outputs": {}
        }
    }

    result = validator.validate(stack_dir, template, "stack", strict=False)

    assert result.valid is True  # Valid but with warnings
    assert len(result.warnings) > 0
    assert any("unusedParam" in w.message for w in result.warnings)


def test_validate_type_mismatch(validator, tmp_path):
    """Test validation detects type mismatches"""
    stack_dir = tmp_path / "stack"
    stack_dir.mkdir()
    (stack_dir / "index.ts").write_text("""
    const config = new pulumi.Config();
    const port = config.requireNumber("port");
    """)

    template = {
        "name": "stack",
        "parameters": {
            "inputs": {
                "port": {"type": "string", "required": True}  # Wrong type
            },
            "outputs": {}
        }
    }

    result = validator.validate(stack_dir, template, "stack")

    assert len(result.warnings) > 0
    assert any("type mismatch" in w.message.lower() for w in result.warnings)


def test_validate_missing_output(validator, tmp_path):
    """Test validation detects missing output"""
    stack_dir = tmp_path / "stack"
    stack_dir.mkdir()
    (stack_dir / "index.ts").write_text("""
    const config = new pulumi.Config();
    const vpcId = config.require("vpcId");
    """)

    template = {
        "name": "stack",
        "parameters": {
            "inputs": {
                "vpcId": {"type": "string", "required": True}
            },
            "outputs": {
                "vpcId": {"type": "string"}  # Declared but not exported
            }
        }
    }

    result = validator.validate(stack_dir, template, "stack")

    assert result.valid is False
    assert any("vpcId" in e.message and "not exported" in e.message for e in result.errors)


def test_validate_undeclared_output_strict(validator, tmp_path):
    """Test validation detects undeclared output in strict mode"""
    stack_dir = tmp_path / "stack"
    stack_dir.mkdir()
    (stack_dir / "index.ts").write_text("""
    const config = new pulumi.Config();
    const vpcId = config.require("vpcId");
    export const undeclaredOutput = "value";
    """)

    template = {
        "name": "stack",
        "parameters": {
            "inputs": {
                "vpcId": {"type": "string", "required": True}
            },
            "outputs": {}
        }
    }

    result = validator.validate(stack_dir, template, "stack", strict=True)

    assert result.valid is False
    assert any("undeclaredOutput" in e.message for e in result.errors)


def test_validate_undeclared_output_non_strict(validator, tmp_path):
    """Test validation gives warning for undeclared output in non-strict mode"""
    stack_dir = tmp_path / "stack"
    stack_dir.mkdir()
    (stack_dir / "index.ts").write_text("""
    const config = new pulumi.Config();
    const vpcId = config.require("vpcId");
    export const undeclaredOutput = "value";
    """)

    template = {
        "name": "stack",
        "parameters": {
            "inputs": {
                "vpcId": {"type": "string", "required": True}
            },
            "outputs": {}
        }
    }

    result = validator.validate(stack_dir, template, "stack", strict=False)

    assert result.valid is True
    assert len(result.warnings) > 0


def test_validate_stack_not_found(validator, tmp_path):
    """Test validation when stack directory doesn't exist"""
    non_existent = tmp_path / "nonexistent"

    template = {"name": "test", "parameters": {"inputs": {}, "outputs": {}}}

    result = validator.validate(non_existent, template, "test")

    assert result.valid is False
    assert len(result.errors) > 0


def test_validate_multiple_stacks(validator, tmp_path):
    """Test validating multiple stacks"""
    stacks_dir = tmp_path / "stacks"
    stacks_dir.mkdir()

    # Create two stacks
    for stack_name in ["network", "security"]:
        stack_dir = stacks_dir / stack_name
        stack_dir.mkdir()
        (stack_dir / "index.ts").write_text("""
        const config = new pulumi.Config();
        const param = config.require("param");
        export const output = "value";
        """)

    templates = {
        "network": {
            "name": "network",
            "parameters": {
                "inputs": {"param": {"type": "string", "required": True}},
                "outputs": {"output": {"type": "string"}}
            }
        },
        "security": {
            "name": "security",
            "parameters": {
                "inputs": {"param": {"type": "string", "required": True}},
                "outputs": {"output": {"type": "string"}}
            }
        }
    }

    results = validator.validate_multiple_stacks(stacks_dir, templates)

    assert len(results) == 2
    assert results["network"].valid is True
    assert results["security"].valid is True


def test_validate_multiple_stacks_with_failure(validator, tmp_path):
    """Test validating multiple stacks with one failure"""
    stacks_dir = tmp_path / "stacks"
    stacks_dir.mkdir()

    # Create two stacks, one with issue
    stack1 = stacks_dir / "stack1"
    stack1.mkdir()
    (stack1 / "index.ts").write_text("""
    const config = new pulumi.Config();
    const param = config.require("param");
    export const output = "value";
    """)

    stack2 = stacks_dir / "stack2"
    stack2.mkdir()
    (stack2 / "index.ts").write_text("""
    const config = new pulumi.Config();
    const wrongParam = config.require("wrongParam");
    """)

    templates = {
        "stack1": {
            "parameters": {
                "inputs": {"param": {"type": "string", "required": True}},
                "outputs": {"output": {"type": "string"}}
            }
        },
        "stack2": {
            "parameters": {
                "inputs": {"param": {"type": "string", "required": True}},
                "outputs": {}
            }
        }
    }

    results = validator.validate_multiple_stacks(stacks_dir, templates)

    assert results["stack1"].valid is True
    assert results["stack2"].valid is False


def test_format_validation_result(validator):
    """Test formatting validation result"""
    result = ValidationResult(valid=False, stack_name="test-stack")
    result.add_error("Test error", "input:vpcId")
    result.add_warning("Test warning", "output:vpcArn")

    formatted = validator.format_validation_result(result)

    assert "test-stack" in formatted
    assert "Error(s)" in formatted
    assert "Test error" in formatted
    assert "Warning(s)" in formatted
    assert "Test warning" in formatted


def test_format_validation_result_valid(validator):
    """Test formatting valid result"""
    result = ValidationResult(valid=True, stack_name="test-stack")

    formatted = validator.format_validation_result(result)

    assert "test-stack" in formatted
    assert "Validation passed" in formatted


def test_format_multiple_results(validator):
    """Test formatting multiple validation results"""
    results = {
        "stack1": ValidationResult(valid=True, stack_name="stack1"),
        "stack2": ValidationResult(valid=False, stack_name="stack2")
    }
    results["stack2"].add_error("Test error")

    formatted = validator.format_multiple_results(results)

    assert "Stack Code Validation Results" in formatted
    assert "stack1" in formatted
    assert "stack2" in formatted
    assert "Valid: 1/2" in formatted


def test_validate_deployment_all_valid(validator, tmp_path):
    """Test validate_deployment with all valid stacks"""
    # Create stacks directory
    stacks_dir = tmp_path / "stacks"
    stacks_dir.mkdir()

    stack_dir = stacks_dir / "network"
    stack_dir.mkdir()
    (stack_dir / "index.ts").write_text("""
    const config = new pulumi.Config();
    const vpcCidr = config.require("vpcCidr");
    export const vpcId = "vpc-12345";
    """)

    # Create template
    config_dir = tmp_path / "templates" / "config"
    config_dir.mkdir(parents=True)

    import yaml
    template = {
        "name": "network",
        "parameters": {
            "inputs": {"vpcCidr": {"type": "string", "required": True}},
            "outputs": {"vpcId": {"type": "string"}}
        }
    }

    with open(config_dir / "network.yaml", 'w') as f:
        yaml.dump(template, f)

    # Create manifest
    manifest = {
        "stacks": {
            "network": {
                "enabled": True,
                "dependencies": []
            }
        }
    }

    # Mock the StackTemplateManager to use our test config dir
    import unittest.mock as mock
    with mock.patch('cloud_core.templates.stack_template_manager.StackTemplateManager') as mock_mgr:
        mock_instance = mock_mgr.return_value
        mock_instance.template_exists.return_value = True
        mock_instance.load_template.return_value = template

        all_valid, results = validator.validate_deployment(stacks_dir, manifest)

        assert all_valid is True
        assert "network" in results
        assert results["network"].valid is True


def test_validate_deployment_template_not_found(validator, tmp_path):
    """Test validate_deployment when template doesn't exist"""
    stacks_dir = tmp_path / "stacks"
    stacks_dir.mkdir()

    manifest = {
        "stacks": {
            "network": {
                "enabled": True
            }
        }
    }

    import unittest.mock as mock
    with mock.patch('cloud_core.templates.stack_template_manager.StackTemplateManager') as mock_mgr:
        mock_instance = mock_mgr.return_value
        mock_instance.template_exists.return_value = False

        all_valid, results = validator.validate_deployment(stacks_dir, manifest)

        assert all_valid is False
        assert "network" in results
        assert results["network"].valid is False


def test_validate_deployment_skips_disabled_stacks(validator, tmp_path):
    """Test validate_deployment skips disabled stacks"""
    stacks_dir = tmp_path / "stacks"

    manifest = {
        "stacks": {
            "network": {
                "enabled": False
            }
        }
    }

    all_valid, results = validator.validate_deployment(stacks_dir, manifest)

    assert all_valid is True
    assert len(results) == 0
