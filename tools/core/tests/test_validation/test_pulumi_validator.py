"""Tests for PulumiValidator"""

import pytest
from unittest.mock import Mock, patch
from cloud_core.validation.pulumi_validator import PulumiValidator


@pytest.fixture
def pulumi_validator():
    """Create PulumiValidator instance"""
    return PulumiValidator()


def test_pulumi_validator_init():
    """Test PulumiValidator initialization"""
    validator = PulumiValidator()
    assert validator is not None
    assert validator.errors == []
    assert validator.warnings == []


@patch.dict('os.environ', {'PULUMI_ACCESS_TOKEN': 'test-token'})
@patch('subprocess.run')
def test_validate_success(mock_run, pulumi_validator):
    """Test successful validation"""
    mock_run.return_value = Mock(returncode=0, stdout="v3.50.0\n")

    result = pulumi_validator.validate()

    assert result is True
    assert len(pulumi_validator.get_errors()) == 0


@patch('subprocess.run')
def test_validate_cli_not_installed(mock_run, pulumi_validator):
    """Test validation when Pulumi CLI is not installed"""
    mock_run.side_effect = FileNotFoundError()

    result = pulumi_validator.validate()

    assert result is False
    errors = pulumi_validator.get_errors()
    assert len(errors) > 0
    assert "not found" in errors[0].lower() or "install" in errors[0].lower()


@patch.dict('os.environ', {'PULUMI_ACCESS_TOKEN': 'test-token'})
@patch('subprocess.run')
def test_validate_cli_error(mock_run, pulumi_validator):
    """Test validation when CLI command fails"""
    import subprocess
    mock_run.side_effect = subprocess.CalledProcessError(1, 'pulumi', stderr="Command failed")

    result = pulumi_validator.validate()

    assert result is False
    errors = pulumi_validator.get_errors()
    assert len(errors) > 0


@patch.dict('os.environ', {}, clear=True)
@patch('subprocess.run')
def test_validate_no_access_token(mock_run, pulumi_validator):
    """Test validation when access token is not configured"""
    mock_run.return_value = Mock(returncode=0, stdout="v3.50.0\n")

    result = pulumi_validator.validate()

    assert result is False
    errors = pulumi_validator.get_errors()
    assert len(errors) > 0
    assert "access_token" in errors[0].lower() or "pulumi_access_token" in errors[0].lower()


def test_get_errors_empty():
    """Test getting errors when none exist"""
    validator = PulumiValidator()
    errors = validator.get_errors()

    assert errors == []
    assert isinstance(errors, list)


def test_get_warnings_empty():
    """Test getting warnings when none exist"""
    validator = PulumiValidator()
    warnings = validator.get_warnings()

    assert warnings == []
    assert isinstance(warnings, list)


@patch('subprocess.run')
def test_validate_clears_previous_errors(mock_run, pulumi_validator):
    """Test that validate clears previous errors"""
    # First validation fails
    mock_run.side_effect = FileNotFoundError()
    pulumi_validator.validate()
    assert len(pulumi_validator.get_errors()) > 0

    # Second validation succeeds
    with patch.dict('os.environ', {'PULUMI_ACCESS_TOKEN': 'test-token'}):
        mock_run.side_effect = None
        mock_run.return_value = Mock(returncode=0, stdout="v3.50.0\n")
        result = pulumi_validator.validate()

    assert result is True
    assert len(pulumi_validator.get_errors()) == 0


@patch.dict('os.environ', {'PULUMI_ACCESS_TOKEN': 'test-token'})
@patch('subprocess.run')
def test_validate_with_version_output(mock_run, pulumi_validator):
    """Test validation with different version output formats"""
    # Test with v prefix
    mock_run.return_value = Mock(returncode=0, stdout="v3.115.0\n")
    result = pulumi_validator.validate()
    assert result is True

    # Test without v prefix
    mock_run.return_value = Mock(returncode=0, stdout="3.115.0\n")
    result = pulumi_validator.validate()
    assert result is True

    # Test with extra text
    mock_run.return_value = Mock(returncode=0, stdout="Pulumi v3.115.0\n")
    result = pulumi_validator.validate()
    assert result is True


@patch.dict('os.environ', {'PULUMI_ACCESS_TOKEN': ''})
@patch('subprocess.run')
def test_validate_empty_access_token(mock_run, pulumi_validator):
    """Test validation when access token is empty"""
    mock_run.return_value = Mock(returncode=0, stdout="v3.50.0\n")

    result = pulumi_validator.validate()

    # Empty token should be treated as not configured
    assert result is False


@patch.dict('os.environ', {'PULUMI_ACCESS_TOKEN': 'test-token'})
@patch('subprocess.run')
def test_validate_subprocess_called_process_error(mock_run, pulumi_validator):
    """Test validation with subprocess.CalledProcessError"""
    import subprocess
    mock_run.side_effect = subprocess.CalledProcessError(1, 'pulumi')

    result = pulumi_validator.validate()

    assert result is False
    errors = pulumi_validator.get_errors()
    assert len(errors) > 0
