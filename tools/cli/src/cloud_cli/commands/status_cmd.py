"""
Status Command

Show deployment status and stack states.
"""

import typer
from rich.console import Console
from rich.table import Table

from cloud_core.deployment import DeploymentManager, StateManager
from cloud_core.utils.logger import get_logger

app = typer.Typer()
console = Console()
logger = get_logger(__name__)


@app.command()
def status(
    deployment_id: str = typer.Argument(..., help="Deployment ID"),
    environment: str = typer.Option(
        "dev", "--environment", "-e", help="Environment"
    ),
) -> None:
    """Show deployment status"""

    try:
        # Load deployment
        deployment_manager = DeploymentManager()
        deployment_dir = deployment_manager.get_deployment_dir(deployment_id)

        if not deployment_dir:
            console.print(f"[red]Error:[/red] Deployment {deployment_id} not found")
            raise typer.Exit(1)

        manifest = deployment_manager.load_manifest(deployment_id)
        metadata = deployment_manager.get_deployment_metadata(deployment_dir)

        # Print deployment info
        console.print()
        console.print(f"[bold]Deployment: {deployment_id}[/bold]")
        console.print(f"Organization: {metadata.get('organization')}")
        console.print(f"Project: {metadata.get('project')}")
        console.print(f"Environment: [cyan]{environment}[/cyan]")
        console.print()

        # Get state
        state_manager = StateManager(deployment_dir)
        summary = state_manager.get_deployment_summary(environment)

        console.print(f"Status: [{_get_status_color(summary['deployment_status'])}]{summary['deployment_status']}[/{_get_status_color(summary['deployment_status'])}]")
        console.print(f"Last Updated: {summary.get('last_updated', 'N/A')}")
        console.print()

        # Stack status table
        table = Table(title="Stack Status")
        table.add_column("Stack", style="cyan")
        table.add_column("Status")
        table.add_column("Enabled")

        stacks = manifest.get("stacks", {})
        stack_statuses = summary.get("stack_statuses", {})

        for stack_name, stack_config in stacks.items():
            enabled = stack_config.get("enabled", True)
            status = stack_statuses.get(stack_name, "not_deployed")

            table.add_row(
                stack_name,
                f"[{_get_status_color(status)}]{status}[/{_get_status_color(status)}]",
                "Yes" if enabled else "No"
            )

        console.print(table)
        console.print()

        # Summary
        console.print(f"Total Stacks: {summary['total_stacks']}")
        console.print(f"Deployed: [green]{summary['deployed_stacks']}[/green]")
        console.print(f"Failed: [red]{summary['failed_stacks']}[/red]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        logger.error(f"Status command failed: {e}", exc_info=True)
        raise typer.Exit(1)


def _get_status_color(status: str) -> str:
    """Get color for status"""
    status_lower = status.lower()
    if "deployed" in status_lower or "success" in status_lower:
        return "green"
    elif "failed" in status_lower or "error" in status_lower:
        return "red"
    elif "deploying" in status_lower or "progress" in status_lower:
        return "yellow"
    else:
        return "white"
