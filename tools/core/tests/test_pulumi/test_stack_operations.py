"""Tests for StackOperations"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from cloud_core.pulumi.stack_operations import StackOperations
from cloud_core.pulumi.pulumi_wrapper import PulumiWrapper, PulumiError


@pytest.fixture
def mock_pulumi_wrapper():
    """Create mock PulumiWrapper"""
    return Mock(spec=PulumiWrapper)


@pytest.fixture
def stack_operations(mock_pulumi_wrapper):
    """Create StackOperations instance"""
    return StackOperations(mock_pulumi_wrapper)


def test_stack_operations_init(mock_pulumi_wrapper):
    """Test StackOperations initialization"""
    operations = StackOperations(mock_pulumi_wrapper)
    assert operations.pulumi is mock_pulumi_wrapper


def test_deploy_stack_success(stack_operations, mock_pulumi_wrapper, tmp_path):
    """Test deploying stack successfully"""
    mock_pulumi_wrapper.select_stack.return_value = None
    mock_pulumi_wrapper.set_all_config.return_value = None
    mock_pulumi_wrapper.up.return_value = {"success": True}

    config = {"key": "value"}

    success, error = stack_operations.deploy_stack(
        deployment_id="D1TEST1",
        stack_name="network",
        environment="dev",
        stack_dir=tmp_path,
        config=config
    )

    assert success is True
    assert error is None
    mock_pulumi_wrapper.select_stack.assert_called_once()
    mock_pulumi_wrapper.set_all_config.assert_called_once_with(config, cwd=tmp_path)
    mock_pulumi_wrapper.up.assert_called_once()


def test_deploy_stack_preview_only(stack_operations, mock_pulumi_wrapper, tmp_path):
    """Test deploying stack in preview mode"""
    mock_pulumi_wrapper.select_stack.return_value = None
    mock_pulumi_wrapper.set_all_config.return_value = None
    mock_pulumi_wrapper.preview.return_value = {"success": True}

    success, error = stack_operations.deploy_stack(
        deployment_id="D1TEST1",
        stack_name="network",
        environment="dev",
        stack_dir=tmp_path,
        config={},
        preview_only=True
    )

    assert success is True
    mock_pulumi_wrapper.preview.assert_called_once()
    mock_pulumi_wrapper.up.assert_not_called()


def test_deploy_stack_failure(stack_operations, mock_pulumi_wrapper, tmp_path):
    """Test deploying stack with failure"""
    mock_pulumi_wrapper.select_stack.side_effect = PulumiError("Stack creation failed")

    success, error = stack_operations.deploy_stack(
        deployment_id="D1TEST1",
        stack_name="network",
        environment="dev",
        stack_dir=tmp_path,
        config={}
    )

    assert success is False
    assert error is not None
    assert "Stack creation failed" in error


def test_deploy_stack_up_failure(stack_operations, mock_pulumi_wrapper, tmp_path):
    """Test deploy when up command fails"""
    mock_pulumi_wrapper.select_stack.return_value = None
    mock_pulumi_wrapper.set_all_config.return_value = None
    mock_pulumi_wrapper.up.return_value = {"success": False, "error": "Deploy failed"}

    success, error = stack_operations.deploy_stack(
        deployment_id="D1TEST1",
        stack_name="network",
        environment="dev",
        stack_dir=tmp_path,
        config={}
    )

    assert success is False


def test_destroy_stack_success(stack_operations, mock_pulumi_wrapper, tmp_path):
    """Test destroying stack successfully"""
    mock_pulumi_wrapper.select_stack.return_value = None
    mock_pulumi_wrapper.destroy.return_value = {"success": True}

    success, error = stack_operations.destroy_stack(
        deployment_id="D1TEST1",
        stack_name="network",
        environment="dev",
        stack_dir=tmp_path
    )

    assert success is True
    assert error is None
    mock_pulumi_wrapper.select_stack.assert_called_once()
    mock_pulumi_wrapper.destroy.assert_called_once()


def test_destroy_stack_failure(stack_operations, mock_pulumi_wrapper, tmp_path):
    """Test destroying stack with failure"""
    mock_pulumi_wrapper.select_stack.side_effect = PulumiError("Stack not found")

    success, error = stack_operations.destroy_stack(
        deployment_id="D1TEST1",
        stack_name="network",
        environment="dev",
        stack_dir=tmp_path
    )

    assert success is False
    assert error is not None
    assert "Stack not found" in error


def test_refresh_stack_success(stack_operations, mock_pulumi_wrapper, tmp_path):
    """Test refreshing stack successfully"""
    mock_pulumi_wrapper.select_stack.return_value = None
    mock_pulumi_wrapper.refresh.return_value = {"success": True}

    success, error = stack_operations.refresh_stack(
        deployment_id="D1TEST1",
        stack_name="network",
        environment="dev",
        stack_dir=tmp_path
    )

    assert success is True
    assert error is None
    mock_pulumi_wrapper.select_stack.assert_called_once()
    mock_pulumi_wrapper.refresh.assert_called_once()


def test_refresh_stack_failure(stack_operations, mock_pulumi_wrapper, tmp_path):
    """Test refreshing stack with failure"""
    mock_pulumi_wrapper.select_stack.side_effect = PulumiError("Refresh failed")

    success, error = stack_operations.refresh_stack(
        deployment_id="D1TEST1",
        stack_name="network",
        environment="dev",
        stack_dir=tmp_path
    )

    assert success is False
    assert error is not None


def test_stack_name_formatting(stack_operations, mock_pulumi_wrapper, tmp_path):
    """Test that Pulumi stack name is correctly formatted"""
    mock_pulumi_wrapper.select_stack.return_value = None
    mock_pulumi_wrapper.set_all_config.return_value = None
    mock_pulumi_wrapper.up.return_value = {"success": True}

    stack_operations.deploy_stack(
        deployment_id="D1TEST1",
        stack_name="network",
        environment="dev",
        stack_dir=tmp_path,
        config={}
    )

    # Check that select_stack was called with correct name format
    call_args = mock_pulumi_wrapper.select_stack.call_args
    stack_name = call_args[0][0]
    assert stack_name == "D1TEST1-network-dev"


def test_deploy_with_empty_config(stack_operations, mock_pulumi_wrapper, tmp_path):
    """Test deploying with empty config"""
    mock_pulumi_wrapper.select_stack.return_value = None
    mock_pulumi_wrapper.set_all_config.return_value = None
    mock_pulumi_wrapper.up.return_value = {"success": True}

    success, error = stack_operations.deploy_stack(
        deployment_id="D1TEST1",
        stack_name="network",
        environment="dev",
        stack_dir=tmp_path,
        config={}
    )

    assert success is True
    mock_pulumi_wrapper.set_all_config.assert_called_once_with({}, cwd=tmp_path)


def test_deploy_creates_stack_if_not_exists(stack_operations, mock_pulumi_wrapper, tmp_path):
    """Test that deploy creates stack if it doesn't exist"""
    mock_pulumi_wrapper.select_stack.return_value = None
    mock_pulumi_wrapper.set_all_config.return_value = None
    mock_pulumi_wrapper.up.return_value = {"success": True}

    stack_operations.deploy_stack(
        deployment_id="D1TEST1",
        stack_name="network",
        environment="dev",
        stack_dir=tmp_path,
        config={}
    )

    # Check that select_stack was called with create=True
    call_args = mock_pulumi_wrapper.select_stack.call_args
    assert call_args[1]["create"] is True


def test_destroy_doesnt_create_stack(stack_operations, mock_pulumi_wrapper, tmp_path):
    """Test that destroy doesn't create stack"""
    mock_pulumi_wrapper.select_stack.return_value = None
    mock_pulumi_wrapper.destroy.return_value = {"success": True}

    stack_operations.destroy_stack(
        deployment_id="D1TEST1",
        stack_name="network",
        environment="dev",
        stack_dir=tmp_path
    )

    # Check that select_stack was called with create=False
    call_args = mock_pulumi_wrapper.select_stack.call_args
    assert call_args[1]["create"] is False


def test_preview_returns_error_on_failure(stack_operations, mock_pulumi_wrapper, tmp_path):
    """Test preview mode returns error on failure"""
    mock_pulumi_wrapper.select_stack.return_value = None
    mock_pulumi_wrapper.set_all_config.return_value = None
    mock_pulumi_wrapper.preview.return_value = {
        "success": False,
        "error": "Preview failed"
    }

    success, error = stack_operations.deploy_stack(
        deployment_id="D1TEST1",
        stack_name="network",
        environment="dev",
        stack_dir=tmp_path,
        config={},
        preview_only=True
    )

    assert success is False
    assert error == "Preview failed"
