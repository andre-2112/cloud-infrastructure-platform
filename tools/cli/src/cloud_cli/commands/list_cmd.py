"""
List Command

List all deployments.
"""

import typer
import subprocess
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
from rich.panel import Panel

from cloud_core.deployment import DeploymentManager, StateManager
from cloud_core.utils.logger import get_logger

app = typer.Typer()
console = Console()
logger = get_logger(__name__)


@app.command(name="list")
def list_command(
    rich: bool = typer.Option(False, "--rich", help="Interactive mode with actions"),
    all: bool = typer.Option(False, "--all", help="Show all deployments including destroyed ones")
) -> None:
    """List all deployments"""

    try:
        deployment_manager = DeploymentManager()
        all_deployments = deployment_manager.list_deployments()

        if not all_deployments:
            console.print("[yellow]No deployments found[/yellow]")
            return

        # Filter deployments if not showing all
        if not all:
            deployments = [d for d in all_deployments if d.get("status", "").lower() != "destroyed"]
        else:
            deployments = all_deployments

        if not deployments:
            console.print("[yellow]No active deployments found. Use --all to see destroyed deployments.[/yellow]")
            return

        if rich:
            # Interactive rich mode with actions
            _list_rich_mode(deployments, deployment_manager)
        else:
            # Standard table view
            _list_standard_mode(deployments)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        logger.error(f"List command failed: {e}", exc_info=True)
        raise typer.Exit(1)


def _list_standard_mode(deployments):
    """Standard table list view"""
    table = Table(title="Deployments", show_header=True, header_style="bold magenta")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Organization")
    table.add_column("Project")
    table.add_column("Status")
    table.add_column("Created")

    for deployment in deployments:
        status = deployment.get("status", "unknown")
        status_color = _get_status_color(status)

        table.add_row(
            deployment.get("deployment_id", "N/A"),
            deployment.get("organization", "N/A"),
            deployment.get("project", "N/A"),
            f"[{status_color}]{status}[/{status_color}]",
            deployment.get("created_at", "N/A")[:10] if deployment.get("created_at") else "N/A",
        )

    console.print()
    console.print(table)
    console.print()
    console.print(f"Total: {len(deployments)} deployment(s)")
    console.print()


def _list_rich_mode(deployments, deployment_manager):
    """Interactive rich mode with deployment table and actions"""
    while True:
        # Clear screen and show header
        console.print()

        # Create deployment table (same format as standard mode)
        table = Table(title="Deployments", show_header=True, header_style="bold magenta")
        table.add_column("#", style="dim", width=4)
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Organization")
        table.add_column("Project")
        table.add_column("Status")
        table.add_column("Created")

        for i, deployment in enumerate(deployments, 1):
            status = deployment.get("status", "unknown")
            status_color = _get_status_color(status)

            table.add_row(
                str(i),
                deployment.get("deployment_id", "N/A"),
                deployment.get("organization", "N/A"),
                deployment.get("project", "N/A"),
                f"[{status_color}]{status}[/{status_color}]",
                deployment.get("created_at", "N/A")[:10] if deployment.get("created_at") else "N/A",
            )

        console.print(table)
        console.print()
        console.print(f"Total: {len(deployments)} deployment(s)")
        console.print()

        # Show action menu
        console.print(Panel.fit(
            "[bold]Actions:[/bold]\n\n"
            "  [cyan]<number>[/cyan]  - Select deployment\n"
            "  [cyan]0[/cyan]         - Exit\n",
            title="Menu",
            border_style="blue"
        ))

        # Get user selection
        choice = Prompt.ask(
            "Select deployment (or 0 to exit)",
            default="0"
        )

        if choice == "0":
            break

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(deployments):
                deployment = deployments[idx]
                dep_id = deployment.get("deployment_id")

                # Show actions menu for selected deployment
                action_result = _show_deployment_actions(dep_id, deployment, deployment_manager)

                if action_result == "exit":
                    break
            else:
                console.print("[yellow]Invalid selection. Please try again.[/yellow]")
                console.print()
                Prompt.ask("Press Enter to continue", default="")
        except ValueError:
            console.print("[yellow]Invalid input. Please enter a number.[/yellow]")
            console.print()
            Prompt.ask("Press Enter to continue", default="")


def _show_deployment_actions(deployment_id: str, deployment: dict, deployment_manager: DeploymentManager):
    """Show actions menu for a selected deployment"""
    while True:
        console.print()
        console.print(f"[bold cyan]Selected:[/bold cyan] {deployment_id}")
        console.print(f"Organization: {deployment.get('organization')}")
        console.print(f"Project: {deployment.get('project')}")
        console.print(f"Status: {deployment.get('status')}")
        console.print()

        # Show available actions
        console.print(Panel.fit(
            "[bold]Available Actions:[/bold]\n\n"
            "  [cyan]1[/cyan] - View Status\n"
            "  [cyan]2[/cyan] - View Config\n"
            "  [cyan]3[/cyan] - Deploy\n"
            "  [cyan]4[/cyan] - Destroy\n"
            "  [cyan]0[/cyan] - Back to list\n",
            title=f"Actions for {deployment_id}",
            border_style="green"
        ))

        action = Prompt.ask(
            "Select action",
            choices=["0", "1", "2", "3", "4"],
            default="0"
        )

        if action == "0":
            return "back"
        elif action == "1":
            _show_deployment_status(deployment_id, deployment_manager)
            console.print()
            Prompt.ask("Press Enter to continue", default="")
        elif action == "2":
            _run_cloud_config(deployment_id)
            console.print()
            Prompt.ask("Press Enter to continue", default="")
        elif action == "3":
            confirm = Prompt.ask(
                f"Deploy {deployment_id}? This will start deployment",
                choices=["y", "n"],
                default="n"
            )
            if confirm == "y":
                _run_cloud_deploy(deployment_id)
            console.print()
            Prompt.ask("Press Enter to continue", default="")
        elif action == "4":
            confirm = Prompt.ask(
                f"[red]Destroy {deployment_id}?[/red] This will delete all resources!",
                choices=["y", "n"],
                default="n"
            )
            if confirm == "y":
                _run_cloud_destroy(deployment_id)
            console.print()
            Prompt.ask("Press Enter to continue", default="")


def _run_cloud_config(deployment_id: str):
    """Run cloud config command"""
    try:
        console.print()
        subprocess.run(["cloud", "config", deployment_id, "--rich"], check=True)
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error running config:[/red] {e}")
    except FileNotFoundError:
        console.print("[red]Error:[/red] 'cloud' command not found")


def _run_cloud_deploy(deployment_id: str):
    """Run cloud deploy command"""
    try:
        console.print()
        subprocess.run(["cloud", "deploy", deployment_id, "--yes"], check=True)
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error running deploy:[/red] {e}")
    except FileNotFoundError:
        console.print("[red]Error:[/red] 'cloud' command not found")


def _run_cloud_destroy(deployment_id: str):
    """Run cloud destroy command"""
    try:
        console.print()
        subprocess.run(["cloud", "destroy", deployment_id, "--yes"], check=True)
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error running destroy:[/red] {e}")
    except FileNotFoundError:
        console.print("[red]Error:[/red] 'cloud' command not found")


def _show_deployment_status(deployment_id: str, deployment_manager: DeploymentManager, environment: str = "dev"):
    """Show detailed status for a deployment"""
    try:
        deployment_dir = deployment_manager.get_deployment_dir(deployment_id)

        if not deployment_dir:
            console.print(f"[red]Error:[/red] Deployment {deployment_id} not found")
            return

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

        status = summary['deployment_status']
        status_color = _get_status_color(status)
        console.print(f"Status: [{status_color}]{status}[/{status_color}]")
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
            stack_status = stack_statuses.get(stack_name, "not_deployed")
            stack_status_color = _get_status_color(stack_status)

            table.add_row(
                stack_name,
                f"[{stack_status_color}]{stack_status}[/{stack_status_color}]",
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
        logger.error(f"Status display failed: {e}", exc_info=True)


def _get_status_color(status: str) -> str:
    """Get color for status"""
    status_lower = status.lower()
    if "deployed" in status_lower or "success" in status_lower:
        return "green"
    elif "failed" in status_lower or "error" in status_lower:
        return "red"
    elif "partial" in status_lower or "deploying" in status_lower or "progress" in status_lower:
        return "yellow"
    elif "destroyed" in status_lower:
        return "dim"
    else:
        return "white"
