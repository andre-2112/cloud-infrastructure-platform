"""
Layer Calculator

Calculates execution layers from dependency graph for parallel execution.
Stacks in the same layer can be deployed in parallel as they have no dependencies on each other.
"""

from typing import Dict, List, Set
from .dependency_resolver import DependencyResolver


class LayerCalculator:
    """Calculates execution layers for parallel deployment"""

    def __init__(self, dependency_resolver: DependencyResolver = None) -> None:
        """
        Initialize layer calculator

        Args:
            dependency_resolver: Optional initialized dependency resolver with graph built
        """
        self.resolver = dependency_resolver
        self.layers: List[List[str]] = []

    def calculate_layers(self, dependency_graph: Dict[str, List[str]] = None) -> List[List[str]]:
        """
        Calculate execution layers using modified topological sort

        Args:
            dependency_graph: Optional dependency graph dict {stack: [dependencies]}
                             If provided, uses this instead of resolver

        Returns:
            List of layers, where each layer is a list of stack names
            Layer 1: Stacks with no dependencies
            Layer N: Stacks depending only on stacks in layers < N

        Algorithm:
        1. Start with stacks that have no dependencies (layer 1)
        2. For each subsequent layer:
           - Find stacks whose dependencies are all in previous layers
           - Add them to current layer
        3. Repeat until all stacks are assigned
        """
        self.layers = []

        # Get dependency information
        if dependency_graph is not None:
            # Use provided dependency graph (new API)
            all_stacks = set(dependency_graph.keys())
            def get_deps(stack): return dependency_graph.get(stack, [])
        elif self.resolver is not None:
            # Use resolver (old API)
            all_stacks = set(self.resolver.get_stack_names())
            def get_deps(stack): return self.resolver.get_dependencies(stack)
        else:
            # No data source available
            return self.layers

        if not all_stacks:
            return self.layers

        # Track which stacks have been assigned to layers
        assigned_stacks: Set[str] = set()

        while len(assigned_stacks) < len(all_stacks):
            current_layer: List[str] = []

            # Find stacks that can be in this layer
            for stack_name in all_stacks:
                if stack_name in assigned_stacks:
                    continue

                # Get dependencies
                dependencies = set(get_deps(stack_name))

                # Stack can be in this layer if all dependencies are assigned
                if dependencies.issubset(assigned_stacks):
                    current_layer.append(stack_name)

            # If no stacks can be added, something is wrong (shouldn't happen after cycle check)
            if not current_layer:
                raise RuntimeError(
                    "Cannot calculate layers - possible undetected cycle"
                )

            # Add layer and mark stacks as assigned
            self.layers.append(current_layer)
            assigned_stacks.update(current_layer)

        return self.layers

    def get_layers(self) -> List[List[str]]:
        """
        Get calculated layers

        Returns:
            List of layers (empty if calculate_layers not called yet)
        """
        return self.layers.copy()

    def get_layer_count(self) -> int:
        """Get number of layers"""
        return len(self.layers)

    def get_layer_for_stack(self, stack_name: str) -> int:
        """
        Get layer number for a specific stack

        Args:
            stack_name: Name of the stack

        Returns:
            Layer number (1-indexed), or -1 if not found
        """
        for layer_num, layer_stacks in enumerate(self.layers, start=1):
            if stack_name in layer_stacks:
                return layer_num
        return -1

    def get_stacks_in_layer(self, layer_num: int) -> List[str]:
        """
        Get stacks in a specific layer

        Args:
            layer_num: Layer number (1-indexed)

        Returns:
            List of stack names in that layer, or empty list if invalid layer
        """
        if layer_num < 1 or layer_num > len(self.layers):
            return []
        return self.layers[layer_num - 1].copy()

    def get_max_parallelism(self) -> int:
        """
        Get maximum number of stacks that can be deployed in parallel

        Returns:
            Maximum layer size
        """
        if not self.layers:
            return 0
        return max(len(layer) for layer in self.layers)

    def validate_layers_against_manifest(
        self, stacks_config: Dict[str, dict]
    ) -> List[str]:
        """
        Validate calculated layers against explicit layer assignments in manifest

        Args:
            stacks_config: Stack configurations from manifest with 'layer' field

        Returns:
            List of validation errors (empty if valid)
        """
        errors: List[str] = []

        for stack_name, config in stacks_config.items():
            # Skip disabled stacks
            if not config.get("enabled", True):
                continue

            # Get explicit layer from manifest
            manifest_layer = config.get("layer")
            if manifest_layer is None:
                continue

            # Get calculated layer
            calculated_layer = self.get_layer_for_stack(stack_name)

            if calculated_layer == -1:
                errors.append(f"Stack '{stack_name}' not found in calculated layers")
                continue

            # Check if manifest layer matches or is valid
            if manifest_layer < calculated_layer:
                errors.append(
                    f"Stack '{stack_name}' assigned to layer {manifest_layer} in manifest, "
                    f"but dependencies require it to be in layer {calculated_layer} or later"
                )
            elif manifest_layer > calculated_layer:
                # This is actually okay - stack can be in a later layer than minimum required
                # But we might want to warn about sub-optimal placement
                pass

        return errors

    def get_layer_statistics(self) -> Dict[str, any]:
        """
        Get statistics about the layers

        Returns:
            Dictionary with layer statistics
        """
        if not self.layers:
            return {
                "total_layers": 0,
                "total_stacks": 0,
                "max_parallelism": 0,
                "min_layer_size": 0,
                "avg_layer_size": 0.0,
            }

        layer_sizes = [len(layer) for layer in self.layers]
        total_stacks = sum(layer_sizes)

        return {
            "total_layers": len(self.layers),
            "total_stacks": total_stacks,
            "max_parallelism": max(layer_sizes),
            "min_layer_size": min(layer_sizes),
            "avg_layer_size": total_stacks / len(self.layers),
            "layer_sizes": layer_sizes,
        }

    def print_layers(self) -> str:
        """
        Generate a human-readable representation of layers

        Returns:
            String representation of layers
        """
        if not self.layers:
            return "No layers calculated"

        lines = []
        lines.append(f"Total Layers: {len(self.layers)}")
        lines.append("")

        for layer_num, layer_stacks in enumerate(self.layers, start=1):
            lines.append(f"Layer {layer_num} ({len(layer_stacks)} stacks):")
            for stack in sorted(layer_stacks):
                lines.append(f"  - {stack}")
            lines.append("")

        return "\n".join(lines)
