"""Tests for StateManager"""

import pytest
from pathlib import Path
from cloud_core.deployment.state_manager import (
    StateManager,
    DeploymentStatus,
    StackStatus,
)


@pytest.fixture
def temp_deployment_dir(tmp_path):
    """Create temporary deployment directory"""
    deployment_dir = tmp_path / "deployment-test"
    deployment_dir.mkdir()
    return deployment_dir


def test_state_manager_init(temp_deployment_dir):
    """Test StateManager initialization"""
    manager = StateManager(temp_deployment_dir)
    assert manager.deployment_dir == temp_deployment_dir
    assert manager.state_file.exists()


def test_state_manager_load_state(temp_deployment_dir):
    """Test loading state"""
    manager = StateManager(temp_deployment_dir)
    state = manager.load_state()

    assert state is not None
    assert "deployment_status" in state
    assert state["deployment_status"] == DeploymentStatus.INITIALIZED.value


def test_state_manager_set_deployment_status(temp_deployment_dir):
    """Test setting deployment status"""
    manager = StateManager(temp_deployment_dir)

    manager.set_deployment_status(DeploymentStatus.DEPLOYING)
    status = manager.get_deployment_status()

    assert status == DeploymentStatus.DEPLOYING


def test_state_manager_set_stack_status(temp_deployment_dir):
    """Test setting stack status"""
    manager = StateManager(temp_deployment_dir)

    manager.set_stack_status("network", StackStatus.DEPLOYED, "dev")
    status = manager.get_stack_status("network", "dev")

    assert status == StackStatus.DEPLOYED


def test_state_manager_get_all_stack_statuses(temp_deployment_dir):
    """Test getting all stack statuses"""
    manager = StateManager(temp_deployment_dir)

    # Set some statuses
    manager.set_stack_status("network", StackStatus.DEPLOYED, "dev")
    manager.set_stack_status("security", StackStatus.DEPLOYING, "dev")

    statuses = manager.get_all_stack_statuses("dev")

    assert statuses["network"] == StackStatus.DEPLOYED
    assert statuses["security"] == StackStatus.DEPLOYING


def test_state_manager_record_operation(temp_deployment_dir):
    """Test recording operation"""
    manager = StateManager(temp_deployment_dir)

    manager.record_operation(
        operation_type="deploy",
        status="success",
        details={"message": "Deployed successfully", "stack_name": "network", "environment": "dev"}
    )

    history = manager.get_operation_history(limit=1)

    assert len(history) == 1
    assert history[0]["operation"] == "deploy"
    assert history[0]["status"] == "success"


def test_state_manager_start_complete_operation(temp_deployment_dir):
    """Test start and complete operation"""
    manager = StateManager(temp_deployment_dir)

    # Start operation
    manager.start_operation(
        operation_type="deploy",
        details={"stack_name": "network", "environment": "dev"}
    )

    assert manager.is_operation_in_progress()

    # Complete operation
    manager.complete_operation(
        success=True,
        details={"message": "Done"}
    )

    assert not manager.is_operation_in_progress()


def test_state_manager_deployment_summary(temp_deployment_dir):
    """Test getting deployment summary"""
    manager = StateManager(temp_deployment_dir)

    # Set some states
    manager.set_deployment_status(DeploymentStatus.DEPLOYED)
    manager.set_stack_status("network", StackStatus.DEPLOYED, "dev")
    manager.set_stack_status("security", StackStatus.DEPLOYED, "dev")

    summary = manager.get_deployment_summary("dev")

    assert summary["deployment_status"] == DeploymentStatus.DEPLOYED.value
    assert summary["total_stacks"] == 2
    assert summary["deployed_stacks"] == 2


def test_state_manager_get_current_operation(temp_deployment_dir):
    """Test getting current operation"""
    manager = StateManager(temp_deployment_dir)

    # Start operation
    manager.start_operation("deploy", {"stack": "network"})

    current = manager.get_current_operation()

    assert current is not None
    assert current["type"] == "deploy"
    assert "started_at" in current


def test_state_manager_no_current_operation(temp_deployment_dir):
    """Test when no operation in progress"""
    manager = StateManager(temp_deployment_dir)

    assert not manager.is_operation_in_progress()
    assert manager.get_current_operation() is None


def test_state_manager_multiple_operations(temp_deployment_dir):
    """Test recording multiple operations"""
    manager = StateManager(temp_deployment_dir)

    manager.record_operation("deploy", "started")
    manager.record_operation("deploy", "completed")
    manager.record_operation("destroy", "started")

    history = manager.get_operation_history(limit=10)

    assert len(history) == 3
    # Should be in reverse chronological order
    assert history[0]["operation"] == "destroy"
    assert history[1]["operation"] == "deploy"
    assert history[2]["operation"] == "deploy"


def test_state_manager_get_stack_status_not_found(temp_deployment_dir):
    """Test getting status for non-existent stack"""
    manager = StateManager(temp_deployment_dir)

    status = manager.get_stack_status("nonexistent", "dev")

    assert status == StackStatus.NOT_DEPLOYED


def test_state_manager_update_stack_status(temp_deployment_dir):
    """Test updating stack status"""
    manager = StateManager(temp_deployment_dir)

    # Set initial status
    manager.set_stack_status("network", StackStatus.DEPLOYING, "dev")
    assert manager.get_stack_status("network", "dev") == StackStatus.DEPLOYING

    # Update status
    manager.set_stack_status("network", StackStatus.DEPLOYED, "dev")
    assert manager.get_stack_status("network", "dev") == StackStatus.DEPLOYED


def test_state_manager_multiple_environments(temp_deployment_dir):
    """Test managing multiple environments"""
    manager = StateManager(temp_deployment_dir)

    manager.set_stack_status("network", StackStatus.DEPLOYED, "dev")
    manager.set_stack_status("network", StackStatus.DEPLOYING, "prod")

    assert manager.get_stack_status("network", "dev") == StackStatus.DEPLOYED
    assert manager.get_stack_status("network", "prod") == StackStatus.DEPLOYING


def test_state_manager_summary_with_mixed_statuses(temp_deployment_dir):
    """Test summary with mixed stack statuses"""
    manager = StateManager(temp_deployment_dir)

    manager.set_stack_status("network", StackStatus.DEPLOYED, "dev")
    manager.set_stack_status("security", StackStatus.DEPLOYING, "dev")
    manager.set_stack_status("app", StackStatus.FAILED, "dev")

    summary = manager.get_deployment_summary("dev")

    assert summary["total_stacks"] == 3
    assert summary["deployed_stacks"] == 1


def test_state_manager_operation_with_details(temp_deployment_dir):
    """Test recording operation with details"""
    manager = StateManager(temp_deployment_dir)

    details = {
        "stack_name": "network",
        "duration": 120,
        "resources_created": 5
    }

    manager.record_operation("deploy", "completed", details)

    history = manager.get_operation_history(limit=1)

    assert history[0]["details"]["stack_name"] == "network"
    assert history[0]["details"]["duration"] == 120


def test_state_manager_complete_operation_failure(temp_deployment_dir):
    """Test completing operation with failure"""
    manager = StateManager(temp_deployment_dir)

    manager.start_operation("deploy")
    manager.complete_operation(success=False, details={"error": "Deployment failed"})

    history = manager.get_operation_history(limit=1)

    assert history[0]["status"] == "failed"
    assert history[0]["details"]["error"] == "Deployment failed"


def test_state_manager_empty_operation_history(temp_deployment_dir):
    """Test getting history when no operations recorded"""
    manager = StateManager(temp_deployment_dir)

    history = manager.get_operation_history()

    assert history == []


def test_state_manager_history_limit(temp_deployment_dir):
    """Test operation history limit"""
    manager = StateManager(temp_deployment_dir)

    # Record more than limit
    for i in range(10):
        manager.record_operation(f"operation_{i}", "completed")

    history = manager.get_operation_history(limit=5)

    assert len(history) == 5


def test_state_manager_get_all_stacks_empty(temp_deployment_dir):
    """Test getting all stacks when none exist"""
    manager = StateManager(temp_deployment_dir)

    statuses = manager.get_all_stack_statuses("dev")

    assert statuses == {}
