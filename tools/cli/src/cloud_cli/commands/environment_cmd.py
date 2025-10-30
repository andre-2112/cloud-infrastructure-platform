from cloud_cli.utils.console_utils import safe_print
"""
Environment Management Commands

Commands for managing deployment environments.
"""

import typer
from rich.console import Console
from rich.table import Table
import yaml

from cloud_core.deployment import DeploymentManager
from cloud_core.validation import ManifestValidator
from cloud_core.utils.logger import get_logger

app = typer.Typer()
console = Console()
logger = get_logger(__name__)


@app.command(name="enable-environment")
def enable_environment_command(
    deployment_id: str = typer.Argument(..., help="Deployment ID"),
    environment: str = typer.Argument(..., help="Environment (dev/stage/prod)"),
    stacks: str = typer.Option(
        None, "--stacks", help="Comma-separated list of stacks (default: all)"
    ),
) -> None:
    """Enable an environment for deployment"""

    try:
        # Load deployment
        deployment_manager = DeploymentManager()
        deployment_dir = deployment_manager.get_deployment_dir(deployment_id)

        if not deployment_dir.exists():
            console.print(f"[red]Error:[/red] Deployment {deployment_id} not found")
            raise typer.Exit(1)

        # Load manifest
        manifest_path = deployment_dir / "deployment-manifest.yaml"
        with open(manifest_path, 'r') as f:
            manifest = yaml.safe_load(f)

        # Parse stack list
        stack_list = None
        if stacks:
            stack_list = [s.strip() for s in stacks.split(',')]

        # Enable environment
        updated_count = 0
        for stack_name, stack_config in manifest.get("stacks", {}).items():
            # Skip if specific stacks requested and this isn't one of them
            if stack_list and stack_name not in stack_list:
                continue

            # Enable environment for stack
            if "environments" not in stack_config:
                stack_config["environments"] = {}

            if environment not in stack_config["environments"]:
                stack_config["environments"][environment] = {}

            stack_config["environments"][environment]["enabled"] = True
            updated_count += 1

        # Save manifest
        with open(manifest_path, 'w') as f:
            yaml.dump(manifest, f, default_flow_style=False, sort_keys=False)

        safe_print(console, f"[green]✓[/green] Enabled environment '{environment}' for {updated_count} stack(s)")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        logger.error(f"Enable-environment command failed: {e}", exc_info=True)
        raise typer.Exit(1)


@app.command(name="disable-environment")
def disable_environment_command(
    deployment_id: str = typer.Argument(..., help="Deployment ID"),
    environment: str = typer.Argument(..., help="Environment (dev/stage/prod)"),
    stacks: str = typer.Option(
        None, "--stacks", help="Comma-separated list of stacks (default: all)"
    ),
) -> None:
    """Disable an environment for deployment"""

    try:
        # Load deployment
        deployment_manager = DeploymentManager()
        deployment_dir = deployment_manager.get_deployment_dir(deployment_id)

        if not deployment_dir.exists():
            console.print(f"[red]Error:[/red] Deployment {deployment_id} not found")
            raise typer.Exit(1)

        # Load manifest
        manifest_path = deployment_dir / "deployment-manifest.yaml"
        with open(manifest_path, 'r') as f:
            manifest = yaml.safe_load(f)

        # Parse stack list
        stack_list = None
        if stacks:
            stack_list = [s.strip() for s in stacks.split(',')]

        # Disable environment
        updated_count = 0
        for stack_name, stack_config in manifest.get("stacks", {}).items():
            # Skip if specific stacks requested and this isn't one of them
            if stack_list and stack_name not in stack_list:
                continue

            # Disable environment for stack
            if "environments" in stack_config and environment in stack_config["environments"]:
                stack_config["environments"][environment]["enabled"] = False
                updated_count += 1

        # Save manifest
        with open(manifest_path, 'w') as f:
            yaml.dump(manifest, f, default_flow_style=False, sort_keys=False)

        safe_print(console, f"[green]✓[/green] Disabled environment '{environment}' for {updated_count} stack(s)")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        logger.error(f"Disable-environment command failed: {e}", exc_info=True)
        raise typer.Exit(1)


@app.command(name="list-environments")
def list_environments_command(
    deployment_id: str = typer.Argument(..., help="Deployment ID"),
) -> None:
    """List all environments and their status"""

    try:
        # Load deployment
        deployment_manager = DeploymentManager()
        deployment_dir = deployment_manager.get_deployment_dir(deployment_id)

        if not deployment_dir.exists():
            console.print(f"[red]Error:[/red] Deployment {deployment_id} not found")
            raise typer.Exit(1)

        # Load manifest
        manifest_path = deployment_dir / "deployment-manifest.yaml"
        with open(manifest_path, 'r') as f:
            manifest = yaml.safe_load(f)

        # Collect environment status
        environments = {}
        for stack_name, stack_config in manifest.get("stacks", {}).items():
            stack_enabled = stack_config.get("enabled", True)

            for env_name, env_config in stack_config.get("environments", {}).items():
                if env_name not in environments:
                    environments[env_name] = {"total": 0, "enabled": 0, "disabled": 0}

                environments[env_name]["total"] += 1

                env_enabled = env_config.get("enabled", True)
                if stack_enabled and env_enabled:
                    environments[env_name]["enabled"] += 1
                else:
                    environments[env_name]["disabled"] += 1

        # Display table
        if not environments:
            console.print("[yellow]No environments configured[/yellow]")
            return

        table = Table(title=f"Environments for {deployment_id}")
        table.add_column("Environment", style="cyan")
        table.add_column("Total Stacks", justify="right")
        table.add_column("Enabled", justify="right", style="green")
        table.add_column("Disabled", justify="right", style="red")

        for env_name in sorted(environments.keys()):
            stats = environments[env_name]
            table.add_row(
                env_name,
                str(stats["total"]),
                str(stats["enabled"]),
                str(stats["disabled"]),
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        logger.error(f"List-environments command failed: {e}", exc_info=True)
        raise typer.Exit(1)
