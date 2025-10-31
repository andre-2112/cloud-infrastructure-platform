"""
Stack Configuration Table

Rich interactive table for configuring stack deployments.
"""

from typing import Dict, List, Any, Optional
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.live import Live


class StackConfigTable:
    """
    Interactive table for stack/environment configuration

    Provides a visual interface for enabling/disabling stacks
    across multiple environments.
    """

    def __init__(
        self,
        stacks: Dict[str, Any],
        environments: List[str],
        environment_configs: Optional[Dict[str, Any]] = None,
        console: Optional[Console] = None
    ):
        """
        Initialize stack configuration table

        Args:
            stacks: Dictionary of stack configurations
            environments: List of environment names
            environment_configs: Dictionary of environment configurations
            console: Rich console instance
        """
        self.stacks = stacks
        self.environments = environments
        self.environment_configs = environment_configs or {}
        self.console = console or Console()
        self.selection_state = {}  # Track selection state
        self.current_row = 0
        self.current_col = 0

    def render(self) -> Table:
        """
        Render the configuration table

        Returns:
            Rich Table object
        """
        table = Table(title="Stack Configuration", show_header=True, header_style="bold cyan")

        # Add columns
        table.add_column("Stack", style="cyan", no_wrap=True)
        for env in self.environments:
            table.add_column(env.capitalize(), justify="center")
        table.add_column("Enabled", justify="center")

        # Add rows
        for stack_name, stack_config in self.stacks.items():
            row = [stack_name]

            # Environment columns
            for env in self.environments:
                # Check if stack is enabled for this environment
                env_config = stack_config.get("environments", {}).get(env, {})
                enabled = env_config.get("enabled", False)
                row.append("[X]" if enabled else "[ ]")

            # Stack enabled column
            stack_enabled = stack_config.get("enabled", False)
            row.append("[X]" if stack_enabled else "[ ]")

            table.add_row(*row)

        return table

    def run(self) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Run the interactive table interface (simplified version)

        Returns:
            Tuple of (updated stack configuration, updated environment configs)
        """
        from rich.prompt import Prompt
        from rich.panel import Panel

        while True:
            self.console.print("\n[bold]Stack Configuration[/bold]\n")
            self.console.print(self.render())

            # Show environment status
            if self.environment_configs:
                self.console.print("\n[bold]Environment Status:[/bold]")
                for env_name, env_config in self.environment_configs.items():
                    enabled = env_config.get("enabled", False)
                    status = "[green]enabled[/green]" if enabled else "[dim]disabled[/dim]"
                    self.console.print(f"  {env_name}: {status}")

            # Show configuration options at the bottom
            self.console.print()
            self.console.print(Panel.fit(
                "[bold]Configuration Options:[/bold]\n\n"
                "  [cyan]1[/cyan] - Enable/disable individual stacks\n"
                "  [cyan]2[/cyan] - Enable all stacks\n"
                "  [cyan]3[/cyan] - Disable all stacks\n"
                "  [cyan]4[/cyan] - Configure environments\n"
                "  [cyan]5[/cyan] - Done (save changes)\n"
                "  [cyan]6[/cyan] - Cancel (discard changes)\n",
                title="Menu",
                border_style="blue"
            ))

            choice = Prompt.ask("Choice", choices=["1", "2", "3", "4", "5", "6"], console=self.console)

            if choice == "1":
                self._configure_individual_stacks()
            elif choice == "2":
                self._enable_all_stacks()
            elif choice == "3":
                self._disable_all_stacks()
            elif choice == "4":
                self._configure_environments()
            elif choice == "5":
                return self.stacks, self.environment_configs
            elif choice == "6":
                return None, None  # Cancel

    def _configure_individual_stacks(self):
        """Configure individual stacks"""
        from rich.prompt import Prompt, Confirm

        stack_names = list(self.stacks.keys())
        self.console.print("\n[bold]Available stacks:[/bold]")
        for i, name in enumerate(stack_names, 1):
            enabled = "enabled" if self.stacks[name].get("enabled", False) else "disabled"
            self.console.print(f"  {i}. {name} ({enabled})")

        selection = Prompt.ask("\nEnter stack number (or 'done' to finish)", console=self.console)

        if selection.lower() == "done":
            return

        try:
            idx = int(selection) - 1
            if 0 <= idx < len(stack_names):
                stack_name = stack_names[idx]
                current_state = self.stacks[stack_name].get("enabled", False)
                new_state = Confirm.ask(
                    f"Enable {stack_name}?",
                    default=current_state,
                    console=self.console
                )
                self.stacks[stack_name]["enabled"] = new_state
        except ValueError:
            self.console.print("[yellow]Invalid selection[/yellow]")

    def _enable_all_stacks(self):
        """Enable all stacks"""
        for stack_config in self.stacks.values():
            stack_config["enabled"] = True
        self.console.print("[green]All stacks enabled[/green]")

    def _disable_all_stacks(self):
        """Disable all stacks"""
        for stack_config in self.stacks.values():
            stack_config["enabled"] = False
        self.console.print("[yellow]All stacks disabled[/yellow]")

    def _configure_environments(self):
        """Configure environment deployment settings"""
        from rich.prompt import Prompt, Confirm

        if not self.environment_configs:
            self.console.print("[yellow]No environments configured[/yellow]")
            return

        self.console.print("\n[bold]Available environments:[/bold]")
        env_names = list(self.environment_configs.keys())
        for i, name in enumerate(env_names, 1):
            enabled = "enabled" if self.environment_configs[name].get("enabled", False) else "disabled"
            self.console.print(f"  {i}. {name} ({enabled})")

        self.console.print(f"  {len(env_names) + 1}. Enable all")
        self.console.print(f"  {len(env_names) + 2}. Disable all")
        self.console.print(f"  {len(env_names) + 3}. Done")

        selection = Prompt.ask("\nEnter environment number (or done to finish)", console=self.console)

        if selection.lower() == "done" or selection == str(len(env_names) + 3):
            return

        try:
            idx = int(selection) - 1

            # Enable all
            if idx == len(env_names):
                for env_config in self.environment_configs.values():
                    env_config["enabled"] = True
                self.console.print("[green]All environments enabled[/green]")
                return

            # Disable all
            elif idx == len(env_names) + 1:
                for env_config in self.environment_configs.values():
                    env_config["enabled"] = False
                self.console.print("[yellow]All environments disabled[/yellow]")
                return

            # Individual environment
            elif 0 <= idx < len(env_names):
                env_name = env_names[idx]
                current_state = self.environment_configs[env_name].get("enabled", False)
                new_state = Confirm.ask(
                    f"Enable {env_name} environment for deployment?",
                    default=current_state,
                    console=self.console
                )
                self.environment_configs[env_name]["enabled"] = new_state
                status = "enabled" if new_state else "disabled"
                self.console.print(f"[green]{env_name} {status}[/green]")
        except ValueError:
            self.console.print("[yellow]Invalid selection[/yellow]")

    def _get_selection_state(self) -> Dict[str, Any]:
        """Get current selection state"""
        return {
            name: config.get("enabled", False)
            for name, config in self.stacks.items()
        }
