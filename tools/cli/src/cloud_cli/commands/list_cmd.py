"""
List Command

List all deployments.
"""

import typer
from rich.console import Console
from rich.table import Table

from cloud_core.deployment import DeploymentManager
from cloud_core.utils.logger import get_logger

app = typer.Typer()
console = Console()
logger = get_logger(__name__)


@app.command(name="list")
def list_command() -> None:
    """List all deployments"""

    try:
        deployment_manager = DeploymentManager()
        deployments = deployment_manager.list_deployments()

        if not deployments:
            console.print("[yellow]No deployments found[/yellow]")
            return

        # Create table
        table = Table(title="Deployments")
        table.add_column("Deployment ID", style="cyan")
        table.add_column("Organization")
        table.add_column("Project")
        table.add_column("Status")
        table.add_column("Created")

        for deployment in deployments:
            table.add_row(
                deployment.get("deployment_id", "N/A"),
                deployment.get("organization", "N/A"),
                deployment.get("project", "N/A"),
                deployment.get("status", "unknown"),
                deployment.get("created_at", "N/A")[:10] if deployment.get("created_at") else "N/A",
            )

        console.print()
        console.print(table)
        console.print()
        console.print(f"Total: {len(deployments)} deployment(s)")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        logger.error(f"List command failed: {e}", exc_info=True)
        raise typer.Exit(1)
