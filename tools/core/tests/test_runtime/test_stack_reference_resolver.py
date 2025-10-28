"""Tests for StackReferenceResolver"""

import pytest
from unittest.mock import Mock
from cloud_core.runtime.stack_reference_resolver import (
    StackReferenceResolver,
    create_resolver_with_pulumi,
)


def test_stack_reference_resolver_init():
    """Test StackReferenceResolver initialization"""
    resolver = StackReferenceResolver(
        deployment_id="D1TEST1",
        environment="dev",
        organization="TestOrg",
        project="test-project"
    )

    assert resolver.deployment_id == "D1TEST1"
    assert resolver.environment == "dev"
    assert resolver.organization == "TestOrg"
    assert resolver.project == "test-project"
    assert resolver.cache == {}
    assert resolver.pulumi_query_func is None


def test_set_pulumi_query_func():
    """Test setting Pulumi query function"""
    resolver = StackReferenceResolver("D1TEST1", "dev", "TestOrg", "test-project")

    def mock_query(stack_name: str, output_key: str):
        return {"vpcId": "vpc-12345"}

    resolver.set_pulumi_query_func(mock_query)

    assert resolver.pulumi_query_func is not None


def test_resolve_stack_reference():
    """Test resolving stack reference"""
    resolver = StackReferenceResolver("D1TEST1", "dev", "TestOrg", "test-project")

    def mock_query(stack_name: str, output_key: str):
        return {"vpcId": "vpc-12345"}

    resolver.set_pulumi_query_func(mock_query)

    result = resolver.resolve("stack.network.vpcId")

    assert result == "vpc-12345"


def test_resolve_invalid_format():
    """Test resolving invalid placeholder format"""
    resolver = StackReferenceResolver("D1TEST1", "dev", "TestOrg", "test-project")

    result = resolver.resolve("invalid.format")

    assert result is None


def test_resolve_incomplete_format():
    """Test resolving incomplete stack reference"""
    resolver = StackReferenceResolver("D1TEST1", "dev", "TestOrg", "test-project")

    result = resolver.resolve("stack.network")

    assert result is None


def test_resolve_without_query_func():
    """Test resolving without query function configured"""
    resolver = StackReferenceResolver("D1TEST1", "dev", "TestOrg", "test-project")

    result = resolver.resolve("stack.network.vpcId")

    assert result is None


def test_resolve_with_error():
    """Test resolving when query function raises error"""
    resolver = StackReferenceResolver("D1TEST1", "dev", "TestOrg", "test-project")

    def mock_query(stack_name: str, output_key: str):
        raise Exception("Query failed")

    resolver.set_pulumi_query_func(mock_query)

    result = resolver.resolve("stack.network.vpcId")

    assert result is None


def test_resolve_caching():
    """Test that resolved values are cached"""
    resolver = StackReferenceResolver("D1TEST1", "dev", "TestOrg", "test-project")

    call_count = {"count": 0}

    def mock_query(stack_name: str, output_key: str):
        call_count["count"] += 1
        return {"vpcId": "vpc-12345"}

    resolver.set_pulumi_query_func(mock_query)

    # First call
    result1 = resolver.resolve("stack.network.vpcId")

    # Second call should use cache
    result2 = resolver.resolve("stack.network.vpcId")

    assert result1 == result2
    assert call_count["count"] == 1  # Only called once due to caching


def test_clear_cache():
    """Test clearing cache"""
    resolver = StackReferenceResolver("D1TEST1", "dev", "TestOrg", "test-project")
    resolver.cache["test.key"] = "test.value"

    assert len(resolver.cache) > 0

    resolver.clear_cache()

    assert len(resolver.cache) == 0


def test_resolve_all_from_stack():
    """Test resolving all outputs from a stack"""
    resolver = StackReferenceResolver("D1TEST1", "dev", "TestOrg", "test-project")

    def mock_query(stack_name: str, output_key: str):
        if output_key is None:
            return {"vpcId": "vpc-12345", "subnetId": "subnet-67890"}
        return {}

    resolver.set_pulumi_query_func(mock_query)

    outputs = resolver.resolve_all_from_stack("network")

    assert outputs["vpcId"] == "vpc-12345"
    assert outputs["subnetId"] == "subnet-67890"


def test_resolve_all_without_query_func():
    """Test resolving all outputs without query function"""
    resolver = StackReferenceResolver("D1TEST1", "dev", "TestOrg", "test-project")

    outputs = resolver.resolve_all_from_stack("network")

    assert outputs == {}


def test_resolve_all_with_error():
    """Test resolving all outputs with error"""
    resolver = StackReferenceResolver("D1TEST1", "dev", "TestOrg", "test-project")

    def mock_query(stack_name: str, output_key: str):
        raise Exception("Query failed")

    resolver.set_pulumi_query_func(mock_query)

    outputs = resolver.resolve_all_from_stack("network")

    assert outputs == {}


def test_preload_stack_outputs():
    """Test preloading stack outputs into cache"""
    resolver = StackReferenceResolver("D1TEST1", "dev", "TestOrg", "test-project")

    def mock_query(stack_name: str, output_key: str):
        if output_key is None:
            return {"vpcId": "vpc-12345", "subnetId": "subnet-67890"}
        return {}

    resolver.set_pulumi_query_func(mock_query)

    count = resolver.preload_stack_outputs("network")

    assert count == 2
    assert resolver.cache["stack.network.vpcId"] == "vpc-12345"
    assert resolver.cache["stack.network.subnetId"] == "subnet-67890"


def test_get_stack_name_from_placeholder():
    """Test extracting stack name from placeholder"""
    resolver = StackReferenceResolver("D1TEST1", "dev", "TestOrg", "test-project")

    stack_name = resolver.get_stack_name_from_placeholder("stack.network.vpcId")

    assert stack_name == "network"


def test_get_stack_name_invalid_placeholder():
    """Test extracting stack name from invalid placeholder"""
    resolver = StackReferenceResolver("D1TEST1", "dev", "TestOrg", "test-project")

    stack_name = resolver.get_stack_name_from_placeholder("invalid.placeholder")

    assert stack_name is None


def test_is_stack_reference():
    """Test checking if placeholder is stack reference"""
    resolver = StackReferenceResolver("D1TEST1", "dev", "TestOrg", "test-project")

    assert resolver.is_stack_reference("stack.network.vpcId")
    assert resolver.is_stack_reference("stack.security.sgId")
    assert not resolver.is_stack_reference("deployment.id")
    assert not resolver.is_stack_reference("stack.network")


def test_pulumi_stack_name_format():
    """Test that Pulumi stack name is correctly formatted"""
    resolver = StackReferenceResolver("D1TEST1", "dev", "TestOrg", "test-project")

    expected_stack_name = "TestOrg/test-project/D1TEST1-network-dev"

    captured_stack_name = None

    def mock_query(stack_name: str, output_key: str):
        nonlocal captured_stack_name
        captured_stack_name = stack_name
        return {"vpcId": "vpc-12345"}

    resolver.set_pulumi_query_func(mock_query)
    resolver.resolve("stack.network.vpcId")

    assert captured_stack_name == expected_stack_name


def test_resolve_multiple_stacks():
    """Test resolving outputs from multiple stacks"""
    resolver = StackReferenceResolver("D1TEST1", "dev", "TestOrg", "test-project")

    def mock_query(stack_name: str, output_key: str):
        if "network" in stack_name:
            return {"vpcId": "vpc-12345"}
        elif "security" in stack_name:
            return {"sgId": "sg-67890"}
        return {}

    resolver.set_pulumi_query_func(mock_query)

    vpc_id = resolver.resolve("stack.network.vpcId")
    sg_id = resolver.resolve("stack.security.sgId")

    assert vpc_id == "vpc-12345"
    assert sg_id == "sg-67890"


def test_create_resolver_with_pulumi():
    """Test creating resolver with Pulumi wrapper"""
    mock_pulumi_wrapper = Mock()
    mock_pulumi_wrapper.get_stack_output.return_value = "vpc-12345"

    resolver = create_resolver_with_pulumi(
        deployment_id="D1TEST1",
        environment="dev",
        organization="TestOrg",
        project="test-project",
        pulumi_wrapper=mock_pulumi_wrapper
    )

    assert resolver.pulumi_query_func is not None

    result = resolver.resolve("stack.network.vpcId")

    assert result == "vpc-12345"
    mock_pulumi_wrapper.get_stack_output.assert_called_once()


def test_create_resolver_with_pulumi_all_outputs():
    """Test creating resolver with Pulumi wrapper for all outputs"""
    mock_pulumi_wrapper = Mock()
    mock_pulumi_wrapper.get_all_stack_outputs.return_value = {
        "vpcId": "vpc-12345",
        "subnetId": "subnet-67890"
    }

    resolver = create_resolver_with_pulumi(
        deployment_id="D1TEST1",
        environment="dev",
        organization="TestOrg",
        project="test-project",
        pulumi_wrapper=mock_pulumi_wrapper
    )

    outputs = resolver.resolve_all_from_stack("network")

    assert outputs["vpcId"] == "vpc-12345"
    assert outputs["subnetId"] == "subnet-67890"


def test_create_resolver_with_pulumi_error_handling():
    """Test error handling in created resolver"""
    mock_pulumi_wrapper = Mock()
    mock_pulumi_wrapper.get_stack_output.side_effect = Exception("Pulumi error")

    resolver = create_resolver_with_pulumi(
        deployment_id="D1TEST1",
        environment="dev",
        organization="TestOrg",
        project="test-project",
        pulumi_wrapper=mock_pulumi_wrapper
    )

    result = resolver.resolve("stack.network.vpcId")

    assert result is None


def test_resolve_with_empty_output():
    """Test resolving when output is empty"""
    resolver = StackReferenceResolver("D1TEST1", "dev", "TestOrg", "test-project")

    def mock_query(stack_name: str, output_key: str):
        return {}

    resolver.set_pulumi_query_func(mock_query)

    result = resolver.resolve("stack.network.vpcId")

    assert result is None


def test_resolve_with_none_output():
    """Test resolving when output returns None"""
    resolver = StackReferenceResolver("D1TEST1", "dev", "TestOrg", "test-project")

    def mock_query(stack_name: str, output_key: str):
        return None

    resolver.set_pulumi_query_func(mock_query)

    result = resolver.resolve("stack.network.vpcId")

    assert result is None


def test_cache_isolation():
    """Test that cache is isolated per instance"""
    resolver1 = StackReferenceResolver("D1TEST1", "dev", "TestOrg", "test-project")
    resolver2 = StackReferenceResolver("D1TEST2", "dev", "TestOrg", "test-project")

    resolver1.cache["test"] = "value1"
    resolver2.cache["test"] = "value2"

    assert resolver1.cache["test"] == "value1"
    assert resolver2.cache["test"] == "value2"


def test_preload_empty_stack():
    """Test preloading from stack with no outputs"""
    resolver = StackReferenceResolver("D1TEST1", "dev", "TestOrg", "test-project")

    def mock_query(stack_name: str, output_key: str):
        return {}

    resolver.set_pulumi_query_func(mock_query)

    count = resolver.preload_stack_outputs("network")

    assert count == 0
    assert len(resolver.cache) == 0
