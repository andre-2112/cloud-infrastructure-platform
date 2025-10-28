"""Tests for LayerCalculator"""

import pytest
from cloud_core.orchestrator.layer_calculator import LayerCalculator


def test_layer_calculator_single_layer():
    """Test layer calculation with independent stacks"""
    dependency_graph = {
        "stack-a": [],
        "stack-b": [],
        "stack-c": [],
    }

    calculator = LayerCalculator()
    layers = calculator.calculate_layers(dependency_graph)

    assert len(layers) == 1
    assert set(layers[0]) == {"stack-a", "stack-b", "stack-c"}


def test_layer_calculator_multiple_layers():
    """Test layer calculation with dependencies"""
    dependency_graph = {
        "network": [],
        "security": ["network"],
        "database": ["network", "security"],
    }

    calculator = LayerCalculator()
    layers = calculator.calculate_layers(dependency_graph)

    assert len(layers) == 3
    assert layers[0] == ["network"]
    assert layers[1] == ["security"]
    assert layers[2] == ["database"]


def test_layer_calculator_parallel_stacks():
    """Test stacks that can be deployed in parallel"""
    dependency_graph = {
        "network": [],
        "security": ["network"],
        "database": ["network"],
        "storage": ["network"],
    }

    calculator = LayerCalculator()
    layers = calculator.calculate_layers(dependency_graph)

    assert len(layers) == 2
    assert layers[0] == ["network"]
    assert set(layers[1]) == {"security", "database", "storage"}


def test_layer_calculator_complex_dependencies():
    """Test complex dependency tree"""
    dependency_graph = {
        "network": [],
        "security": ["network"],
        "dns": ["network"],
        "database": ["network", "security"],
        "app": ["network", "database", "dns"],
    }

    calculator = LayerCalculator()
    layers = calculator.calculate_layers(dependency_graph)

    # Layer 0: network
    # Layer 1: security, dns (parallel)
    # Layer 2: database
    # Layer 3: app
    assert len(layers) == 4
    assert layers[0] == ["network"]
    assert set(layers[1]) == {"security", "dns"}
    assert layers[2] == ["database"]
    assert layers[3] == ["app"]


def test_layer_calculator_empty_graph():
    """Test with empty dependency graph"""
    calculator = LayerCalculator()
    layers = calculator.calculate_layers({})

    assert len(layers) == 0


def test_layer_calculator_no_data_source():
    """Test with no resolver and no dependency graph"""
    calculator = LayerCalculator()
    layers = calculator.calculate_layers()

    assert len(layers) == 0


def test_layer_calculator_circular_dependency():
    """Test detection of circular dependencies"""
    dependency_graph = {
        "stack-a": ["stack-b"],
        "stack-b": ["stack-c"],
        "stack-c": ["stack-a"],  # Circular dependency
    }

    calculator = LayerCalculator()

    with pytest.raises(RuntimeError, match="Cannot calculate layers"):
        calculator.calculate_layers(dependency_graph)


def test_get_layers():
    """Test get_layers method"""
    dependency_graph = {
        "network": [],
        "security": ["network"],
    }

    calculator = LayerCalculator()
    calculator.calculate_layers(dependency_graph)

    layers = calculator.get_layers()
    assert len(layers) == 2
    assert layers[0] == ["network"]


def test_get_layer_count():
    """Test get_layer_count method"""
    dependency_graph = {
        "network": [],
        "security": ["network"],
        "database": ["security"],
    }

    calculator = LayerCalculator()
    calculator.calculate_layers(dependency_graph)

    assert calculator.get_layer_count() == 3


def test_get_layer_for_stack():
    """Test get_layer_for_stack method"""
    dependency_graph = {
        "network": [],
        "security": ["network"],
        "database": ["security"],
    }

    calculator = LayerCalculator()
    calculator.calculate_layers(dependency_graph)

    assert calculator.get_layer_for_stack("network") == 1
    assert calculator.get_layer_for_stack("security") == 2
    assert calculator.get_layer_for_stack("database") == 3


def test_get_layer_for_stack_not_found():
    """Test get_layer_for_stack with non-existent stack"""
    dependency_graph = {
        "network": [],
    }

    calculator = LayerCalculator()
    calculator.calculate_layers(dependency_graph)

    assert calculator.get_layer_for_stack("nonexistent") == -1


def test_get_stacks_in_layer():
    """Test get_stacks_in_layer method"""
    dependency_graph = {
        "network": [],
        "security": ["network"],
        "database": ["network"],
    }

    calculator = LayerCalculator()
    calculator.calculate_layers(dependency_graph)

    layer1 = calculator.get_stacks_in_layer(1)
    assert layer1 == ["network"]

    layer2 = calculator.get_stacks_in_layer(2)
    assert set(layer2) == {"security", "database"}


def test_get_stacks_in_layer_invalid():
    """Test get_stacks_in_layer with invalid layer number"""
    dependency_graph = {"network": []}

    calculator = LayerCalculator()
    calculator.calculate_layers(dependency_graph)

    # Layer 0 is invalid (1-indexed)
    assert calculator.get_stacks_in_layer(0) == []

    # Layer 999 is invalid (doesn't exist)
    assert calculator.get_stacks_in_layer(999) == []


def test_get_max_parallelism():
    """Test get_max_parallelism method"""
    dependency_graph = {
        "network": [],
        "security": ["network"],
        "database": ["network"],
        "storage": ["network"],
    }

    calculator = LayerCalculator()
    calculator.calculate_layers(dependency_graph)

    # Layer 2 has 3 stacks (security, database, storage)
    assert calculator.get_max_parallelism() == 3


def test_get_max_parallelism_empty():
    """Test get_max_parallelism with empty layers"""
    calculator = LayerCalculator()
    assert calculator.get_max_parallelism() == 0


def test_validate_layers_against_manifest_valid():
    """Test validate_layers_against_manifest with valid manifest"""
    dependency_graph = {
        "network": [],
        "security": ["network"],
    }

    calculator = LayerCalculator()
    calculator.calculate_layers(dependency_graph)

    stacks_config = {
        "network": {"enabled": True, "layer": 1},
        "security": {"enabled": True, "layer": 2},
    }

    errors = calculator.validate_layers_against_manifest(stacks_config)
    assert len(errors) == 0


def test_validate_layers_against_manifest_invalid_layer():
    """Test validation with stack in wrong layer"""
    dependency_graph = {
        "network": [],
        "security": ["network"],
    }

    calculator = LayerCalculator()
    calculator.calculate_layers(dependency_graph)

    stacks_config = {
        "network": {"enabled": True, "layer": 1},
        "security": {"enabled": True, "layer": 1},  # Should be in layer 2
    }

    errors = calculator.validate_layers_against_manifest(stacks_config)
    assert len(errors) == 1
    assert "security" in errors[0]
    assert "layer 1" in errors[0]


def test_validate_layers_against_manifest_stack_not_found():
    """Test validation with stack not in calculated layers"""
    dependency_graph = {
        "network": [],
    }

    calculator = LayerCalculator()
    calculator.calculate_layers(dependency_graph)

    stacks_config = {
        "network": {"enabled": True, "layer": 1},
        "nonexistent": {"enabled": True, "layer": 1},
    }

    errors = calculator.validate_layers_against_manifest(stacks_config)
    assert len(errors) == 1
    assert "nonexistent" in errors[0]
    assert "not found" in errors[0]


def test_validate_layers_against_manifest_disabled_stack():
    """Test validation skips disabled stacks"""
    dependency_graph = {
        "network": [],
    }

    calculator = LayerCalculator()
    calculator.calculate_layers(dependency_graph)

    stacks_config = {
        "network": {"enabled": True, "layer": 1},
        "disabled": {"enabled": False, "layer": 999},  # Should be ignored
    }

    errors = calculator.validate_layers_against_manifest(stacks_config)
    assert len(errors) == 0


def test_validate_layers_against_manifest_no_layer():
    """Test validation with stack without layer field"""
    dependency_graph = {
        "network": [],
    }

    calculator = LayerCalculator()
    calculator.calculate_layers(dependency_graph)

    stacks_config = {
        "network": {"enabled": True},  # No layer field
    }

    errors = calculator.validate_layers_against_manifest(stacks_config)
    assert len(errors) == 0


def test_validate_layers_against_manifest_later_layer():
    """Test validation with stack in later layer than required (valid)"""
    dependency_graph = {
        "network": [],
        "security": ["network"],
    }

    calculator = LayerCalculator()
    calculator.calculate_layers(dependency_graph)

    stacks_config = {
        "network": {"enabled": True, "layer": 1},
        "security": {"enabled": True, "layer": 5},  # Can be in later layer
    }

    errors = calculator.validate_layers_against_manifest(stacks_config)
    assert len(errors) == 0


def test_get_layer_statistics():
    """Test get_layer_statistics method"""
    dependency_graph = {
        "network": [],
        "security": ["network"],
        "database": ["network"],
        "storage": ["network"],
    }

    calculator = LayerCalculator()
    calculator.calculate_layers(dependency_graph)

    stats = calculator.get_layer_statistics()

    assert stats["total_layers"] == 2
    assert stats["total_stacks"] == 4
    assert stats["max_parallelism"] == 3
    assert stats["min_layer_size"] == 1
    assert stats["avg_layer_size"] == 2.0
    assert stats["layer_sizes"] == [1, 3]


def test_get_layer_statistics_empty():
    """Test get_layer_statistics with no layers"""
    calculator = LayerCalculator()

    stats = calculator.get_layer_statistics()

    assert stats["total_layers"] == 0
    assert stats["total_stacks"] == 0
    assert stats["max_parallelism"] == 0
    assert stats["min_layer_size"] == 0
    assert stats["avg_layer_size"] == 0.0


def test_print_layers():
    """Test print_layers method"""
    dependency_graph = {
        "network": [],
        "security": ["network"],
        "database": ["network"],
    }

    calculator = LayerCalculator()
    calculator.calculate_layers(dependency_graph)

    output = calculator.print_layers()

    assert "Total Layers: 2" in output
    assert "Layer 1" in output
    assert "network" in output
    assert "Layer 2" in output
    assert "security" in output
    assert "database" in output


def test_print_layers_empty():
    """Test print_layers with no layers"""
    calculator = LayerCalculator()

    output = calculator.print_layers()
    assert output == "No layers calculated"
