"""
Dependency Validator

Validates stack dependencies and detects circular dependencies.
"""

from typing import Dict, List, Any
from ..orchestrator import DependencyResolver, CircularDependencyError
from ..utils.logger import get_logger

logger = get_logger(__name__)


class DependencyValidator:
    """Validates stack dependencies"""

    def __init__(self):
        """Initialize dependency validator"""
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate(self, stacks_config: Dict[str, dict]) -> bool:
        """
        Validate stack dependencies

        Args:
            stacks_config: Stack configurations from manifest

        Returns:
            True if valid, False otherwise
        """
        self.errors = []
        self.warnings = []

        try:
            # Use dependency resolver to check
            resolver = DependencyResolver()
            resolver.build_graph(stacks_config)

            # Check for circular dependencies
            cycles = resolver.detect_cycles()

            if cycles:
                for cycle in cycles:
                    cycle_str = " -> ".join(cycle)
                    self.errors.append(f"Circular dependency: {cycle_str}")
                return False

            # Validate dependency order
            try:
                order = resolver.get_dependency_order()
                logger.info(f"Valid dependency order with {len(order)} stacks")
            except CircularDependencyError as e:
                self.errors.append(str(e))
                return False

            return True

        except ValueError as e:
            self.errors.append(str(e))
            return False
        except Exception as e:
            self.errors.append(f"Unexpected error: {e}")
            return False

    def get_errors(self) -> List[str]:
        """Get validation errors"""
        return self.errors

    def get_warnings(self) -> List[str]:
        """Get validation warnings"""
        return self.warnings
