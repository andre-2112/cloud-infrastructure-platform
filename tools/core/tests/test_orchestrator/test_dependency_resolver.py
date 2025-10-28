"""Tests for DependencyResolver"""

import pytest
from cloud_core.orchestrator.dependency_resolver import DependencyResolver


def test_dependency_resolver_simple():
    """Test simple dependency resolution"""
    manifest = {
        "stacks": {
            "network": {"dependencies": [], "enabled": True},
            "security": {"dependencies": ["network"], "enabled": True},
        }
    }

    resolver = DependencyResolver()
    graph = resolver.build_graph(manifest)

    assert "network" in graph
    assert "security" in graph
    assert graph["network"] == []
    assert graph["security"] == ["network"]


def test_dependency_resolver_no_cycles():
    """Test cycle detection with no cycles"""
    manifest = {
        "stacks": {
            "network": {"dependencies": [], "enabled": True},
            "security": {"dependencies": ["network"], "enabled": True},
            "database": {"dependencies": ["network", "security"], "enabled": True},
        }
    }

    resolver = DependencyResolver()
    assert resolver.has_cycles(manifest) is False


def test_dependency_resolver_detects_cycles():
    """Test cycle detection with circular dependencies"""
    manifest = {
        "stacks": {
            "stack-a": {"dependencies": ["stack-b"], "enabled": True},
            "stack-b": {"dependencies": ["stack-a"], "enabled": True},
        }
    }

    resolver = DependencyResolver()
    assert resolver.has_cycles(manifest) is True


def test_dependency_resolver_get_dependencies():
    """Test getting dependencies for a stack"""
    manifest = {
        "stacks": {
            "network": {"dependencies": [], "enabled": True},
            "security": {"dependencies": ["network"], "enabled": True},
            "database": {"dependencies": ["network", "security"], "enabled": True},
        }
    }

    resolver = DependencyResolver()
    deps = resolver.get_dependencies(manifest, "database")

    assert "network" in deps
    assert "security" in deps
    assert len(deps) == 2


def test_dependency_resolver_get_dependents():
    """Test getting stacks that depend on a given stack"""
    manifest = {
        "stacks": {
            "network": {"dependencies": [], "enabled": True},
            "security": {"dependencies": ["network"], "enabled": True},
            "database": {"dependencies": ["network"], "enabled": True},
        }
    }

    resolver = DependencyResolver()
    dependents = resolver.get_dependents(manifest, "network")

    assert "security" in dependents
    assert "database" in dependents
    assert len(dependents) == 2


def test_dependency_resolver_transitive_dependencies():
    """Test transitive dependency resolution"""
    manifest = {
        "stacks": {
            "network": {"dependencies": [], "enabled": True},
            "security": {"dependencies": ["network"], "enabled": True},
            "database": {"dependencies": ["security"], "enabled": True},
        }
    }

    resolver = DependencyResolver()
    deps = resolver.get_all_dependencies(manifest, "database")

    # Database depends on security, which depends on network
    assert "security" in deps
    assert "network" in deps
    assert len(deps) == 2


def test_dependency_resolver_disabled_stacks():
    """Test that disabled stacks are excluded from graph"""
    manifest = {
        "stacks": {
            "network": {"dependencies": [], "enabled": True},
            "security": {"dependencies": [], "enabled": False},  # Disabled
            "database": {"dependencies": ["network"], "enabled": True},
        }
    }

    resolver = DependencyResolver()
    graph = resolver.build_graph(manifest)

    assert "network" in graph
    assert "security" not in graph  # Should be excluded
    assert "database" in graph


def test_dependency_resolver_unknown_dependency():
    """Test error when depending on unknown stack"""
    manifest = {
        "stacks": {
            "network": {"dependencies": [], "enabled": True},
            "database": {"dependencies": ["nonexistent"], "enabled": True},
        }
    }

    resolver = DependencyResolver()

    with pytest.raises(ValueError, match="unknown or disabled stack"):
        resolver.build_graph(manifest)


def test_dependency_resolver_get_dependency_order():
    """Test getting deployment order"""
    manifest = {
        "stacks": {
            "network": {"dependencies": [], "enabled": True},
            "security": {"dependencies": ["network"], "enabled": True},
            "database": {"dependencies": ["network", "security"], "enabled": True},
        }
    }

    resolver = DependencyResolver()
    resolver.build_graph(manifest)
    order = resolver.get_dependency_order()

    # Network should come first
    assert order.index("network") < order.index("security")
    assert order.index("security") < order.index("database")


def test_dependency_resolver_get_dependency_order_with_cycle():
    """Test that get_dependency_order raises error on cycles"""
    manifest = {
        "stacks": {
            "stack-a": {"dependencies": ["stack-b"], "enabled": True},
            "stack-b": {"dependencies": ["stack-a"], "enabled": True},
        }
    }

    resolver = DependencyResolver()
    resolver.build_graph(manifest)

    from cloud_core.orchestrator.dependency_resolver import CircularDependencyError
    with pytest.raises(CircularDependencyError) as exc_info:
        resolver.get_dependency_order()

    # Check that the cycle is included in the error
    assert len(exc_info.value.cycle) > 0


def test_dependency_resolver_detect_cycles():
    """Test detect_cycles method"""
    manifest = {
        "stacks": {
            "stack-a": {"dependencies": ["stack-b"], "enabled": True},
            "stack-b": {"dependencies": ["stack-c"], "enabled": True},
            "stack-c": {"dependencies": ["stack-a"], "enabled": True},  # Cycle
        }
    }

    resolver = DependencyResolver()
    resolver.build_graph(manifest)
    cycles = resolver.detect_cycles()

    assert len(cycles) > 0
    assert len(cycles[0]) > 0  # Cycle should have entries


def test_dependency_resolver_old_api_get_dependencies():
    """Test old API for get_dependencies (stateful)"""
    stacks = {
        "network": {"dependencies": [], "enabled": True},
        "security": {"dependencies": ["network"], "enabled": True},
    }

    resolver = DependencyResolver()
    resolver.build_graph(stacks)

    # Old API: pass stack name directly
    deps = resolver.get_dependencies("security")
    assert "network" in deps


def test_dependency_resolver_old_api_get_dependencies_not_found():
    """Test old API for get_dependencies with non-existent stack"""
    stacks = {
        "network": {"dependencies": [], "enabled": True},
    }

    resolver = DependencyResolver()
    resolver.build_graph(stacks)

    # Non-existent stack should return empty list
    deps = resolver.get_dependencies("nonexistent")
    assert deps == []


def test_dependency_resolver_old_api_get_dependents():
    """Test old API for get_dependents (stateful)"""
    stacks = {
        "network": {"dependencies": [], "enabled": True},
        "security": {"dependencies": ["network"], "enabled": True},
    }

    resolver = DependencyResolver()
    resolver.build_graph(stacks)

    # Old API: pass stack name directly
    dependents = resolver.get_dependents("network")
    assert "security" in dependents


def test_dependency_resolver_old_api_get_dependents_not_found():
    """Test old API for get_dependents with non-existent stack"""
    stacks = {
        "network": {"dependencies": [], "enabled": True},
    }

    resolver = DependencyResolver()
    resolver.build_graph(stacks)

    # Non-existent stack should return empty list
    dependents = resolver.get_dependents("nonexistent")
    assert dependents == []


def test_dependency_resolver_get_all_dependencies_recursive():
    """Test get_all_dependencies_recursive method"""
    stacks = {
        "network": {"dependencies": [], "enabled": True},
        "security": {"dependencies": ["network"], "enabled": True},
        "database": {"dependencies": ["security"], "enabled": True},
        "app": {"dependencies": ["database"], "enabled": True},
    }

    resolver = DependencyResolver()
    resolver.build_graph(stacks)

    # App transitively depends on database, security, and network
    deps = resolver.get_all_dependencies_recursive("app")

    assert "database" in deps
    assert "security" in deps
    assert "network" in deps
    assert len(deps) == 3


def test_dependency_resolver_get_all_dependencies_recursive_not_found():
    """Test get_all_dependencies_recursive with non-existent stack"""
    stacks = {
        "network": {"dependencies": [], "enabled": True},
    }

    resolver = DependencyResolver()
    resolver.build_graph(stacks)

    deps = resolver.get_all_dependencies_recursive("nonexistent")
    assert len(deps) == 0


def test_dependency_resolver_get_all_dependents_recursive():
    """Test get_all_dependents_recursive method"""
    stacks = {
        "network": {"dependencies": [], "enabled": True},
        "security": {"dependencies": ["network"], "enabled": True},
        "database": {"dependencies": ["security"], "enabled": True},
        "app": {"dependencies": ["database"], "enabled": True},
    }

    resolver = DependencyResolver()
    resolver.build_graph(stacks)

    # Network is transitively required by security, database, and app
    dependents = resolver.get_all_dependents_recursive("network")

    assert "security" in dependents
    assert "database" in dependents
    assert "app" in dependents
    assert len(dependents) == 3


def test_dependency_resolver_get_all_dependents_recursive_not_found():
    """Test get_all_dependents_recursive with non-existent stack"""
    stacks = {
        "network": {"dependencies": [], "enabled": True},
    }

    resolver = DependencyResolver()
    resolver.build_graph(stacks)

    dependents = resolver.get_all_dependents_recursive("nonexistent")
    assert len(dependents) == 0


def test_dependency_resolver_can_deploy_stack():
    """Test can_deploy_stack method"""
    stacks = {
        "network": {"dependencies": [], "enabled": True},
        "security": {"dependencies": ["network"], "enabled": True},
        "database": {"dependencies": ["network", "security"], "enabled": True},
    }

    resolver = DependencyResolver()
    resolver.build_graph(stacks)

    # Network can be deployed with no dependencies
    assert resolver.can_deploy_stack("network", set()) is True

    # Security can be deployed if network is deployed
    assert resolver.can_deploy_stack("security", {"network"}) is True
    assert resolver.can_deploy_stack("security", set()) is False

    # Database can be deployed if both network and security are deployed
    assert resolver.can_deploy_stack("database", {"network", "security"}) is True
    assert resolver.can_deploy_stack("database", {"network"}) is False


def test_dependency_resolver_can_deploy_stack_not_found():
    """Test can_deploy_stack with non-existent stack"""
    stacks = {
        "network": {"dependencies": [], "enabled": True},
    }

    resolver = DependencyResolver()
    resolver.build_graph(stacks)

    assert resolver.can_deploy_stack("nonexistent", set()) is False


def test_dependency_resolver_get_stack_count():
    """Test get_stack_count method"""
    stacks = {
        "network": {"dependencies": [], "enabled": True},
        "security": {"dependencies": ["network"], "enabled": True},
        "database": {"dependencies": ["security"], "enabled": True},
    }

    resolver = DependencyResolver()
    resolver.build_graph(stacks)

    assert resolver.get_stack_count() == 3


def test_dependency_resolver_get_stack_names():
    """Test get_stack_names method"""
    stacks = {
        "network": {"dependencies": [], "enabled": True},
        "security": {"dependencies": ["network"], "enabled": True},
    }

    resolver = DependencyResolver()
    resolver.build_graph(stacks)

    names = resolver.get_stack_names()
    assert "network" in names
    assert "security" in names
    assert len(names) == 2


def test_dependency_resolver_build_dependency_graph():
    """Test build_dependency_graph convenience method"""
    manifest = {
        "stacks": {
            "network": {"dependencies": [], "enabled": True},
            "security": {"dependencies": ["network"], "enabled": True},
        }
    }

    resolver = DependencyResolver()
    graph = resolver.build_dependency_graph(manifest)

    assert graph["network"] == []
    assert graph["security"] == ["network"]
