"""Tests for StateQueries"""

import pytest
from unittest.mock import Mock, MagicMock
from cloud_core.pulumi.state_queries import StateQueries
from cloud_core.pulumi.pulumi_wrapper import PulumiWrapper


@pytest.fixture
def mock_pulumi_wrapper():
    """Create mock PulumiWrapper"""
    wrapper = Mock(spec=PulumiWrapper)
    wrapper.organization = "TestOrg"
    wrapper.project = "test-project"
    wrapper.get_stack_output = MagicMock(return_value="test-value")
    wrapper.get_all_stack_outputs = MagicMock(return_value={"key1": "value1", "key2": "value2"})
    return wrapper


@pytest.fixture
def state_queries(mock_pulumi_wrapper):
    """Create StateQueries instance"""
    return StateQueries(mock_pulumi_wrapper)


def test_state_queries_init(mock_pulumi_wrapper):
    """Test StateQueries initialization"""
    queries = StateQueries(mock_pulumi_wrapper)
    assert queries.pulumi == mock_pulumi_wrapper


def test_get_output(state_queries, mock_pulumi_wrapper):
    """Test getting specific output from stack"""
    result = state_queries.get_output(
        deployment_id="D1TEST1",
        stack_name="network",
        environment="dev",
        output_key="vpcId"
    )

    assert result == "test-value"
    mock_pulumi_wrapper.get_stack_output.assert_called_once_with(
        "TestOrg/test-project/D1TEST1-network-dev",
        "vpcId"
    )


def test_get_output_not_found(state_queries, mock_pulumi_wrapper):
    """Test getting output that doesn't exist"""
    mock_pulumi_wrapper.get_stack_output.return_value = None

    result = state_queries.get_output(
        deployment_id="D1TEST1",
        stack_name="network",
        environment="dev",
        output_key="nonexistent"
    )

    assert result is None


def test_get_all_outputs(state_queries, mock_pulumi_wrapper):
    """Test getting all outputs from stack"""
    result = state_queries.get_all_outputs(
        deployment_id="D1TEST1",
        stack_name="network",
        environment="dev"
    )

    assert result == {"key1": "value1", "key2": "value2"}
    mock_pulumi_wrapper.get_all_stack_outputs.assert_called_once_with(
        "TestOrg/test-project/D1TEST1-network-dev"
    )


def test_get_all_outputs_empty(state_queries, mock_pulumi_wrapper):
    """Test getting outputs from stack with no outputs"""
    mock_pulumi_wrapper.get_all_stack_outputs.return_value = {}

    result = state_queries.get_all_outputs(
        deployment_id="D1TEST1",
        stack_name="network",
        environment="dev"
    )

    assert result == {}


def test_full_stack_name_format(state_queries, mock_pulumi_wrapper):
    """Test that full stack name is formatted correctly"""
    state_queries.get_output(
        deployment_id="D2PROD9",
        stack_name="database",
        environment="production",
        output_key="endpoint"
    )

    # Verify the full stack name format
    call_args = mock_pulumi_wrapper.get_stack_output.call_args[0]
    assert call_args[0] == "TestOrg/test-project/D2PROD9-database-production"


def test_multiple_environments(state_queries, mock_pulumi_wrapper):
    """Test querying outputs from multiple environments"""
    # Query dev environment
    state_queries.get_output("D1TEST1", "network", "dev", "vpcId")

    # Query prod environment
    state_queries.get_output("D1TEST1", "network", "prod", "vpcId")

    # Verify both were called with correct stack names
    calls = mock_pulumi_wrapper.get_stack_output.call_args_list
    assert calls[0][0][0] == "TestOrg/test-project/D1TEST1-network-dev"
    assert calls[1][0][0] == "TestOrg/test-project/D1TEST1-network-prod"


def test_multiple_stacks(state_queries, mock_pulumi_wrapper):
    """Test querying outputs from multiple stacks"""
    # Query network stack
    state_queries.get_output("D1TEST1", "network", "dev", "vpcId")

    # Query database stack
    state_queries.get_output("D1TEST1", "database", "dev", "endpoint")

    # Verify both were called with correct stack names
    calls = mock_pulumi_wrapper.get_stack_output.call_args_list
    assert calls[0][0][0] == "TestOrg/test-project/D1TEST1-network-dev"
    assert calls[1][0][0] == "TestOrg/test-project/D1TEST1-database-dev"
