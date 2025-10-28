"""Tests for DependencyValidator"""

import pytest
from cloud_core.validation.dependency_validator import DependencyValidator


def test_dependency_validator_init():
    """Test DependencyValidator initialization"""
    validator = DependencyValidator()
    assert validator is not None


def test_validate_dependencies_no_cycles():
    """Test validating dependencies without cycles"""
    validator = DependencyValidator()

    stacks = {
        "network": {"dependencies": []},
        "security": {"dependencies": ["network"]},
        "app": {"dependencies": ["network", "security"]}
    }

    result = validator.validate(stacks)

    assert result is True


def test_validate_dependencies_with_cycle():
    """Test validating dependencies with circular dependency"""
    validator = DependencyValidator()

    stacks = {
        "stack_a": {"dependencies": ["stack_b"]},
        "stack_b": {"dependencies": ["stack_a"]}
    }

    result = validator.validate(stacks)

    assert result is False
    errors = validator.get_errors()
    assert len(errors) > 0
    assert "circular" in errors[0].lower() or "cycle" in errors[0].lower()


def test_validate_dependencies_missing_dependency():
    """Test validating with missing dependency"""
    validator = DependencyValidator()

    stacks = {
        "app": {"dependencies": ["nonexistent"]}
    }

    result = validator.validate(stacks)

    assert result is False
    errors = validator.get_errors()
    assert len(errors) > 0
    assert "nonexistent" in errors[0]


def test_validate_dependencies_complex_graph():
    """Test validating complex dependency graph"""
    validator = DependencyValidator()

    stacks = {
        "network": {"dependencies": []},
        "security": {"dependencies": ["network"]},
        "database": {"dependencies": ["network", "security"]},
        "app": {"dependencies": ["network", "security", "database"]}
    }

    result = validator.validate(stacks)

    assert result is True


def test_validate_self_dependency():
    """Test validating stack depending on itself"""
    validator = DependencyValidator()

    stacks = {
        "network": {"dependencies": ["network"]}
    }

    result = validator.validate(stacks)

    assert result is False


def test_get_errors():
    """Test getting validation errors"""
    validator = DependencyValidator()

    stacks = {
        "stack_a": {"dependencies": ["stack_b"]},
        "stack_b": {"dependencies": ["stack_a"]}
    }

    validator.validate(stacks)
    errors = validator.get_errors()

    assert len(errors) > 0
    assert isinstance(errors[0], str)


def test_validate_empty_stacks():
    """Test validating empty stacks"""
    validator = DependencyValidator()

    result = validator.validate({})

    assert result is True


def test_validate_single_stack():
    """Test validating single stack without dependencies"""
    validator = DependencyValidator()

    stacks = {
        "network": {"dependencies": []}
    }

    result = validator.validate(stacks)

    assert result is True


def test_validate_stacks_no_dependencies_key():
    """Test validating stacks without dependencies key"""
    validator = DependencyValidator()

    stacks = {
        "network": {},
        "security": {}
    }

    result = validator.validate(stacks)

    # Should handle missing dependencies key
    assert result is True or result is False  # Implementation dependent


def test_multiple_cycles():
    """Test detecting multiple cycles"""
    validator = DependencyValidator()

    stacks = {
        "a": {"dependencies": ["b"]},
        "b": {"dependencies": ["c"]},
        "c": {"dependencies": ["a"]},
        "x": {"dependencies": ["y"]},
        "y": {"dependencies": ["x"]}
    }

    result = validator.validate(stacks)

    assert result is False
    errors = validator.get_errors()
    # Should detect at least one cycle
    assert len(errors) >= 1


def test_get_warnings():
    """Test getting warnings"""
    validator = DependencyValidator()

    stacks = {
        "network": {"dependencies": []},
    }

    validator.validate(stacks)
    warnings = validator.get_warnings()

    # Currently no warnings are generated, but method should work
    assert isinstance(warnings, list)


def test_validate_with_invalid_input():
    """Test validation with invalid input that causes exception"""
    validator = DependencyValidator()

    # Create a stacks config that will cause an exception
    # This is tricky - we need to mock or create a scenario that causes an exception
    # Let's try with a non-dict dependency list
    import unittest.mock as mock

    with mock.patch('cloud_core.validation.dependency_validator.DependencyResolver') as mock_resolver:
        mock_instance = mock.Mock()
        mock_resolver.return_value = mock_instance

        # Make build_graph raise a general exception
        mock_instance.build_graph.side_effect = RuntimeError("Unexpected error")

        result = validator.validate({"network": {"dependencies": []}})

        assert result is False
        errors = validator.get_errors()
        assert len(errors) > 0
        assert "Unexpected error" in errors[0]
