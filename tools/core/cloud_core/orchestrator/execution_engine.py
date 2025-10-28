"""
Execution Engine

Executes stacks layer by layer with support for parallel execution.
Handles errors, rollback, and progress tracking.
"""

import asyncio
from typing import Dict, List, Callable, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class StackStatus(Enum):
    """Status of stack execution"""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    ROLLED_BACK = "rolled_back"


@dataclass
class StackExecution:
    """Represents execution of a single stack"""

    stack_name: str
    layer: int
    status: StackStatus = StackStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error: Optional[str] = None
    output: str = ""

    def duration_seconds(self) -> float:
        """Get execution duration in seconds"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0


@dataclass
class ExecutionResult:
    """Result of execution"""

    success: bool
    total_stacks: int
    successful_stacks: int
    failed_stacks: int
    skipped_stacks: int
    stack_executions: Dict[str, StackExecution] = field(default_factory=dict)
    total_duration_seconds: float = 0.0
    error_message: Optional[str] = None


class ExecutionEngine:
    """Executes stacks in layers with parallel execution support"""

    def __init__(
        self,
        max_parallel: int = 3,
        on_stack_start: Optional[Callable[[str, int], None]] = None,
        on_stack_complete: Optional[Callable[[str, bool, Optional[str]], None]] = None,
        on_layer_start: Optional[Callable[[int, List[str]], None]] = None,
        on_layer_complete: Optional[Callable[[int, bool], None]] = None,
    ) -> None:
        """
        Initialize execution engine

        Args:
            max_parallel: Maximum number of stacks to execute in parallel per layer
            on_stack_start: Callback when stack execution starts (stack_name, layer)
            on_stack_complete: Callback when stack completes (stack_name, success, error)
            on_layer_start: Callback when layer starts (layer_num, stack_names)
            on_layer_complete: Callback when layer completes (layer_num, success)
        """
        self.max_parallel = max_parallel
        self.on_stack_start = on_stack_start
        self.on_stack_complete = on_stack_complete
        self.on_layer_start = on_layer_start
        self.on_layer_complete = on_layer_complete

        self.executions: Dict[str, StackExecution] = {}
        self.stop_on_error = True

    async def execute_layers(
        self,
        layers: List[List[str]],
        stack_executor: Callable[[str], Any],
        stop_on_error: bool = True,
    ) -> ExecutionResult:
        """
        Execute stacks layer by layer

        Args:
            layers: List of layers (each layer is a list of stack names)
            stack_executor: Async function to execute a single stack
                           Should return (success: bool, error: Optional[str])
            stop_on_error: Whether to stop execution if a stack fails

        Returns:
            ExecutionResult with summary and details
        """
        self.stop_on_error = stop_on_error
        self.executions = {}

        # Initialize executions
        for layer_num, layer_stacks in enumerate(layers, start=1):
            for stack_name in layer_stacks:
                self.executions[stack_name] = StackExecution(
                    stack_name=stack_name, layer=layer_num
                )

        start_time = datetime.now()
        overall_success = True
        failed_layer = False

        # Execute each layer
        for layer_num, layer_stacks in enumerate(layers, start=1):
            # Skip remaining layers if previous layer failed and stop_on_error is True
            if failed_layer and stop_on_error:
                # Mark remaining stacks as skipped
                for stack_name in layer_stacks:
                    self.executions[stack_name].status = StackStatus.SKIPPED
                continue

            # Callback: Layer start
            if self.on_layer_start:
                self.on_layer_start(layer_num, layer_stacks)

            # Execute layer
            layer_success = await self._execute_layer(
                layer_num, layer_stacks, stack_executor
            )

            # Callback: Layer complete
            if self.on_layer_complete:
                self.on_layer_complete(layer_num, layer_success)

            if not layer_success:
                overall_success = False
                failed_layer = True

        end_time = datetime.now()
        total_duration = (end_time - start_time).total_seconds()

        # Build result
        successful = sum(
            1
            for e in self.executions.values()
            if e.status == StackStatus.SUCCESS
        )
        failed = sum(
            1 for e in self.executions.values() if e.status == StackStatus.FAILED
        )
        skipped = sum(
            1 for e in self.executions.values() if e.status == StackStatus.SKIPPED
        )

        result = ExecutionResult(
            success=overall_success,
            total_stacks=len(self.executions),
            successful_stacks=successful,
            failed_stacks=failed,
            skipped_stacks=skipped,
            stack_executions=self.executions.copy(),
            total_duration_seconds=total_duration,
            error_message=self._get_first_error() if not overall_success else None,
        )

        return result

    async def _execute_layer(
        self,
        layer_num: int,
        layer_stacks: List[str],
        stack_executor: Callable[[str], Any],
    ) -> bool:
        """
        Execute all stacks in a layer with parallelism

        Args:
            layer_num: Layer number
            layer_stacks: List of stack names in this layer
            stack_executor: Async function to execute a stack

        Returns:
            True if all stacks succeeded, False otherwise
        """
        # Create semaphore for parallel execution limit
        semaphore = asyncio.Semaphore(self.max_parallel)

        async def execute_with_semaphore(stack_name: str) -> bool:
            async with semaphore:
                return await self._execute_stack(stack_name, stack_executor)

        # Execute all stacks in parallel (up to max_parallel)
        tasks = [execute_with_semaphore(stack) for stack in layer_stacks]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Check if all succeeded
        layer_success = True
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                layer_success = False
                stack_name = layer_stacks[i]
                self.executions[stack_name].status = StackStatus.FAILED
                self.executions[stack_name].error = str(result)
            elif not result:
                layer_success = False

        return layer_success

    async def _execute_stack(
        self, stack_name: str, stack_executor: Callable[[str], Any]
    ) -> bool:
        """
        Execute a single stack

        Args:
            stack_name: Name of the stack
            stack_executor: Async function to execute the stack

        Returns:
            True if successful, False otherwise
        """
        execution = self.executions[stack_name]
        execution.status = StackStatus.RUNNING
        execution.start_time = datetime.now()

        # Callback: Stack start
        if self.on_stack_start:
            self.on_stack_start(stack_name, execution.layer)

        try:
            # Execute stack
            success, error = await stack_executor(stack_name)

            execution.end_time = datetime.now()

            if success:
                execution.status = StackStatus.SUCCESS
            else:
                execution.status = StackStatus.FAILED
                execution.error = error

            # Callback: Stack complete
            if self.on_stack_complete:
                self.on_stack_complete(stack_name, success, error)

            return success

        except Exception as e:
            execution.end_time = datetime.now()
            execution.status = StackStatus.FAILED
            execution.error = str(e)

            # Callback: Stack complete
            if self.on_stack_complete:
                self.on_stack_complete(stack_name, False, str(e))

            return False

    def _get_first_error(self) -> Optional[str]:
        """Get the first error message from failed stacks"""
        for execution in self.executions.values():
            if execution.status == StackStatus.FAILED and execution.error:
                return f"{execution.stack_name}: {execution.error}"
        return None

    def get_execution_summary(self) -> Dict[str, Any]:
        """
        Get execution summary

        Returns:
            Dictionary with execution statistics
        """
        if not self.executions:
            return {}

        successful = [e for e in self.executions.values() if e.status == StackStatus.SUCCESS]
        failed = [e for e in self.executions.values() if e.status == StackStatus.FAILED]
        skipped = [e for e in self.executions.values() if e.status == StackStatus.SKIPPED]

        total_duration = sum(e.duration_seconds() for e in successful + failed)

        return {
            "total_stacks": len(self.executions),
            "successful": len(successful),
            "failed": len(failed),
            "skipped": len(skipped),
            "total_duration_seconds": total_duration,
            "average_duration_seconds": (
                total_duration / len(successful + failed) if (successful + failed) else 0
            ),
            "success_rate": (
                len(successful) / len(self.executions) if self.executions else 0
            ),
        }

    def get_failed_stacks(self) -> List[str]:
        """Get list of failed stack names"""
        return [
            name
            for name, exec in self.executions.items()
            if exec.status == StackStatus.FAILED
        ]

    def get_successful_stacks(self) -> List[str]:
        """Get list of successful stack names"""
        return [
            name
            for name, exec in self.executions.items()
            if exec.status == StackStatus.SUCCESS
        ]
