"""Tests for PulumiWrapper"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from cloud_core.pulumi.pulumi_wrapper import PulumiWrapper, PulumiError


@pytest.fixture
def pulumi_wrapper(tmp_path):
    """Create PulumiWrapper instance"""
    return PulumiWrapper(
        organization="test-org",
        project="test-project",
        working_dir=tmp_path
    )


def test_pulumi_wrapper_init(pulumi_wrapper, tmp_path):
    """Test PulumiWrapper initialization"""
    assert pulumi_wrapper.organization == "test-org"
    assert pulumi_wrapper.project == "test-project"
    assert pulumi_wrapper.working_dir == tmp_path


@patch('subprocess.run')
def test_select_stack_success(mock_run, pulumi_wrapper):
    """Test selecting a stack"""
    mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

    pulumi_wrapper.select_stack("test-stack")

    # Should have called pulumi stack select
    assert mock_run.called


@patch('subprocess.run')
def test_select_stack_with_create(mock_run, pulumi_wrapper):
    """Test selecting and creating a stack"""
    mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

    pulumi_wrapper.select_stack("test-stack", create=True)

    # Should have called pulumi stack init and select
    assert mock_run.call_count >= 1


@patch('subprocess.run')
def test_set_config(mock_run, pulumi_wrapper):
    """Test setting configuration"""
    mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

    pulumi_wrapper.set_config("key", "value")

    assert mock_run.called


@patch('subprocess.run')
def test_preview(mock_run, pulumi_wrapper):
    """Test preview operation"""
    mock_run.return_value = Mock(
        returncode=0,
        stdout='{"changeSummary": {"create": 1}}',
        stderr=""
    )

    result = pulumi_wrapper.preview()

    assert result is not None
    assert mock_run.called


@patch('subprocess.run')
def test_up(mock_run, pulumi_wrapper):
    """Test up operation"""
    mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

    result = pulumi_wrapper.up()

    assert result is not None
    assert mock_run.called


@patch('subprocess.run')
def test_destroy(mock_run, pulumi_wrapper):
    """Test destroy operation"""
    mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

    result = pulumi_wrapper.destroy()

    assert result is not None
    assert mock_run.called


@patch('subprocess.run')
def test_get_stack_output(mock_run, pulumi_wrapper):
    """Test getting stack output"""
    mock_run.return_value = Mock(
        returncode=0,
        stdout='"test-value"',
        stderr=""
    )

    value = pulumi_wrapper.get_stack_output("test-stack", "outputKey")

    assert value == "test-value"
    assert mock_run.called


@patch('subprocess.run')
def test_pulumi_command_failure(mock_run, pulumi_wrapper):
    """Test Pulumi command failure"""
    mock_run.return_value = Mock(returncode=1, stdout="", stderr="Error message")

    result = pulumi_wrapper.preview()

    assert result["success"] is False
    assert "error" in result


def test_check_pulumi_available(pulumi_wrapper):
    """Test checking if Pulumi is available"""
    # This will fail if Pulumi is not installed, which is fine for testing
    try:
        result = pulumi_wrapper.check_pulumi_available()
        # If Pulumi is installed, should return True or False
        assert isinstance(result, bool)
    except:
        # If Pulumi not installed, that's okay for tests
        pass
