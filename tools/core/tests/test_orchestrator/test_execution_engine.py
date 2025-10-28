"""Tests for ExecutionEngine"""

import pytest
import asyncio
from cloud_core.orchestrator.execution_engine import (
    ExecutionEngine,
    StackStatus,
    StackExecution,
    ExecutionResult,
)


def test_execution_engine_init():
    """Test ExecutionEngine initialization"""
    engine = ExecutionEngine(max_parallel=5)
    assert engine.max_parallel == 5
    assert engine.executions == {}


def test_stack_execution_duration():
    """Test StackExecution duration calculation"""
    from datetime import datetime, timedelta

    execution = StackExecution(stack_name="test", layer=1)
    execution.start_time = datetime.now()
    execution.end_time = execution.start_time + timedelta(seconds=5)

    duration = execution.duration_seconds()
    assert 4.9 <= duration <= 5.1  # Allow small variance


@pytest.mark.asyncio
async def test_execute_layers_success():
    """Test executing layers successfully"""
    engine = ExecutionEngine(max_parallel=2)

    layers = [["stack1", "stack2"], ["stack3"]]

    executed = []

    async def stack_executor(stack_name: str):
        executed.append(stack_name)
        return (True, None)

    result = await engine.execute_layers(layers, stack_executor)

    assert result.success
    assert result.total_stacks == 3
    assert result.successful_stacks == 3
    assert result.failed_stacks == 0
    assert len(executed) == 3


@pytest.mark.asyncio
async def test_execute_layers_with_failure():
    """Test executing layers with failure"""
    engine = ExecutionEngine(max_parallel=2)

    layers = [["stack1", "stack2"], ["stack3"]]

    async def stack_executor(stack_name: str):
        if stack_name == "stack1":
            return (False, "Stack1 failed")
        return (True, None)

    result = await engine.execute_layers(layers, stack_executor, stop_on_error=True)

    assert not result.success
    assert result.failed_stacks >= 1
    assert result.skipped_stacks >= 1  # stack3 should be skipped


@pytest.mark.asyncio
async def test_execute_layers_continue_on_error():
    """Test executing layers without stopping on error"""
    engine = ExecutionEngine(max_parallel=2)

    layers = [["stack1"], ["stack2"]]

    async def stack_executor(stack_name: str):
        if stack_name == "stack1":
            return (False, "Stack1 failed")
        return (True, None)

    result = await engine.execute_layers(layers, stack_executor, stop_on_error=False)

    assert not result.success
    assert result.successful_stacks == 1  # stack2 should still execute
    assert result.failed_stacks == 1


@pytest.mark.asyncio
async def test_parallel_execution():
    """Test parallel execution within a layer"""
    engine = ExecutionEngine(max_parallel=3)

    layers = [["stack1", "stack2", "stack3"]]

    execution_order = []
    start_times = {}

    async def stack_executor(stack_name: str):
        from datetime import datetime
        start_times[stack_name] = datetime.now()
        execution_order.append(stack_name)
        await asyncio.sleep(0.1)  # Simulate work
        return (True, None)

    result = await engine.execute_layers(layers, stack_executor)

    assert result.success
    assert len(execution_order) == 3

    # All stacks should start within a short time window (parallel execution)
    times = list(start_times.values())
    time_spread = (max(times) - min(times)).total_seconds()
    assert time_spread < 0.5  # Should all start within 0.5 seconds


@pytest.mark.asyncio
async def test_execution_callbacks():
    """Test execution engine callbacks"""
    callback_data = {
        "stack_starts": [],
        "stack_completes": [],
        "layer_starts": [],
        "layer_completes": []
    }

    def on_stack_start(stack_name, layer):
        callback_data["stack_starts"].append((stack_name, layer))

    def on_stack_complete(stack_name, success, error):
        callback_data["stack_completes"].append((stack_name, success))

    def on_layer_start(layer_num, stacks):
        callback_data["layer_starts"].append((layer_num, stacks))

    def on_layer_complete(layer_num, success):
        callback_data["layer_completes"].append((layer_num, success))

    engine = ExecutionEngine(
        max_parallel=2,
        on_stack_start=on_stack_start,
        on_stack_complete=on_stack_complete,
        on_layer_start=on_layer_start,
        on_layer_complete=on_layer_complete
    )

    layers = [["stack1"], ["stack2"]]

    async def stack_executor(stack_name: str):
        return (True, None)

    await engine.execute_layers(layers, stack_executor)

    # Verify callbacks
    assert len(callback_data["stack_starts"]) == 2
    assert len(callback_data["stack_completes"]) == 2
    assert len(callback_data["layer_starts"]) == 2
    assert len(callback_data["layer_completes"]) == 2


@pytest.mark.asyncio
async def test_exception_handling():
    """Test handling executor exceptions"""
    engine = ExecutionEngine()

    layers = [["stack1"]]

    async def stack_executor(stack_name: str):
        raise Exception("Executor crashed")

    result = await engine.execute_layers(layers, stack_executor)

    assert not result.success
    assert result.failed_stacks == 1
    assert "crashed" in result.error_message.lower()


def test_get_execution_summary():
    """Test getting execution summary"""
    engine = ExecutionEngine()

    from datetime import datetime, timedelta

    # Create mock executions
    engine.executions = {
        "stack1": StackExecution(
            stack_name="stack1",
            layer=1,
            status=StackStatus.SUCCESS,
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(seconds=5)
        ),
        "stack2": StackExecution(
            stack_name="stack2",
            layer=2,
            status=StackStatus.FAILED,
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(seconds=3)
        ),
        "stack3": StackExecution(
            stack_name="stack3",
            layer=3,
            status=StackStatus.SKIPPED
        )
    }

    summary = engine.get_execution_summary()

    assert summary["total_stacks"] == 3
    assert summary["successful"] == 1
    assert summary["failed"] == 1
    assert summary["skipped"] == 1
    assert summary["total_duration_seconds"] > 0


def test_get_failed_stacks():
    """Test getting failed stacks"""
    engine = ExecutionEngine()

    engine.executions = {
        "stack1": StackExecution(stack_name="stack1", layer=1, status=StackStatus.SUCCESS),
        "stack2": StackExecution(stack_name="stack2", layer=2, status=StackStatus.FAILED),
        "stack3": StackExecution(stack_name="stack3", layer=3, status=StackStatus.FAILED)
    }

    failed = engine.get_failed_stacks()

    assert len(failed) == 2
    assert "stack2" in failed
    assert "stack3" in failed


def test_get_successful_stacks():
    """Test getting successful stacks"""
    engine = ExecutionEngine()

    engine.executions = {
        "stack1": StackExecution(stack_name="stack1", layer=1, status=StackStatus.SUCCESS),
        "stack2": StackExecution(stack_name="stack2", layer=2, status=StackStatus.FAILED),
        "stack3": StackExecution(stack_name="stack3", layer=3, status=StackStatus.SUCCESS)
    }

    successful = engine.get_successful_stacks()

    assert len(successful) == 2
    assert "stack1" in successful
    assert "stack3" in successful


def test_execution_result():
    """Test ExecutionResult dataclass"""
    from datetime import datetime

    execution = StackExecution(
        stack_name="test",
        layer=1,
        status=StackStatus.SUCCESS,
        start_time=datetime.now()
    )

    result = ExecutionResult(
        success=True,
        total_stacks=5,
        successful_stacks=4,
        failed_stacks=1,
        skipped_stacks=0,
        stack_executions={"test": execution},
        total_duration_seconds=120.5
    )

    assert result.success
    assert result.total_stacks == 5
    assert result.total_duration_seconds == 120.5


def test_stack_status_enum():
    """Test StackStatus enum values"""
    assert StackStatus.PENDING.value == "pending"
    assert StackStatus.RUNNING.value == "running"
    assert StackStatus.SUCCESS.value == "success"
    assert StackStatus.FAILED.value == "failed"
    assert StackStatus.SKIPPED.value == "skipped"
    assert StackStatus.ROLLED_BACK.value == "rolled_back"


@pytest.mark.asyncio
async def test_max_parallel_limit():
    """Test that max_parallel limit is respected"""
    engine = ExecutionEngine(max_parallel=2)

    layers = [["stack1", "stack2", "stack3", "stack4"]]

    concurrent_count = {"current": 0, "max": 0}
    lock = asyncio.Lock()

    async def stack_executor(stack_name: str):
        async with lock:
            concurrent_count["current"] += 1
            concurrent_count["max"] = max(
                concurrent_count["max"],
                concurrent_count["current"]
            )

        await asyncio.sleep(0.1)

        async with lock:
            concurrent_count["current"] -= 1

        return (True, None)

    await engine.execute_layers(layers, stack_executor)

    # Max concurrent should not exceed max_parallel
    assert concurrent_count["max"] <= 2


@pytest.mark.asyncio
async def test_layer_execution_order():
    """Test that layers execute in order"""
    engine = ExecutionEngine(max_parallel=3)

    layers = [["layer1_stack1"], ["layer2_stack1"], ["layer3_stack1"]]

    execution_order = []

    async def stack_executor(stack_name: str):
        execution_order.append(stack_name)
        return (True, None)

    await engine.execute_layers(layers, stack_executor)

    # Should execute in layer order
    assert execution_order[0] == "layer1_stack1"
    assert execution_order[1] == "layer2_stack1"
    assert execution_order[2] == "layer3_stack1"


@pytest.mark.asyncio
async def test_stack_execution_tracking():
    """Test that stack executions are tracked correctly"""
    engine = ExecutionEngine()

    layers = [["stack1", "stack2"]]

    async def stack_executor(stack_name: str):
        return (True, None)

    result = await engine.execute_layers(layers, stack_executor)

    # Check executions were tracked
    assert "stack1" in result.stack_executions
    assert "stack2" in result.stack_executions

    exec1 = result.stack_executions["stack1"]
    assert exec1.status == StackStatus.SUCCESS
    assert exec1.start_time is not None
    assert exec1.end_time is not None
    assert exec1.layer == 1
