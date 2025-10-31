"""
Interactive Prompts

Provides interactive prompt utilities for CLI commands.
"""

from typing import List, Optional, Dict, Any
from rich.prompt import Prompt, Confirm
from rich.console import Console


class InteractivePrompt:
    """
    Interactive prompt utilities using Rich

    Provides methods for gathering user input interactively
    """

    def __init__(self, console: Optional[Console] = None):
        """Initialize interactive prompt helper"""
        self.console = console or Console()

    def text(
        self,
        prompt: str,
        default: Optional[str] = None,
        required: bool = False
    ) -> str:
        """
        Prompt for text input

        Args:
            prompt: Prompt message
            default: Default value
            required: Whether input is required

        Returns:
            User input string
        """
        while True:
            result = Prompt.ask(prompt, default=default, console=self.console)
            if result or not required:
                return result
            self.console.print("[red]This field is required[/red]")

    def confirm(self, prompt: str, default: bool = False) -> bool:
        """
        Prompt for yes/no confirmation

        Args:
            prompt: Prompt message
            default: Default value

        Returns:
            Boolean response
        """
        return Confirm.ask(prompt, default=default, console=self.console)

    def choice(
        self,
        prompt: str,
        choices: List[str],
        default: Optional[str] = None
    ) -> str:
        """
        Prompt for single choice from list

        Args:
            prompt: Prompt message
            choices: List of available choices
            default: Default choice

        Returns:
            Selected choice
        """
        return Prompt.ask(
            prompt,
            choices=choices,
            default=default,
            console=self.console
        )

    def multi_select(
        self,
        prompt: str,
        choices: List[str],
        defaults: Optional[List[str]] = None
    ) -> List[str]:
        """
        Prompt for multiple selections

        Args:
            prompt: Prompt message
            choices: List of available choices
            defaults: Default selections

        Returns:
            List of selected choices
        """
        self.console.print(f"\n{prompt}")
        self.console.print("[dim]Select items (enter numbers separated by commas, or 'all' for all items)[/dim]")

        # Display choices
        for i, choice in enumerate(choices, 1):
            marker = "✓" if defaults and choice in defaults else " "
            self.console.print(f"  {i}. [{marker}] {choice}")

        # Get selection
        selection = Prompt.ask(
            "\nSelection",
            default="all" if defaults and len(defaults) == len(choices) else "",
            console=self.console
        )

        if selection.lower() == "all":
            return choices

        if not selection:
            return defaults or []

        # Parse comma-separated numbers
        try:
            indices = [int(x.strip()) for x in selection.split(",")]
            return [choices[i-1] for i in indices if 1 <= i <= len(choices)]
        except (ValueError, IndexError):
            self.console.print("[yellow]Invalid selection, using defaults[/yellow]")
            return defaults or []
