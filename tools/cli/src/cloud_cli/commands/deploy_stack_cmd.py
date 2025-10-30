"""
Deploy Stack Command

Deploy a single stack.
"""

import typer
from typing import Optional
from rich.console import Console
from pathlib import Path

from cloud_core.deployment import DeploymentManager, StateManager, ConfigGenerator, StackStatus
from cloud_core.orchestrator import DependencyResolver
from cloud_core.pulumi import PulumiWrapper, StackOperations
from cloud_core.validation import ManifestValidator
from cloud_core.utils.logger import get_logger
from cloud_cli.utils.path_utils import get_stacks_dir
from cloud_cli.utils.console_utils import safe_print

app = typer.Typer()
console = Console()
logger = get_logger(__name__)


@app.command(name="deploy-stack")
def deploy_stack_command(
    deployment_id: str = typer.Argument(..., help="Deployment ID"),
    stack_name: str = typer.Argument(..., help="Stack name"),
    environment: str = typer.Option(
        "dev", "--environment", "-e", help="Environment (dev/stage/prod)"
    ),
    skip_dependencies: bool = typer.Option(
        False, "--skip-dependencies", help="Skip dependency checks"
    ),
    preview: bool = typer.Option(
        False, "--preview", help="Preview changes without deploying"
    ),
) -> None:
    """Deploy a single stack"""

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

        stack_config = manifest["stacks"][stack_name]

        # Check stack is enabled
        if not stack_config.get("enabled", True):
            console.print(f"[yellow]Warning:[/yellow] Stack '{stack_name}' is disabled")
            raise typer.Exit(1)

        # Check environment is enabled
        env_config = stack_config.get("environments", {}).get(environment, {})
        if not env_config.get("enabled", True):
            console.print(f"[yellow]Warning:[/yellow] Stack '{stack_name}' is disabled for environment '{environment}'")
            raise typer.Exit(1)

        # Check dependencies if not skipped
        if not skip_dependencies:
            resolver = DependencyResolver()
            dependencies = resolver.get_dependencies(manifest, stack_name)

            if dependencies:
                console.print(f"[cyan]Dependencies:[/cyan] {', '.join(dependencies)}")

                # Verify dependencies are deployed
                state_manager = StateManager(deployment_dir)
                for dep in dependencies:
                    dep_state = state_manager.get_stack_state(dep, environment)
                    if dep_state.get("status") != "deployed":
                        console.print(f"[red]Error:[/red] Dependency '{dep}' is not deployed")
                        console.print(f"Deploy '{dep}' first or use --skip-dependencies")
                        raise typer.Exit(1)

        # Deploy stack
        console.print(f"\n[bold]Deploying stack {stack_name} ({environment})...[/bold]")

        state_manager = StateManager(deployment_dir)
        state_manager.set_stack_status(stack_name, StackStatus.DEPLOYING, environment)

        # Get Pulumi organization and project from manifest
        pulumi_org = manifest.get("pulumiOrg", manifest.get("organization", ""))
        project = manifest.get("project", deployment_id)  # Use deployment project name

        pulumi_wrapper = PulumiWrapper(organization=pulumi_org, project=project)
        stack_ops = StackOperations(pulumi_wrapper)

        try:
            # Get stack directory
            stack_dir = get_stacks_dir() / stack_name

            # Get stack config and convert all values to strings
            stack_custom_config = stack_config.get("config", {})

            # Build complete config with required deployment metadata
            config = {
                "project": manifest.get("project", ""),
                "environment": environment,
                "deploymentId": deployment_id,
                "pulumiOrg": manifest.get("pulumiOrg", manifest.get("organization", "")),
                "region": manifest.get("environments", {}).get(environment, {}).get("region", "us-east-1"),
            }

            # Add stack-specific config (all values as strings)
            config.update({k: str(v) for k, v in stack_custom_config.items()})

            # Use deployment context for Pulumi.yaml management
            with pulumi_wrapper.deployment_context(stack_dir, stack_name):
                # Deploy within context
                success, error = stack_ops.deploy_stack(
                    deployment_id=deployment_id,
                    stack_name=stack_name,
                    environment=environment,
                    stack_dir=stack_dir,
                    config=config,
                    preview_only=preview,
                )
            # Pulumi.yaml automatically restored here

            if success:
                state_manager.set_stack_status(stack_name, StackStatus.DEPLOYED, environment)
                safe_print(console, f"\n[green]✓[/green] Stack {stack_name} deployed successfully")
            else:
                state_manager.set_stack_status(stack_name, StackStatus.FAILED, environment)
                safe_print(console, f"\n[red]✗[/red] Stack deployment failed: {error}")
                raise typer.Exit(1)

        except Exception as e:
            state_manager.set_stack_status(stack_name, StackStatus.FAILED, environment)
            raise e

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        logger.error(f"Deploy-stack command failed: {e}", exc_info=True)
        raise typer.Exit(1)
