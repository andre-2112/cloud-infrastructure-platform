"""Simplified tests for StackCodeValidator that don't require cross-module imports"""

import pytest
from pathlib import Path
from cloud_core.validation.stack_code_validator import (
    StackCodeValidator,
    ValidationIssue,
    ValidationResult
)


def test_validation_issue():
    """Test ValidationIssue dataclass"""
    issue = ValidationIssue("error", "Test error", "input:vpcId")
    assert issue.severity == "error"
    assert issue.message == "Test error"


def test_validation_result():
    """Test ValidationResult dataclass"""
    result = ValidationResult(valid=True)
    assert result.valid is True

    result.add_error("Error")
    assert result.valid is False
    assert result.get_error_count() == 1


def test_validator_init():
    """Test StackCodeValidator initialization"""
    validator = StackCodeValidator()
    assert validator is not None


def test_format_validation_result():
    """Test formatting validation result"""
    validator = StackCodeValidator()
    result = ValidationResult(valid=False, stack_name="test")
    result.add_error("Test error")
    result.add_warning("Test warning")

    formatted = validator.format_validation_result(result)

    assert "test" in formatted
    assert "Test error" in formatted
    assert "Test warning" in formatted


def test_format_multiple_results():
    """Test formatting multiple results"""
    validator = StackCodeValidator()
    results = {
        "stack1": ValidationResult(valid=True, stack_name="stack1"),
        "stack2": ValidationResult(valid=False, stack_name="stack2")
    }
    results["stack2"].add_error("Error")

    formatted = validator.format_multiple_results(results)

    assert "Stack Code Validation Results" in formatted
    assert "stack1" in formatted
    assert "stack2" in formatted
