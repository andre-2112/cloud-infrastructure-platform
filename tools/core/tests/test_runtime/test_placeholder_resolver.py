"""Tests for PlaceholderResolver"""

import pytest
from cloud_core.runtime.placeholder_resolver import (
    PlaceholderResolver,
    create_deployment_resolver,
)


def test_placeholder_resolver_init():
    """Test PlaceholderResolver initialization"""
    resolver = PlaceholderResolver()
    assert resolver is not None
    assert isinstance(resolver.resolvers, dict)
    assert isinstance(resolver.cache, dict)


def test_register_resolver():
    """Test registering a resolver"""
    resolver = PlaceholderResolver()

    def custom_resolver(placeholder: str):
        return "test-value"

    resolver.register_resolver("custom", custom_resolver)

    assert "custom" in resolver.resolvers


def test_resolve_string_with_placeholder():
    """Test resolving string with placeholder"""
    resolver = PlaceholderResolver()

    def test_resolver(placeholder: str):
        if placeholder == "deployment.id":
            return "D1TEST1"
        return None

    resolver.register_resolver("deployment", test_resolver)

    result = resolver.resolve("Deploy {{deployment.id}} now")

    assert result == "Deploy D1TEST1 now"


def test_resolve_dict_with_placeholders():
    """Test resolving dict with placeholders"""
    resolver = PlaceholderResolver()

    def test_resolver(placeholder: str):
        if placeholder == "deployment.id":
            return "D1TEST1"
        return None

    resolver.register_resolver("deployment", test_resolver)

    data = {
        "name": "{{deployment.id}}-network",
        "region": "us-east-1"
    }

    result = resolver.resolve(data)

    assert result["name"] == "D1TEST1-network"
    assert result["region"] == "us-east-1"


def test_resolve_list_with_placeholders():
    """Test resolving list with placeholders"""
    resolver = PlaceholderResolver()

    def test_resolver(placeholder: str):
        if placeholder == "deployment.id":
            return "D1TEST1"
        return None

    resolver.register_resolver("deployment", test_resolver)

    data = ["{{deployment.id}}", "static-value"]

    result = resolver.resolve(data)

    assert result[0] == "D1TEST1"
    assert result[1] == "static-value"


def test_has_placeholders():
    """Test checking if value has placeholders"""
    resolver = PlaceholderResolver()

    assert resolver.has_placeholders("{{test.value}}")
    assert resolver.has_placeholders({"key": "{{test.value}}"})
    assert not resolver.has_placeholders("no placeholders here")


def test_get_placeholders():
    """Test getting all placeholders from value"""
    resolver = PlaceholderResolver()

    text = "{{deployment.id}} and {{stack.network.vpcId}}"
    placeholders = resolver.get_placeholders(text)

    assert "deployment.id" in placeholders
    assert "stack.network.vpcId" in placeholders


def test_cache():
    """Test placeholder caching"""
    resolver = PlaceholderResolver()
    call_count = {"count": 0}

    def counting_resolver(placeholder: str):
        call_count["count"] += 1
        return "cached-value"

    resolver.register_resolver("test", counting_resolver)

    # Resolve twice
    resolver.resolve("{{test.value}}")
    resolver.resolve("{{test.value}}")

    # Should only call resolver once due to caching
    assert call_count["count"] == 1


def test_clear_cache():
    """Test clearing cache"""
    resolver = PlaceholderResolver()

    def test_resolver(placeholder: str):
        return "value"

    resolver.register_resolver("test", test_resolver)

    resolver.resolve("{{test.value}}")
    assert len(resolver.cache) > 0

    resolver.clear_cache()
    assert len(resolver.cache) == 0


def test_strict_mode():
    """Test strict mode"""
    resolver = PlaceholderResolver()
    resolver.set_strict_mode(True)

    with pytest.raises(ValueError):
        resolver.resolve("{{unresolved.placeholder}}")


def test_create_deployment_resolver():
    """Test creating deployment resolver"""
    # The deployment_context should be flat, not nested
    deployment_context = {
        "id": "D1TEST1",
        "org": "TestOrg",
        "project": "test-project",
        "environment": "dev"
    }

    resolver = create_deployment_resolver(deployment_context)

    result = resolver.resolve("{{deployment.id}}")
    assert result == "D1TEST1"

    result = resolver.resolve("{{deployment.org}}")
    assert result == "TestOrg"


def test_resolve_primitive_values():
    """Test resolving primitive values (non-string, non-dict, non-list)"""
    resolver = PlaceholderResolver()

    # Test integer
    assert resolver.resolve(42) == 42

    # Test float
    assert resolver.resolve(3.14) == 3.14

    # Test boolean
    assert resolver.resolve(True) is True

    # Test None
    assert resolver.resolve(None) is None


def test_unresolved_placeholder_non_strict():
    """Test unresolved placeholder in non-strict mode"""
    resolver = PlaceholderResolver()
    resolver.set_strict_mode(False)

    # Unresolved placeholder should be left as-is
    result = resolver.resolve("{{unresolved.placeholder}}")
    assert result == "{{unresolved.placeholder}}"


def test_context_simple_lookup():
    """Test simple context lookup without nesting"""
    resolver = PlaceholderResolver()
    context = {"simple.key": "simple-value"}

    result = resolver.resolve("{{simple.key}}", context)
    assert result == "simple-value"


def test_context_nested_lookup():
    """Test nested context lookup"""
    resolver = PlaceholderResolver()
    context = {
        "deployment": {
            "id": "D1TEST1",
            "config": {
                "region": "us-east-1"
            }
        }
    }

    result = resolver.resolve("{{deployment.id}}", context)
    assert result == "D1TEST1"

    result = resolver.resolve("{{deployment.config.region}}", context)
    assert result == "us-east-1"


def test_resolver_exception_handling():
    """Test resolver that raises exception"""
    resolver = PlaceholderResolver()

    def failing_resolver(placeholder: str):
        raise ValueError("Resolver error")

    resolver.register_resolver("failing", failing_resolver)

    # Should not raise, should return None and leave placeholder unresolved
    result = resolver.resolve("{{failing.test}}")
    assert result == "{{failing.test}}"


def test_nested_value_extraction():
    """Test _get_nested_value method"""
    resolver = PlaceholderResolver()

    data = {
        "level1": {
            "level2": {
                "level3": "deep-value"
            }
        }
    }

    # Test nested access
    value = resolver._get_nested_value(data, "level1.level2.level3")
    assert value == "deep-value"

    # Test partial path
    value = resolver._get_nested_value(data, "level1.level2")
    assert value == {"level3": "deep-value"}

    # Test non-existent path
    value = resolver._get_nested_value(data, "level1.nonexistent.level3")
    assert value is None


def test_has_placeholders_list():
    """Test has_placeholders with list"""
    resolver = PlaceholderResolver()

    # List with placeholder
    assert resolver.has_placeholders(["{{test.value}}", "static"])

    # List without placeholder
    assert not resolver.has_placeholders(["static1", "static2"])

    # Nested list
    assert resolver.has_placeholders([["{{test.value}}"]])


def test_get_placeholders_from_dict():
    """Test get_placeholders from dict"""
    resolver = PlaceholderResolver()

    data = {
        "key1": "{{deployment.id}}",
        "key2": "{{stack.network.vpcId}}",
        "key3": "static"
    }

    placeholders = resolver.get_placeholders(data)

    assert "deployment.id" in placeholders
    assert "stack.network.vpcId" in placeholders
    assert len(placeholders) == 2


def test_get_placeholders_from_list():
    """Test get_placeholders from list"""
    resolver = PlaceholderResolver()

    data = [
        "{{deployment.id}}",
        "{{stack.network.vpcId}}",
        "static"
    ]

    placeholders = resolver.get_placeholders(data)

    assert "deployment.id" in placeholders
    assert "stack.network.vpcId" in placeholders
    assert len(placeholders) == 2


def test_get_placeholders_duplicates():
    """Test get_placeholders removes duplicates"""
    resolver = PlaceholderResolver()

    data = {
        "key1": "{{deployment.id}}",
        "key2": "{{deployment.id}}",  # Duplicate
        "key3": "{{deployment.id}}"   # Duplicate
    }

    placeholders = resolver.get_placeholders(data)

    assert placeholders == ["deployment.id"]


def test_deployment_resolver_invalid_prefix():
    """Test deployment resolver with invalid prefix"""
    deployment_context = {
        "id": "D1TEST1",
        "org": "TestOrg"
    }

    resolver = create_deployment_resolver(deployment_context)

    # Try to resolve non-deployment placeholder with deployment resolver
    result = resolver.resolve("{{other.value}}")
    assert result == "{{other.value}}"


def test_env_resolver():
    """Test env resolver from create_deployment_resolver"""
    deployment_context = {
        "region": "us-east-1",
        "account_id": "123456789012"
    }

    resolver = create_deployment_resolver(deployment_context)

    # Test env resolver
    result = resolver.resolve("{{env.region}}")
    assert result == "us-east-1"

    result = resolver.resolve("{{env.account_id}}")
    assert result == "123456789012"


def test_env_resolver_not_found():
    """Test env resolver with non-existent key"""
    deployment_context = {
        "region": "us-east-1"
    }

    resolver = create_deployment_resolver(deployment_context)

    # Non-existent env key
    result = resolver.resolve("{{env.nonexistent}}")
    assert result == "{{env.nonexistent}}"


def test_complex_nested_resolution():
    """Test complex nested dict and list resolution"""
    resolver = PlaceholderResolver()

    def test_resolver(placeholder: str):
        if placeholder == "test.value":
            return "resolved"
        return None

    resolver.register_resolver("test", test_resolver)

    data = {
        "nested": {
            "list": [
                {"key": "{{test.value}}"},
                "{{test.value}}"
            ]
        }
    }

    result = resolver.resolve(data)

    assert result["nested"]["list"][0]["key"] == "resolved"
    assert result["nested"]["list"][1] == "resolved"


def test_dollar_brace_syntax():
    """Test ${...} placeholder syntax"""
    resolver = PlaceholderResolver()

    def test_resolver(placeholder: str):
        if placeholder == "deployment.id":
            return "D1TEST1"
        return None

    resolver.register_resolver("deployment", test_resolver)

    result = resolver.resolve("Deploy ${deployment.id} now")

    assert result == "Deploy D1TEST1 now"


def test_mixed_placeholder_syntaxes():
    """Test mixing {{...}} and ${...} syntaxes"""
    resolver = PlaceholderResolver()

    def test_resolver(placeholder: str):
        if placeholder == "deployment.id":
            return "D1TEST1"
        elif placeholder == "stack.network.vpcId":
            return "vpc-12345"
        return None

    resolver.register_resolver("deployment", test_resolver)
    resolver.register_resolver("stack", test_resolver)

    result = resolver.resolve("Deploy {{deployment.id}} with ${stack.network.vpcId}")

    assert result == "Deploy D1TEST1 with vpc-12345"


def test_dollar_brace_in_dict():
    """Test ${...} syntax in dict"""
    resolver = PlaceholderResolver()

    def test_resolver(placeholder: str):
        if placeholder == "network.privateSubnetIds":
            return '["subnet-1", "subnet-2"]'
        return None

    resolver.register_resolver("network", test_resolver)

    data = {
        "subnets": "${network.privateSubnetIds}",
        "region": "us-east-1"
    }

    result = resolver.resolve(data)

    assert result["subnets"] == '["subnet-1", "subnet-2"]'
    assert result["region"] == "us-east-1"


def test_has_placeholders_dollar_brace():
    """Test has_placeholders with ${...} syntax"""
    resolver = PlaceholderResolver()

    assert resolver.has_placeholders("${test.value}")
    assert resolver.has_placeholders({"key": "${test.value}"})
    assert resolver.has_placeholders("Mix {{test1}} and ${test2}")


def test_get_placeholders_dollar_brace():
    """Test get_placeholders with ${...} syntax"""
    resolver = PlaceholderResolver()

    text = "${deployment.id} and ${stack.network.vpcId}"
    placeholders = resolver.get_placeholders(text)

    assert "deployment.id" in placeholders
    assert "stack.network.vpcId" in placeholders


def test_get_placeholders_mixed_syntax():
    """Test get_placeholders with mixed syntaxes"""
    resolver = PlaceholderResolver()

    text = "{{deployment.id}} and ${stack.network.vpcId}"
    placeholders = resolver.get_placeholders(text)

    assert "deployment.id" in placeholders
    assert "stack.network.vpcId" in placeholders
    assert len(placeholders) == 2


def test_unresolved_dollar_brace_non_strict():
    """Test unresolved ${...} placeholder in non-strict mode"""
    resolver = PlaceholderResolver()
    resolver.set_strict_mode(False)

    # Unresolved placeholder should be left as-is
    result = resolver.resolve("${unresolved.placeholder}")
    assert result == "${unresolved.placeholder}"


def test_cache_with_dollar_brace():
    """Test placeholder caching with ${...} syntax"""
    resolver = PlaceholderResolver()
    call_count = {"count": 0}

    def counting_resolver(placeholder: str):
        call_count["count"] += 1
        return "cached-value"

    resolver.register_resolver("test", counting_resolver)

    # Resolve twice with ${...} syntax
    resolver.resolve("${test.value}")
    resolver.resolve("${test.value}")

    # Should only call resolver once due to caching
    assert call_count["count"] == 1


def test_cache_same_placeholder_different_syntax():
    """Test that {{...}} and ${...} use same cache"""
    resolver = PlaceholderResolver()
    call_count = {"count": 0}

    def counting_resolver(placeholder: str):
        call_count["count"] += 1
        return "cached-value"

    resolver.register_resolver("test", counting_resolver)

    # Resolve with {{...}}
    resolver.resolve("{{test.value}}")
    # Resolve with ${...}} - should use cache
    resolver.resolve("${test.value}")

    # Should only call resolver once due to caching
    assert call_count["count"] == 1
