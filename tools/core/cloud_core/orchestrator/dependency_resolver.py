"""
Dependency Resolver

Builds dependency graph from stack configurations and detects circular dependencies.
Part of the orchestration engine for Architecture 3.1
"""

from typing import Dict, List, Set, Optional
from dataclasses import dataclass


@dataclass
class DependencyNode:
    """Represents a stack in the dependency graph"""

    name: str
    dependencies: List[str]
    dependents: List[str]  # Reverse dependencies (who depends on this)
    visited: bool = False
    in_path: bool = False  # For cycle detection


class CircularDependencyError(Exception):
    """Raised when circular dependencies are detected"""

    def __init__(self, cycle: List[str]):
        self.cycle = cycle
        cycle_str = " -> ".join(cycle)
        super().__init__(f"Circular dependency detected: {cycle_str}")


class DependencyResolver:
    """Resolves stack dependencies and builds execution graph"""

    def __init__(self) -> None:
        """Initialize dependency resolver"""
        self.nodes: Dict[str, DependencyNode] = {}
        self.cycles: List[List[str]] = []

    def build_graph(self, manifest_or_stacks: Dict) -> Optional[Dict[str, List[str]]]:
        """
        Build dependency graph from stack configurations or manifest

        Args:
            manifest_or_stacks: Either full manifest with 'stacks' key OR 
                               dictionary of stack configurations
                               Format: {stack_name: {enabled: bool, dependencies: [...]}}

        Returns:
            Dictionary mapping stack names to dependencies (if manifest provided),
            None (if stacks_config provided for backward compatibility)

        Raises:
            ValueError: If dependency references unknown stack
        """
        # Check if this is a full manifest or just stacks config
        if "stacks" in manifest_or_stacks:
            # It's a manifest - extract stacks and return graph
            stacks_config = manifest_or_stacks["stacks"]
            return_graph = True
        else:
            # It's just stacks config - backward compatible
            stacks_config = manifest_or_stacks
            return_graph = False

        # Clear existing nodes
        self.nodes = {}

        # First pass: Create all nodes
        for stack_name, config in stacks_config.items():
            # Only include enabled stacks
            if not config.get("enabled", True):
                continue

            dependencies = config.get("dependencies", [])
            self.nodes[stack_name] = DependencyNode(
                name=stack_name, dependencies=dependencies, dependents=[]
            )

        # Second pass: Validate dependencies and build reverse edges
        for stack_name, node in self.nodes.items():
            for dep in node.dependencies:
                if dep not in self.nodes:
                    raise ValueError(
                        f"Stack '{stack_name}' depends on unknown or disabled stack '{dep}'"
                    )
                # Add reverse dependency
                self.nodes[dep].dependents.append(stack_name)

        # Return graph if manifest was provided
        if return_graph:
            result = {}
            for stack_name, node in self.nodes.items():
                result[stack_name] = node.dependencies.copy()
            return result
        return None

    def detect_cycles(self) -> List[List[str]]:
        """
        Detect circular dependencies using DFS

        Returns:
            List of cycles found (each cycle is a list of stack names)
        """
        self.cycles = []

        # Reset visited state
        for node in self.nodes.values():
            node.visited = False
            node.in_path = False

        # Check each node
        for stack_name in self.nodes:
            if not self.nodes[stack_name].visited:
                self._dfs_detect_cycle(stack_name, [])

        return self.cycles

    def _dfs_detect_cycle(self, stack_name: str, path: List[str]) -> bool:
        """
        DFS-based cycle detection

        Args:
            stack_name: Current stack being visited
            path: Current path in DFS traversal

        Returns:
            True if cycle detected from this node
        """
        node = self.nodes[stack_name]

        if node.in_path:
            # Found a cycle - extract the cycle from path
            cycle_start = path.index(stack_name)
            cycle = path[cycle_start:] + [stack_name]
            self.cycles.append(cycle)
            return True

        if node.visited:
            return False

        # Mark as in current path
        node.in_path = True
        path.append(stack_name)

        # Visit dependencies
        for dep in node.dependencies:
            self._dfs_detect_cycle(dep, path)

        # Mark as visited and remove from path
        node.visited = True
        node.in_path = False
        path.pop()

        return False

    def get_dependency_order(self) -> List[str]:
        """
        Get stack deployment order using topological sort

        Returns:
            List of stack names in dependency order

        Raises:
            CircularDependencyError: If circular dependencies exist
        """
        # Check for cycles first
        cycles = self.detect_cycles()
        if cycles:
            # Raise error with first cycle found
            raise CircularDependencyError(cycles[0])

        # Topological sort using Kahn's algorithm
        result: List[str] = []
        in_degree: Dict[str, int] = {}

        # Calculate in-degrees
        for stack_name, node in self.nodes.items():
            in_degree[stack_name] = len(node.dependencies)

        # Queue of nodes with no dependencies
        queue: List[str] = [
            name for name, degree in in_degree.items() if degree == 0
        ]

        while queue:
            # Process node with no remaining dependencies
            current = queue.pop(0)
            result.append(current)

            # Reduce in-degree of dependents
            for dependent in self.nodes[current].dependents:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        # If not all nodes processed, there's a cycle (shouldn't happen after cycle check)
        if len(result) != len(self.nodes):
            raise CircularDependencyError(["Unknown cycle detected"])

        return result

    def get_dependencies(self, manifest_or_stack: any, stack_name: str = None) -> List[str]:
        """
        Get direct dependencies of a stack

        Args:
            manifest_or_stack: Either manifest dict (new API) or stack_name str (old API)
            stack_name: Stack name (only when first arg is manifest)

        Returns:
            List of dependency stack names
        """
        # Support both old and new API
        if isinstance(manifest_or_stack, dict):
            # New API: get_dependencies(manifest, stack_name)
            manifest = manifest_or_stack
            stacks = manifest.get("stacks", {})
            self.build_graph(stacks)
            if stack_name not in self.nodes:
                return []
            return self.nodes[stack_name].dependencies.copy()
        else:
            # Old API: get_dependencies(stack_name)
            stack_name = manifest_or_stack
            if stack_name not in self.nodes:
                return []
            return self.nodes[stack_name].dependencies.copy()

    def get_dependents(self, manifest_or_stack: any, stack_name: str = None) -> List[str]:
        """
        Get stacks that depend on the given stack

        Args:
            manifest_or_stack: Either manifest dict (new API) or stack_name str (old API)
            stack_name: Stack name (only when first arg is manifest)

        Returns:
            List of dependent stack names
        """
        # Support both old and new API
        if isinstance(manifest_or_stack, dict):
            # New API: get_dependents(manifest, stack_name)
            manifest = manifest_or_stack
            stacks = manifest.get("stacks", {})
            self.build_graph(stacks)
            if stack_name not in self.nodes:
                return []
            return self.nodes[stack_name].dependents.copy()
        else:
            # Old API: get_dependents(stack_name)
            stack_name = manifest_or_stack
            if stack_name not in self.nodes:
                return []
            return self.nodes[stack_name].dependents.copy()

    def get_all_dependencies_recursive(self, stack_name: str) -> Set[str]:
        """
        Get all dependencies of a stack recursively

        Args:
            stack_name: Name of the stack

        Returns:
            Set of all dependency stack names (direct and transitive)
        """
        if stack_name not in self.nodes:
            return set()

        result: Set[str] = set()
        self._collect_dependencies_recursive(stack_name, result)
        return result

    def _collect_dependencies_recursive(
        self, stack_name: str, result: Set[str]
    ) -> None:
        """Helper for recursive dependency collection"""
        node = self.nodes.get(stack_name)
        if not node:
            return

        for dep in node.dependencies:
            if dep not in result:
                result.add(dep)
                self._collect_dependencies_recursive(dep, result)

    def get_all_dependents_recursive(self, stack_name: str) -> Set[str]:
        """
        Get all stacks that depend on the given stack recursively

        Args:
            stack_name: Name of the stack

        Returns:
            Set of all dependent stack names (direct and transitive)
        """
        if stack_name not in self.nodes:
            return set()

        result: Set[str] = set()
        self._collect_dependents_recursive(stack_name, result)
        return result

    def _collect_dependents_recursive(
        self, stack_name: str, result: Set[str]
    ) -> None:
        """Helper for recursive dependent collection"""
        node = self.nodes.get(stack_name)
        if not node:
            return

        for dependent in node.dependents:
            if dependent not in result:
                result.add(dependent)
                self._collect_dependents_recursive(dependent, result)

    def can_deploy_stack(self, stack_name: str, deployed_stacks: Set[str]) -> bool:
        """
        Check if a stack can be deployed given the set of already deployed stacks

        Args:
            stack_name: Name of the stack to check
            deployed_stacks: Set of stack names that are already deployed

        Returns:
            True if all dependencies are deployed, False otherwise
        """
        if stack_name not in self.nodes:
            return False

        dependencies = set(self.nodes[stack_name].dependencies)
        return dependencies.issubset(deployed_stacks)

    def get_stack_count(self) -> int:
        """Get total number of stacks in the graph"""
        return len(self.nodes)

    def get_stack_names(self) -> List[str]:
        """Get list of all stack names"""
        return list(self.nodes.keys())

    # Convenience methods that match test API (stateless operation on manifest)

    def build_dependency_graph(self, manifest: Dict) -> Dict[str, List[str]]:
        """
        Build and return dependency graph from manifest

        Args:
            manifest: Full deployment manifest with 'stacks' key

        Returns:
            Dictionary mapping stack names to their dependencies
        """
        stacks = manifest.get("stacks", {})
        self.build_graph(stacks)

        # Return simple dict format for tests
        result = {}
        for stack_name, node in self.nodes.items():
            result[stack_name] = node.dependencies.copy()
        return result

    def has_cycles(self, manifest: Dict) -> bool:
        """
        Check if manifest has circular dependencies

        Args:
            manifest: Full deployment manifest with 'stacks' key

        Returns:
            True if cycles exist, False otherwise
        """
        stacks = manifest.get("stacks", {})
        self.build_graph(stacks)
        cycles = self.detect_cycles()
        return len(cycles) > 0

    def get_all_dependencies(self, manifest: Dict, stack_name: str) -> List[str]:
        """
        Get all dependencies (transitive) for a stack from manifest

        Args:
            manifest: Full deployment manifest with 'stacks' key
            stack_name: Name of the stack

        Returns:
            List of all dependency stack names (direct and transitive)
        """
        stacks = manifest.get("stacks", {})
        self.build_graph(stacks)
        deps_set = self.get_all_dependencies_recursive(stack_name)
        return list(deps_set)
