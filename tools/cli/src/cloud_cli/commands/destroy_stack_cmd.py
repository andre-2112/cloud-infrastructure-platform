"""
Destroy Stack Command

Destroy a single stack.
"""

import typer
from rich.console import Console
from pathlib import Path

from cloud_core.deployment import DeploymentManager, StateManager, StackStatus
from cloud_core.orchestrator import DependencyResolver
from cloud_core.pulumi import PulumiWrapper, StackOperations
from cloud_core.validation import ManifestValidator
from cloud_core.utils.logger import get_logger
from cloud_cli.utils.path_utils import get_stacks_dir
from cloud_cli.utils.console_utils import safe_print

app = typer.Typer()
console = Console()
logger = get_logger(__name__)


@app.command(name="destroy-stack")
def destroy_stack_command(
    deployment_id: str = typer.Argument(..., help="Deployment ID"),
    stack_name: str = typer.Argument(..., help="Stack name"),
    environment: str = typer.Option(
        "dev", "--environment", "-e", help="Environment (dev/stage/prod)"
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="Force destroy even if other stacks depend on it"
    ),
    yes: bool = typer.Option(
        False, "--yes", "-y", help="Skip confirmation prompt"
    ),
) -> None:
    """Destroy a single stack"""

    try:
        # Load deployment
        deployment_manager = DeploymentManager()
        deployment_dir = deployment_manager.get_deployment_dir(deployment_id)

        if deployment_dir is None or not deployment_dir.exists():
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

        # Check stack exists
        if stack_name not in manifest.get("stacks", {}):
            console.print(f"[red]Error:[/red] Stack '{stack_name}' not found in deployment")
            raise typer.Exit(1)

        # Check for dependent stacks
        if not force:
            resolver = DependencyResolver()
            dependents = resolver.get_dependents(manifest, stack_name)

            if dependents:
                console.print(f"[red]Error:[/red] The following stacks depend on '{stack_name}':")
                for dep in dependents:
                    console.print(f"  - {dep}")
                console.print("\nDestroy dependent stacks first or use --force")
                raise typer.Exit(1)

        # Confirm destruction
        if not yes:
            confirm = typer.confirm(
                f"Are you sure you want to destroy stack '{stack_name}' in {deployment_id} ({environment})?"
            )
            if not confirm:
                console.print("Destruction cancelled")
                return

        # Destroy stack
        console.print(f"\n[bold]Destroying stack {stack_name} ({environment})...[/bold]")

        state_manager = StateManager(deployment_dir)
        state_manager.set_stack_status(stack_name, StackStatus.DESTROYING, environment)

        # Get Pulumi organization (NOT deployment organization) and project from manifest
        # pulumiOrg is the Pulumi Cloud organization (e.g., "andre-2112")
        # project is the deployment project name per v4.1 architecture
        pulumi_org = manifest.get("pulumiOrg", manifest.get("organization", ""))
        project = manifest.get("project", deployment_id)  # Use deployment project name

        pulumi_wrapper = PulumiWrapper(organization=pulumi_org, project=project)
        stack_ops = StackOperations(pulumi_wrapper)

        try:
            # Get stack directory
            stack_dir = get_stacks_dir() / stack_name

            # Use deployment context for Pulumi.yaml management
            with pulumi_wrapper.deployment_context(stack_dir, stack_name):
                # Destroy within context
                success, error = stack_ops.destroy_stack(
                    deployment_id=deployment_id,
                    stack_name=stack_name,
                    environment=environment,
                    stack_dir=stack_dir,
                )
            # Pulumi.yaml automatically restored here

            if success:
                state_manager.set_stack_status(stack_name, StackStatus.DESTROYED, environment)
                safe_print(console, f"\n[green]✓[/green] Stack {stack_name} destroyed successfully")
            else:
                state_manager.set_stack_status(stack_name, StackStatus.FAILED, environment)
                safe_print(console, f"\n[red]✗[/red] Stack destruction failed: {error}")
                raise typer.Exit(1)

        except Exception as e:
            state_manager.set_stack_status(stack_name, StackStatus.FAILED, environment)
            raise e

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        logger.error(f"Destroy-stack command failed: {e}", exc_info=True)
        raise typer.Exit(1)
