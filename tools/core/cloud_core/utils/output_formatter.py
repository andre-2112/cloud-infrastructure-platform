"""
Output Formatter

Provides consistent output formatting with configurable verbosity levels.
"""

from enum import Enum
from typing import Optional
from rich.console import Console


class OutputLevel(Enum):
    """Output verbosity levels"""
    QUIET = "quiet"      # Minimal output
    NORMAL = "normal"    # Standard output (default)
    VERBOSE = "verbose"  # Detailed output


class OutputFormatter:
    """
    Manages console output with configurable verbosity

    Usage:
        formatter = OutputFormatter(level=OutputLevel.QUIET)
        formatter.info("This is info")  # Only shown in normal/verbose
        formatter.success("Done!")      # Always shown
        formatter.error("Failed!")      # Always shown
    """

    def __init__(self, level: OutputLevel = OutputLevel.NORMAL, console: Optional[Console] = None):
        """
        Initialize output formatter

        Args:
            level: Verbosity level
            console: Rich console instance (creates new if not provided)
        """
        self.level = level
        self.console = console or Console()

    def set_level(self, level: OutputLevel):
        """Set output verbosity level"""
        self.level = level

    def quiet(self, message: str, **kwargs):
        """Output message in quiet mode (always shown)"""
        self.console.print(message, **kwargs)

    def info(self, message: str, **kwargs):
        """Output info message (shown in normal and verbose)"""
        if self.level in [OutputLevel.NORMAL, OutputLevel.VERBOSE]:
            self.console.print(message, **kwargs)

    def verbose(self, message: str, **kwargs):
        """Output verbose message (only shown in verbose mode)"""
        if self.level == OutputLevel.VERBOSE:
            self.console.print(message, **kwargs)

    def success(self, message: str, **kwargs):
        """Output success message (always shown)"""
        self.console.print(f"[green][OK][/green] {message}", **kwargs)

    def error(self, message: str, **kwargs):
        """Output error message (always shown)"""
        self.console.print(f"[red][ERROR][/red] {message}", **kwargs)

    def warning(self, message: str, **kwargs):
        """Output warning message (shown in normal and verbose)"""
        if self.level in [OutputLevel.NORMAL, OutputLevel.VERBOSE]:
            self.console.print(f"[yellow]![/yellow] {message}", **kwargs)

    def section(self, title: str, **kwargs):
        """Output section header (shown in normal and verbose)"""
        if self.level in [OutputLevel.NORMAL, OutputLevel.VERBOSE]:
            self.console.print(f"\n[bold]{title}[/bold]", **kwargs)

    def detail(self, key: str, value: str):
        """Output key-value detail (shown in normal and verbose)"""
        if self.level in [OutputLevel.NORMAL, OutputLevel.VERBOSE]:
            self.console.print(f"  {key}: {value}")
