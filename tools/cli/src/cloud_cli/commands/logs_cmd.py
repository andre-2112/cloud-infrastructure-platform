"""
Logs and Monitoring Commands
"""

import typer
from rich.console import Console
from pathlib import Path
import boto3
from typing import Optional

from cloud_core.deployment import DeploymentManager, StateManager
from cloud_core.utils.logger import get_logger

app = typer.Typer()
console = Console()
logger = get_logger(__name__)


@app.command(name="logs")
def logs_command(
    deployment_id: str = typer.Argument(..., help="Deployment ID"),
    stack_name: Optional[str] = typer.Option(None, "--stack", "-s", help="Filter by stack"),
    environment: Optional[str] = typer.Option(None, "--environment", "-e", help="Filter by environment"),
    tail: int = typer.Option(50, "--tail", "-n", help="Number of log lines"),
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow log output"),
) -> None:
    """View deployment logs"""

    try:
        deployment_manager = DeploymentManager()
        deployment_dir = deployment_manager.get_deployment_dir(deployment_id)

        if not deployment_dir.exists():
            console.print(f"[red]Error:[/red] Deployment {deployment_id} not found")
            raise typer.Exit(1)

        logs_dir = deployment_dir / "logs"

        if not logs_dir.exists():
            console.print(f"[yellow]No logs found for {deployment_id}[/yellow]")
            return

        # Find log files
        if stack_name and environment:
            pattern = f"{deployment_id}-{stack_name}-{environment}-*.log"
        elif stack_name:
            pattern = f"{deployment_id}-{stack_name}-*-*.log"
        elif environment:
            pattern = f"{deployment_id}-*-{environment}-*.log"
        else:
            pattern = "*.log"

        log_files = sorted(logs_dir.glob(pattern))

        if not log_files:
            console.print(f"[yellow]No logs match the filter criteria[/yellow]")
            return

        # Display logs
        if follow:
            console.print("[yellow]Follow mode not yet implemented[/yellow]")
            console.print("Showing last logs instead:\n")

        for log_file in log_files[-tail:]:
            console.print(f"[bold cyan]{'='*60}[/bold cyan]")
            console.print(f"[bold]Log: {log_file.name}[/bold]")
            console.print(f"[bold cyan]{'='*60}[/bold cyan]")

            with open(log_file, 'r') as f:
                lines = f.readlines()
                for line in lines[-tail:]:
                    console.print(line.rstrip())

            console.print()

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        logger.error(f"Logs command failed: {e}", exc_info=True)
        raise typer.Exit(1)


@app.command(name="discover-resources")
def discover_resources_command(
    deployment_id: str = typer.Argument(..., help="Deployment ID"),
    environment: str = typer.Option("dev", "--environment", "-e"),
    resource_type: Optional[str] = typer.Option(None, "--type", "-t", help="Resource type filter"),
) -> None:
    """Discover AWS resources for a deployment"""

    try:
        from rich.table import Table

        console.print(f"[bold]Discovering resources for {deployment_id} ({environment})...[/bold]\n")

        deployment_manager = DeploymentManager()
        deployment_dir = deployment_manager.get_deployment_dir(deployment_id)

        if not deployment_dir.exists():
            console.print(f"[red]Error:[/red] Deployment {deployment_id} not found")
            raise typer.Exit(1)

        # Get deployment state
        state_manager = StateManager(deployment_dir)
        deployment_state = state_manager.get_deployment_state(environment)

        if not deployment_state or not deployment_state.get("stacks"):
            console.print(f"[yellow]No deployed stacks found for {environment}[/yellow]")
            return

        # Query Pulumi for resources (simplified)
        table = Table(title=f"Resources in {deployment_id} ({environment})")
        table.add_column("Stack", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Last Update")

        for stack_name, stack_state in deployment_state.get("stacks", {}).items():
            table.add_row(
                stack_name,
                stack_state.get("status", "unknown"),
                stack_state.get("last_update", "N/A"),
            )

        console.print(table)
        console.print("\n[yellow]Note:[/yellow] Detailed resource discovery requires Pulumi Automation API")
        console.print("Use: pulumi stack --stack <deployment-id>-<stack>-<env> --show-urns")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        logger.error(f"Discover-resources command failed: {e}", exc_info=True)
        raise typer.Exit(1)
