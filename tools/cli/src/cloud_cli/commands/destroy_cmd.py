"""
Destroy Command

Destroy all stacks in a deployment in reverse order.
"""

import typer
import asyncio
from typing import Optional
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from pathlib import Path

from cloud_core.deployment import DeploymentManager, StateManager
from cloud_core.orchestrator import Orchestrator
from cloud_core.pulumi import PulumiWrapper
from cloud_core.validation import ManifestValidator
from cloud_core.utils.logger import get_logger

app = typer.Typer()
console = Console()
logger = get_logger(__name__)


@app.command(name="destroy")
def destroy_command(
    deployment_id: str = typer.Argument(..., help="Deployment ID"),
    environment: str = typer.Option(
        "dev", "--environment", "-e", help="Environment (dev/stage/prod)"
    ),
    yes: bool = typer.Option(
        False, "--yes", "-y", help="Skip confirmation prompt"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would be destroyed without destroying"
    ),
) -> None:
    """Destroy all stacks in a deployment (reverse order)"""

    try:
        # Load deployment
        deployment_manager = DeploymentManager()
        deployment_dir = deployment_manager.get_deployment_dir(deployment_id)

        if not deployment_dir.exists():
            console.print(f"[red]Error:[/red] Deployment {deployment_id} not found")
            raise typer.Exit(1)

        # Load manifest
        manifest_path = deployment_dir / "deployment-manifest.yaml"
        validator = ManifestValidator()

        if not validator.validate(str(manifest_path)):
            console.print("[red]Error:[/red] Invalid deployment manifest")
            for error in validator.errors:
                console.print(f"  - {error}")
            raise typer.Exit(1)

        manifest = validator.manifest

        # Create orchestrator
        orchestrator = Orchestrator()

        # Build reverse orchestration plan (destroy in reverse order)
        console.print("\n[bold]Building destroy plan...[/bold]")
        plan = orchestrator.create_destroy_plan(manifest, environment)

        if not plan.layers:
            console.print("[yellow]No stacks to destroy[/yellow]")
            return

        # Display plan
        console.print(f"\n[bold]Destroy plan for {deployment_id} ({environment}):[/bold]")
        console.print(f"Total stacks: {plan.total_stacks}")
        console.print(f"Layers: {len(plan.layers)}")
        console.print()

        for i, layer in enumerate(plan.layers, 1):
            console.print(f"Layer {i}: {', '.join(layer.stacks)}")

        if dry_run:
            console.print("\n[yellow]Dry run - no resources will be destroyed[/yellow]")
            return

        # Confirm destruction
        if not yes:
            console.print()
            confirm = typer.confirm(
                f"Are you sure you want to destroy all stacks in {deployment_id} ({environment})?"
            )
            if not confirm:
                console.print("Destruction cancelled")
                return

        # Execute destroy
        console.print("\n[bold]Destroying stacks...[/bold]")

        state_manager = StateManager(deployment_dir)
        state_manager.start_operation("destroy", environment)

        async def run_destroy():
            try:
                await orchestrator.execute_destroy(
                    plan=plan,
                    deployment_id=deployment_id,
                    environment=environment,
                    pulumi_wrapper=PulumiWrapper(),
                    state_manager=state_manager,
                )
                return True
            except Exception as e:
                logger.error(f"Destroy failed: {e}")
                return False

        success = asyncio.run(run_destroy())

        if success:
            state_manager.complete_operation("destroy", success=True)
            console.print(f"\n[green]✓[/green] Deployment {deployment_id} ({environment}) destroyed successfully")
        else:
            state_manager.complete_operation("destroy", success=False)
            console.print(f"\n[red]✗[/red] Destroy failed - see logs for details")
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        logger.error(f"Destroy command failed: {e}", exc_info=True)
        raise typer.Exit(1)
