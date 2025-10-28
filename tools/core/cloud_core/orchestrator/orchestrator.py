"""
Orchestrator

Main orchestration engine that coordinates deployment execution.
Combines dependency resolution, layer calculation, and execution engine.
"""

from typing import Dict, List, Optional, Callable, Any
from pathlib import Path
import asyncio

from .dependency_resolver import DependencyResolver, CircularDependencyError
from .layer_calculator import LayerCalculator
from .execution_engine import ExecutionEngine, ExecutionResult, StackStatus
from ..utils.logger import get_logger

logger = get_logger(__name__)


class OrchestrationPlan:
    """Represents a deployment orchestration plan"""

    def __init__(
        self,
        layers: List[List[str]],
        dependency_resolver: DependencyResolver,
        layer_calculator: LayerCalculator,
    ):
        self.layers = layers
        self.dependency_resolver = dependency_resolver
        self.layer_calculator = layer_calculator

    def get_total_stacks(self) -> int:
        """Get total number of stacks"""
        return sum(len(layer) for layer in self.layers)

    def get_layer_count(self) -> int:
        """Get number of layers"""
        return len(self.layers)

    def get_max_parallelism(self) -> int:
        """Get maximum parallelism"""
        return max(len(layer) for layer in self.layers) if self.layers else 0


class Orchestrator:
    """Main orchestration engine for multi-stack deployments"""

    def __init__(self, max_parallel: int = 3):
        """
        Initialize orchestrator

        Args:
            max_parallel: Maximum number of stacks to execute in parallel per layer
        """
        self.max_parallel = max_parallel
        self.dependency_resolver: Optional[DependencyResolver] = None
        self.layer_calculator: Optional[LayerCalculator] = None
        self.execution_engine: Optional[ExecutionEngine] = None

        # Callbacks
        self.on_stack_start: Optional[Callable[[str, int], None]] = None
        self.on_stack_complete: Optional[Callable[[str, bool, Optional[str]], None]] = None
        self.on_layer_start: Optional[Callable[[int, List[str]], None]] = None
        self.on_layer_complete: Optional[Callable[[int, bool], None]] = None

    def create_plan(
        self, stacks_config: Dict[str, dict], validate_manifest: bool = True
    ) -> OrchestrationPlan:
        """
        Create orchestration plan from stack configuration

        Args:
            stacks_config: Stack configurations from manifest
                          Format: {stack_name: {enabled: bool, dependencies: [...], layer: int}}
            validate_manifest: Whether to validate layers against manifest

        Returns:
            OrchestrationPlan

        Raises:
            CircularDependencyError: If circular dependencies detected
            ValueError: If validation errors found
        """
        logger.info("Creating orchestration plan")

        # Build dependency graph
        self.dependency_resolver = DependencyResolver()
        self.dependency_resolver.build_graph(stacks_config)

        # Check for circular dependencies
        cycles = self.dependency_resolver.detect_cycles()
        if cycles:
            cycle_str = " -> ".join(cycles[0])
            logger.error(f"Circular dependency detected: {cycle_str}")
            raise CircularDependencyError(cycles[0])

        # Calculate layers
        self.layer_calculator = LayerCalculator(self.dependency_resolver)
        layers = self.layer_calculator.calculate_layers()

        logger.info(f"Calculated {len(layers)} execution layers")
        logger.info(
            f"Total stacks: {self.dependency_resolver.get_stack_count()}, "
            f"Max parallelism: {self.layer_calculator.get_max_parallelism()}"
        )

        # Validate layers against manifest if requested
        if validate_manifest:
            errors = self.layer_calculator.validate_layers_against_manifest(
                stacks_config
            )
            if errors:
                error_msg = "\n".join(errors)
                logger.error(f"Layer validation errors:\n{error_msg}")
                raise ValueError(f"Layer validation failed:\n{error_msg}")

        return OrchestrationPlan(layers, self.dependency_resolver, self.layer_calculator)

    async def execute_plan(
        self,
        plan: OrchestrationPlan,
        stack_executor: Callable[[str], Any],
        stop_on_error: bool = True,
    ) -> ExecutionResult:
        """
        Execute orchestration plan

        Args:
            plan: Orchestration plan to execute
            stack_executor: Async function to execute a single stack
                           Should return (success: bool, error: Optional[str])
            stop_on_error: Whether to stop if a stack fails

        Returns:
            ExecutionResult
        """
        logger.info(f"Executing orchestration plan with {plan.get_total_stacks()} stacks")

        # Create execution engine with callbacks
        self.execution_engine = ExecutionEngine(
            max_parallel=self.max_parallel,
            on_stack_start=self.on_stack_start,
            on_stack_complete=self.on_stack_complete,
            on_layer_start=self.on_layer_start,
            on_layer_complete=self.on_layer_complete,
        )

        # Execute
        result = await self.execution_engine.execute_layers(
            plan.layers, stack_executor, stop_on_error
        )

        # Log summary
        logger.info(
            f"Execution complete: {result.successful_stacks}/{result.total_stacks} succeeded, "
            f"{result.failed_stacks} failed, {result.skipped_stacks} skipped"
        )

        if not result.success:
            logger.error(f"Execution failed: {result.error_message}")

        return result

    def execute_single_stack(
        self,
        stack_name: str,
        stacks_config: Dict[str, dict],
        stack_executor: Callable[[str], Any],
        check_dependencies: bool = True,
    ) -> ExecutionResult:
        """
        Execute a single stack (useful for deploy-stack command)

        Args:
            stack_name: Name of the stack to execute
            stacks_config: All stack configurations (for dependency checking)
            stack_executor: Function to execute the stack
            check_dependencies: Whether to check if dependencies are deployed

        Returns:
            ExecutionResult with single stack execution

        Raises:
            ValueError: If stack not found or dependencies not met
        """
        if stack_name not in stacks_config:
            raise ValueError(f"Stack '{stack_name}' not found in configuration")

        if not stacks_config[stack_name].get("enabled", True):
            raise ValueError(f"Stack '{stack_name}' is disabled")

        # Build dependency graph to check dependencies
        if check_dependencies:
            resolver = DependencyResolver()
            resolver.build_graph(stacks_config)
            dependencies = resolver.get_dependencies(stack_name)

            if dependencies:
                logger.info(f"Stack '{stack_name}' depends on: {', '.join(dependencies)}")
                # Note: We don't automatically check if dependencies are deployed
                # That would require querying Pulumi state, which is handled by the executor

        # Execute single stack
        async def execute():
            engine = ExecutionEngine(max_parallel=1)
            return await engine.execute_layers([[stack_name]], stack_executor, True)

        return asyncio.run(execute())

    def get_destroy_order(self, stacks_config: Dict[str, dict]) -> List[List[str]]:
        """
        Get destroy order (reverse of deploy order)

        Args:
            stacks_config: Stack configurations

        Returns:
            List of layers in reverse order
        """
        plan = self.create_plan(stacks_config, validate_manifest=False)
        return list(reversed(plan.layers))

    def validate_deployment(self, stacks_config: Dict[str, dict]) -> Dict[str, Any]:
        """
        Validate deployment configuration without executing

        Args:
            stacks_config: Stack configurations

        Returns:
            Dictionary with validation results
        """
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "info": {},
        }

        try:
            # Create plan (this validates dependencies and layers)
            plan = self.create_plan(stacks_config, validate_manifest=True)

            # Add plan info
            validation_result["info"] = {
                "total_stacks": plan.get_total_stacks(),
                "total_layers": plan.get_layer_count(),
                "max_parallelism": plan.get_max_parallelism(),
                "layers": plan.layers,
                "statistics": self.layer_calculator.get_layer_statistics() if self.layer_calculator else {},
            }

            logger.info("Deployment validation successful")

        except CircularDependencyError as e:
            validation_result["valid"] = False
            validation_result["errors"].append(str(e))
            logger.error(f"Validation failed: {e}")

        except ValueError as e:
            validation_result["valid"] = False
            validation_result["errors"].append(str(e))
            logger.error(f"Validation failed: {e}")

        except Exception as e:
            validation_result["valid"] = False
            validation_result["errors"].append(f"Unexpected error: {str(e)}")
            logger.error(f"Validation failed with unexpected error: {e}")

        return validation_result

    def print_plan(self, plan: OrchestrationPlan) -> str:
        """
        Generate human-readable plan description

        Args:
            plan: Orchestration plan

        Returns:
            String representation
        """
        lines = []
        lines.append("=" * 60)
        lines.append("ORCHESTRATION PLAN")
        lines.append("=" * 60)
        lines.append(f"Total Stacks: {plan.get_total_stacks()}")
        lines.append(f"Total Layers: {plan.get_layer_count()}")
        lines.append(f"Max Parallelism: {plan.get_max_parallelism()}")
        lines.append("")

        for layer_num, layer_stacks in enumerate(plan.layers, start=1):
            lines.append(f"Layer {layer_num} ({len(layer_stacks)} stacks):")
            for stack in sorted(layer_stacks):
                deps = plan.dependency_resolver.get_dependencies(stack)
                if deps:
                    lines.append(f"  - {stack} (depends on: {', '.join(deps)})")
                else:
                    lines.append(f"  - {stack}")
            lines.append("")

        lines.append("=" * 60)
        return "\n".join(lines)
