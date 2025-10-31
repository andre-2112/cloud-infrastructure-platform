"""
Config Command

Interactive configuration for deployments.
"""

import typer
from typing import Optional
from rich.console import Console
from pathlib import Path

from cloud_core.deployment import DeploymentManager
from cloud_core.ui import InteractivePrompt, StackConfigTable
from cloud_core.utils.logger import get_logger
from cloud_cli.utils.console_utils import safe_print

app = typer.Typer()
console = Console()
logger = get_logger(__name__)


@app.command()
def config(
    deployment_id: str = typer.Argument(..., help="Deployment ID"),
    interactive: bool = typer.Option(
        True, "--interactive/--no-interactive", help="Interactive mode"
    ),
    rich_mode: bool = typer.Option(
        False, "--rich", help="Rich table interface"
    ),
) -> None:
    """Configure deployment stacks and environments"""

    try:
        # Load deployment
        deployment_manager = DeploymentManager()
        deployment_dir = deployment_manager.get_deployment_dir(deployment_id)

        if not deployment_dir:
            console.print(f"[red]Error:[/red] Deployment {deployment_id} not found")
            raise typer.Exit(1)

        # Load manifest
        manifest = deployment_manager.load_manifest(deployment_id)

        if rich_mode:
            # Use rich table interface
            _config_rich_mode(deployment_id, manifest, deployment_manager)
        elif interactive:
            # Use simple interactive mode
            _config_interactive_mode(deployment_id, manifest, deployment_manager)
        else:
            # Show current configuration
            _show_configuration(deployment_id, manifest)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        logger.error(f"Config command failed: {e}", exc_info=True)
        raise typer.Exit(1)


def _config_interactive_mode(
    deployment_id: str,
    manifest: dict,
    deployment_manager: DeploymentManager
):
    """Simple interactive configuration mode"""
    prompt = InteractivePrompt()

    console.print(f"\n[bold]Configuration for Deployment: {deployment_id}[/bold]\n")

    # Configuration menu
    choice = prompt.choice(
        "What would you like to configure?",
        choices=["stacks", "environments", "both", "exit"],
        default="stacks"
    )

    if choice == "exit":
        return

    stacks = manifest.get("stacks", {})
    environments = list(manifest.get("environments", {}).keys())

    if choice in ["stacks", "both"]:
        # Configure stacks
        stack_names = list(stacks.keys())
        enabled_stacks = [name for name, config in stacks.items() if config.get("enabled", False)]

        selected = prompt.multi_select(
            "Select stacks to ENABLE",
            stack_names,
            defaults=enabled_stacks
        )

        # Update stack enabled status
        for stack_name in stack_names:
            stacks[stack_name]["enabled"] = stack_name in selected

        console.print(f"\n[green]✓[/green] Updated {len(selected)} enabled stacks")

    if choice in ["environments", "both"]:
        # Configure environments
        enabled_envs = [name for name, config in manifest.get("environments", {}).items() if config.get("enabled", False)]

        selected = prompt.multi_select(
            "Select environments to deploy to",
            environments,
            defaults=enabled_envs
        )

        # Update environment enabled status
        for env_name in environments:
            manifest["environments"][env_name]["enabled"] = env_name in selected

        console.print(f"\n[green]✓[/green] Updated {len(selected)} enabled environments")

    # Save changes
    if prompt.confirm("Save changes to manifest?", default=True):
        deployment_manager.save_manifest(deployment_id, manifest)
        safe_print(console, "[green]✓[/green] Configuration saved successfully!")
    else:
        console.print("[yellow]Changes discarded[/yellow]")


def _config_rich_mode(
    deployment_id: str,
    manifest: dict,
    deployment_manager: DeploymentManager
):
    """Rich table configuration mode"""
    stacks = manifest.get("stacks", {})
    environments = list(manifest.get("environments", {}).keys())
    environment_configs = manifest.get("environments", {})

    table = StackConfigTable(stacks, environments, environment_configs)
    updated_stacks, updated_environments = table.run()

    if updated_stacks is None:
        console.print("[yellow]Configuration cancelled[/yellow]")
        return

    # Update manifest with changes
    manifest["stacks"] = updated_stacks
    if updated_environments:
        manifest["environments"] = updated_environments

    # Save changes
    deployment_manager.save_manifest(deployment_id, manifest)
    safe_print(console, "[green]✓[/green] Configuration saved successfully!")


def _show_configuration(deployment_id: str, manifest: dict):
    """Show current configuration"""
    from rich.table import Table

    console.print(f"\n[bold]Configuration for Deployment: {deployment_id}[/bold]\n")

    # Show stacks
    stacks_table = Table(title="Stacks", show_header=True, header_style="bold cyan")
    stacks_table.add_column("Stack", style="cyan")
    stacks_table.add_column("Enabled", justify="center")
    stacks_table.add_column("Dependencies")

    for stack_name, stack_config in manifest.get("stacks", {}).items():
        enabled = "[X]" if stack_config.get("enabled", False) else "[ ]"
        deps = ", ".join(stack_config.get("dependencies", [])) or "none"
        stacks_table.add_row(stack_name, enabled, deps)

    console.print(stacks_table)

    # Show environments
    env_table = Table(title="\nEnvironments", show_header=True, header_style="bold cyan")
    env_table.add_column("Environment", style="cyan")
    env_table.add_column("Enabled", justify="center")
    env_table.add_column("Region")
    env_table.add_column("Account ID")

    for env_name, env_config in manifest.get("environments", {}).items():
        enabled = "[X]" if env_config.get("enabled", False) else "[ ]"
        region = env_config.get("region", "N/A")
        account = env_config.get("account_id", "N/A")
        env_table.add_row(env_name, enabled, region, account)

    console.print(env_table)

    console.print("\n[dim]Use --interactive or --rich for configuration mode[/dim]")
