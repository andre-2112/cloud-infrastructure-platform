"""Tests for Orchestrator"""

import pytest
import asyncio
from cloud_core.orchestrator.orchestrator import (
    Orchestrator,
    OrchestrationPlan,
)
from cloud_core.orchestrator.dependency_resolver import CircularDependencyError


def test_orchestrator_init():
    """Test Orchestrator initialization"""
    orchestrator = Orchestrator(max_parallel=5)
    assert orchestrator.max_parallel == 5
    assert orchestrator.dependency_resolver is None


def test_create_plan():
    """Test creating orchestration plan"""
    orchestrator = Orchestrator()

    stacks_config = {
        "network": {
            "enabled": True,
            "dependencies": [],
            "layer": 1
        },
        "security": {
            "enabled": True,
            "dependencies": ["network"],
            "layer": 2
        }
    }

    plan = orchestrator.create_plan(stacks_config)

    assert plan is not None
    assert plan.get_total_stacks() == 2
    assert plan.get_layer_count() >= 1


def test_create_plan_circular_dependency():
    """Test creating plan with circular dependencies"""
    orchestrator = Orchestrator()

    stacks_config = {
        "stack_a": {
            "enabled": True,
            "dependencies": ["stack_b"]
        },
        "stack_b": {
            "enabled": True,
            "dependencies": ["stack_a"]
        }
    }

    with pytest.raises(CircularDependencyError):
        orchestrator.create_plan(stacks_config)


def test_create_plan_with_disabled_stack():
    """Test creating plan with disabled stacks"""
    orchestrator = Orchestrator()

    stacks_config = {
        "network": {
            "enabled": True,
            "dependencies": [],
            "layer": 1
        },
        "disabled_stack": {
            "enabled": False,
            "dependencies": []
        }
    }

    plan = orchestrator.create_plan(stacks_config)

    # Should only include enabled stack
    assert plan.get_total_stacks() == 1


@pytest.mark.asyncio
async def test_execute_plan():
    """Test executing orchestration plan"""
    orchestrator = Orchestrator(max_parallel=2)

    stacks_config = {
        "network": {
            "enabled": True,
            "dependencies": [],
            "layer": 1
        },
        "security": {
            "enabled": True,
            "dependencies": ["network"],
            "layer": 2
        }
    }

    plan = orchestrator.create_plan(stacks_config)

    # Mock stack executor
    executed_stacks = []

    async def stack_executor(stack_name: str):
        executed_stacks.append(stack_name)
        return (True, None)  # success, no error

    result = await orchestrator.execute_plan(plan, stack_executor)

    assert result.success
    assert result.total_stacks == 2
    assert result.successful_stacks == 2
    assert len(executed_stacks) == 2


@pytest.mark.asyncio
async def test_execute_plan_with_failure():
    """Test executing plan with stack failure"""
    orchestrator = Orchestrator()

    stacks_config = {
        "network": {
            "enabled": True,
            "dependencies": [],
            "layer": 1
        },
        "security": {
            "enabled": True,
            "dependencies": ["network"],
            "layer": 2
        }
    }

    plan = orchestrator.create_plan(stacks_config)

    # Mock executor that fails on network stack
    async def stack_executor(stack_name: str):
        if stack_name == "network":
            return (False, "Network deployment failed")
        return (True, None)

    result = await orchestrator.execute_plan(plan, stack_executor, stop_on_error=True)

    assert not result.success
    assert result.failed_stacks == 1
    assert result.skipped_stacks == 1  # security should be skipped


def test_get_destroy_order():
    """Test getting destroy order"""
    orchestrator = Orchestrator()

    stacks_config = {
        "network": {
            "enabled": True,
            "dependencies": [],
            "layer": 1
        },
        "security": {
            "enabled": True,
            "dependencies": ["network"],
            "layer": 2
        }
    }

    destroy_order = orchestrator.get_destroy_order(stacks_config)

    # Should be in reverse order
    assert len(destroy_order) >= 1
    # Security (layer 2) should be destroyed before network (layer 1)
    first_layer = destroy_order[0]
    assert "security" in first_layer


def test_validate_deployment():
    """Test validating deployment"""
    orchestrator = Orchestrator()

    stacks_config = {
        "network": {
            "enabled": True,
            "dependencies": [],
            "layer": 1
        }
    }

    validation_result = orchestrator.validate_deployment(stacks_config)

    assert validation_result["valid"]
    assert len(validation_result["errors"]) == 0
    assert validation_result["info"]["total_stacks"] == 1


def test_validate_deployment_with_errors():
    """Test validation with circular dependency"""
    orchestrator = Orchestrator()

    stacks_config = {
        "stack_a": {
            "enabled": True,
            "dependencies": ["stack_b"]
        },
        "stack_b": {
            "enabled": True,
            "dependencies": ["stack_a"]
        }
    }

    validation_result = orchestrator.validate_deployment(stacks_config)

    assert not validation_result["valid"]
    assert len(validation_result["errors"]) > 0


def test_execute_single_stack():
    """Test executing single stack"""
    orchestrator = Orchestrator()

    stacks_config = {
        "network": {
            "enabled": True,
            "dependencies": [],
            "layer": 1
        }
    }

    executed = []

    async def stack_executor(stack_name: str):
        executed.append(stack_name)
        return (True, None)

    result = orchestrator.execute_single_stack(
        "network",
        stacks_config,
        stack_executor,
        check_dependencies=False
    )

    assert result.success
    assert len(executed) == 1


def test_execute_single_stack_not_found():
    """Test executing non-existent stack"""
    orchestrator = Orchestrator()

    stacks_config = {
        "network": {
            "enabled": True,
            "dependencies": []
        }
    }

    async def stack_executor(stack_name: str):
        return (True, None)

    with pytest.raises(ValueError, match="not found"):
        orchestrator.execute_single_stack(
            "nonexistent",
            stacks_config,
            stack_executor
        )


def test_execute_single_stack_disabled():
    """Test executing disabled stack"""
    orchestrator = Orchestrator()

    stacks_config = {
        "network": {
            "enabled": False,
            "dependencies": []
        }
    }

    async def stack_executor(stack_name: str):
        return (True, None)

    with pytest.raises(ValueError, match="disabled"):
        orchestrator.execute_single_stack(
            "network",
            stacks_config,
            stack_executor
        )


def test_print_plan():
    """Test printing orchestration plan"""
    orchestrator = Orchestrator()

    stacks_config = {
        "network": {
            "enabled": True,
            "dependencies": [],
            "layer": 1
        },
        "security": {
            "enabled": True,
            "dependencies": ["network"],
            "layer": 2
        }
    }

    plan = orchestrator.create_plan(stacks_config)
    plan_text = orchestrator.print_plan(plan)

    assert "ORCHESTRATION PLAN" in plan_text
    assert "network" in plan_text
    assert "security" in plan_text


def test_orchestration_plan_methods():
    """Test OrchestrationPlan helper methods"""
    from cloud_core.orchestrator.dependency_resolver import DependencyResolver
    from cloud_core.orchestrator.layer_calculator import LayerCalculator

    resolver = DependencyResolver()
    resolver.build_graph({
        "stack1": {"dependencies": []},
        "stack2": {"dependencies": ["stack1"]},
        "stack3": {"dependencies": ["stack1"]}
    })

    calculator = LayerCalculator(resolver)
    layers = calculator.calculate_layers()

    plan = OrchestrationPlan(layers, resolver, calculator)

    assert plan.get_total_stacks() == 3
    assert plan.get_layer_count() == 2
    assert plan.get_max_parallelism() >= 1


def test_orchestrator_callbacks():
    """Test orchestrator callbacks"""
    orchestrator = Orchestrator()

    callback_data = {
        "stack_starts": [],
        "stack_completes": [],
        "layer_starts": [],
        "layer_completes": []
    }

    def on_stack_start(stack_name, layer):
        callback_data["stack_starts"].append(stack_name)

    def on_stack_complete(stack_name, success, error):
        callback_data["stack_completes"].append(stack_name)

    def on_layer_start(layer_num, stacks):
        callback_data["layer_starts"].append(layer_num)

    def on_layer_complete(layer_num, success):
        callback_data["layer_completes"].append(layer_num)

    orchestrator.on_stack_start = on_stack_start
    orchestrator.on_stack_complete = on_stack_complete
    orchestrator.on_layer_start = on_layer_start
    orchestrator.on_layer_complete = on_layer_complete

    stacks_config = {
        "network": {
            "enabled": True,
            "dependencies": [],
            "layer": 1
        }
    }

    plan = orchestrator.create_plan(stacks_config)

    async def stack_executor(stack_name: str):
        return (True, None)

    # Execute plan
    asyncio.run(orchestrator.execute_plan(plan, stack_executor))

    # Verify callbacks were called
    assert len(callback_data["stack_starts"]) == 1
    assert len(callback_data["stack_completes"]) == 1
    assert len(callback_data["layer_starts"]) == 1
    assert len(callback_data["layer_completes"]) == 1
