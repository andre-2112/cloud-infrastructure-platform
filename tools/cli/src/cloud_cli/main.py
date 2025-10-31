#!/usr/bin/env python3
"""
Cloud Infrastructure Orchestration Platform CLI

Main entry point for the cloud CLI tool.
Version: 0.7.0
Architecture: 4.1
"""

import sys
from typing import Optional
import typer
from rich.console import Console
from rich import print as rprint

# Import command modules
from .commands import (
    init_cmd,
    deploy_cmd,
    deploy_stack_cmd,
    destroy_cmd,
    destroy_stack_cmd,
    rollback_cmd,
    status_cmd,
    list_cmd,
    environment_cmd,
    stack_cmd,
    template_cmd,
    validate_cmd,
    logs_cmd,
)

# Create main Typer app
app = typer.Typer(
    name="cloud",
    help="Cloud Infrastructure Orchestration Platform CLI v0.7 (Architecture 4.1)",
    no_args_is_help=True,
    add_completion=True,
    rich_markup_mode="rich",
)

# Console for rich output
console = Console()

# Global options callback
@app.callback()
def main(
    ctx: typer.Context,
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    debug: bool = typer.Option(False, "--debug", help="Enable debug mode"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress non-error output"),
    no_color: bool = typer.Option(False, "--no-color", help="Disable colored output"),
) -> None:
    """
    Cloud Infrastructure Orchestration Platform CLI

    Manage cloud infrastructure deployments using Multi-Stack Architecture 4.1
    """
    # Store global options in context
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["debug"] = debug
    ctx.obj["quiet"] = quiet
    ctx.obj["no_color"] = no_color

    if no_color:
        console.no_color = True

    if debug:
        console.print("[yellow]Debug mode enabled[/yellow]")


@app.command()
def version() -> None:
    """Show version information"""
    rprint("[bold]Cloud Infrastructure Orchestration Platform CLI[/bold]")
    rprint(f"Version: [cyan]0.7.0[/cyan]")
    rprint(f"Architecture: [cyan]4.1[/cyan]")
    rprint(f"Python: [cyan]{sys.version.split()[0]}[/cyan]")


# Register command modules
# Note: When adding single-command Typer apps, DON'T specify a name to avoid repetition

# Deployment lifecycle
app.add_typer(init_cmd.app, help="Initialize a new deployment")
app.add_typer(deploy_cmd.app, help="Deploy all stacks")
app.add_typer(deploy_stack_cmd.app, help="Deploy a single stack")
app.add_typer(destroy_cmd.app, help="Destroy all stacks")
app.add_typer(destroy_stack_cmd.app, help="Destroy a single stack")
app.add_typer(rollback_cmd.app, help="Rollback deployment")

# Status and monitoring
app.add_typer(status_cmd.app, help="Show deployment status")
app.add_typer(list_cmd.app, help="List all deployments")
app.add_typer(logs_cmd.app, help="View deployment logs")

# Environment management
app.add_typer(environment_cmd.app, name="enable-environment", help="Enable an environment")
app.add_typer(environment_cmd.app, name="disable-environment", help="Disable an environment")
app.add_typer(environment_cmd.app, name="list-environments", help="List environments")

# Stack management
app.add_typer(stack_cmd.app, name="register-stack", help="Register a new stack")
app.add_typer(stack_cmd.app, name="update-stack", help="Update a stack")
app.add_typer(stack_cmd.app, name="unregister-stack", help="Unregister a stack")
app.add_typer(stack_cmd.app, name="list-stacks", help="List registered stacks")
app.add_typer(stack_cmd.app, name="validate-stack", help="Validate a stack")

# Template management
app.add_typer(template_cmd.app, name="list-templates", help="List deployment templates")
app.add_typer(template_cmd.app, name="show-template", help="Show template contents")
app.add_typer(template_cmd.app, name="create-template", help="Create a new template")
app.add_typer(template_cmd.app, name="update-template", help="Update a template")
app.add_typer(template_cmd.app, name="validate-template", help="Validate a template")

# Validation
app.add_typer(validate_cmd.app, name="validate", help="Validation commands")


# Entry point
def run() -> None:
    """Main entry point for the CLI"""
    app()


if __name__ == "__main__":
    run()
