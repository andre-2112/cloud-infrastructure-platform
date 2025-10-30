from cloud_cli.utils.console_utils import safe_print
"""
Deploy Command

Deploy all stacks in a deployment using orchestration.
"""

import typer
import asyncio
from typing import Optional
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from pathlib import Path

from cloud_core.deployment import DeploymentManager, StateManager, ConfigGenerator, StackStatus
from cloud_core.orchestrator import Orchestrator
from cloud_core.pulumi import PulumiWrapper, StackOperations
from cloud_core.validation import ManifestValidator, DependencyValidator
from cloud_core.validation.stack_code_validator import StackCodeValidator
from cloud_core.utils.logger import get_logger

app = typer.Typer()
console = Console()
logger = get_logger(__name__)


@app.command(name="deploy")
def deploy_command(
    deployment_id: str = typer.Argument(..., help="Deployment ID"),
    environment: str = typer.Option(
        "dev", "--environment", "-e", help="Environment (dev/stage/prod)"
    ),
    preview: bool = typer.Option(
        False, "--preview", help="Preview changes without deploying"
    ),
    parallel: int = typer.Option(
        3, "--parallel", "-p", help="Maximum parallel stack deployments"
    ),
    validate_code: bool = typer.Option(
        True, "--validate-code/--no-validate-code", help="Validate stack code against templates"
    ),
    strict: bool = typer.Option(
        False, "--strict", help="Enable strict validation"
    ),
) -> None:
    """Deploy all stacks in a deployment (Enhanced with code validation)"""

    try:
        # Load deployment
        deployment_manager = DeploymentManager()
        deployment_dir = deployment_manager.get_deployment_dir(deployment_id)

        if not deployment_dir:
            console.print(f"[red]Error:[/red] Deployment {deployment_id} not found")
            raise typer.Exit(1)

        manifest = deployment_manager.load_manifest(deployment_id)

        # Validate environment
        if environment not in manifest.get("environments", {}):
            console.print(f"[red]Error:[/red] Environment '{environment}' not found in manifest")
            raise typer.Exit(1)

        env_config = manifest["environments"][environment]
        if not env_config.get("enabled", False):
            console.print(f"[red]Error:[/red] Environment '{environment}' is not enabled")
            raise typer.Exit(1)

        console.print(f"[bold]Deploying {deployment_id} to {environment}[/bold]")
        console.print()

        # Validate manifest
        console.print("Validating deployment...")
        validator = ManifestValidator()
        manifest_path = deployment_dir / "deployment-manifest.yaml"

        if not validator.validate_file(manifest_path):
            console.print("[red]Manifest validation failed:[/red]")
            for error in validator.get_errors():
                console.print(f"  - {error}")
            raise typer.Exit(1)

        # Validate dependencies
        dep_validator = DependencyValidator()
        if not dep_validator.validate(manifest.get("stacks", {})):
            console.print("[red]Dependency validation failed:[/red]")
            for error in dep_validator.get_errors():
                console.print(f"  - {error}")
            raise typer.Exit(1)

        safe_print(console, "[green]✓[/green] Manifest and dependencies valid")

        # Validate stack code against templates
        if validate_code:
            console.print("\nValidating stack code against templates...")
            cli_root = Path(__file__).parent.parent.parent.parent.parent
            stacks_root = cli_root / "stacks"

            code_validator = StackCodeValidator()
            all_valid, validation_results = code_validator.validate_deployment(
                stacks_root, manifest, strict
            )

            # Count results
            total_stacks = len(validation_results)
            valid_stacks = sum(1 for r in validation_results.values() if r.valid)
            total_errors = sum(r.get_error_count() for r in validation_results.values())
            total_warnings = sum(r.get_warning_count() for r in validation_results.values())

            console.print(f"  Validated: {total_stacks} stack(s)")
            console.print(f"  Valid: {valid_stacks}/{total_stacks}")

            if total_errors > 0:
                console.print(f"  [red]Errors: {total_errors}[/red]")
            if total_warnings > 0:
                console.print(f"  [yellow]Warnings: {total_warnings}[/yellow]")

            # Show details for failed stacks
            if not all_valid:
                console.print("\n[red]Code validation failed:[/red]")
                for stack_name, result in validation_results.items():
                    if not result.valid:
                        console.print(f"\n  Stack: {stack_name}")
                        for error in result.errors[:3]:  # Show first 3 errors
                            safe_print(console, f"    ✗ {error.message}")
                        if result.get_error_count() > 3:
                            console.print(f"    ... and {result.get_error_count() - 3} more error(s)")

                console.print("\n[yellow]Tip:[/yellow] Run 'cloud validate-stack <stack-name>' for detailed validation")
                raise typer.Exit(1)

            safe_print(console, "[green]✓[/green] Code validation passed")

        console.print()

        # Create orchestration plan
        orchestrator = Orchestrator(max_parallel=parallel)
        plan = orchestrator.create_plan(manifest.get("stacks", {}))

        console.print(orchestrator.print_plan(plan))

        if preview:
            console.print("[yellow]Preview mode - no changes will be made[/yellow]")
            return

        # Confirm deployment
        if not typer.confirm("Proceed with deployment?"):
            console.print("Deployment cancelled")
            raise typer.Exit(0)

        # Initialize state manager
        state_manager = StateManager(deployment_dir)
        state_manager.start_operation("deploy", {"environment": environment})

        # Execute deployment (sync wrapper for async execution)
        asyncio.run(_execute_deployment(
            deployment_id, manifest, environment, deployment_dir, orchestrator, plan, state_manager
        ))

        console.print()
        safe_print(console, "[green]✓[/green] Deployment completed successfully")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        logger.error(f"Deploy command failed: {e}", exc_info=True)
        raise typer.Exit(1)


async def _execute_deployment(
    deployment_id, manifest, environment, deployment_dir, orchestrator, plan, state_manager
):
    """Execute deployment asynchronously"""

    # Get stack dir (assuming stacks are in cloud/stacks/)
    cli_root = Path(__file__).parent.parent.parent.parent.parent
    stacks_root = cli_root / "stacks"

    # Initialize Pulumi
    # Use pulumiOrg (Pulumi Cloud organization), NOT organization (deployment org)
    pulumi_org = manifest.get("pulumiOrg", manifest.get("organization", ""))
    project = manifest.get("project", deployment_id)
    pulumi_wrapper = PulumiWrapper(organization=pulumi_org, project=project)
    stack_ops = StackOperations(pulumi_wrapper)

    # Config generator
    config_gen = ConfigGenerator(deployment_dir)

    # Stack executor function
    async def stack_executor(stack_name: str):
        try:
            console.print(f"  Deploying stack: [cyan]{stack_name}[/cyan]")

            # Get stack directory
            stack_dir = stacks_root / stack_name

            if not stack_dir.exists():
                return False, f"Stack directory not found: {stack_dir}"

            # Generate config
            config_file = config_gen.generate_stack_config(stack_name, manifest, environment)
            config = config_gen.load_stack_config(stack_name, environment)

            # Get Pulumi config values
            pulumi_config = config_gen.generate_pulumi_config_values(stack_name, environment)

            # Use deployment context for Pulumi.yaml management
            with pulumi_wrapper.deployment_context(stack_dir, stack_name):
                # Deploy stack within context
                success, error = stack_ops.deploy_stack(
                    deployment_id=deployment_id,
                    stack_name=stack_name,
                    environment=environment,
                    stack_dir=stack_dir,
                    config=pulumi_config,
                    preview_only=False,
                )
            # Pulumi.yaml automatically restored here

            if success:
                state_manager.set_stack_status(stack_name, StackStatus.DEPLOYED, environment)
            else:
                state_manager.set_stack_status(stack_name, StackStatus.FAILED, environment)

            return success, error

        except Exception as e:
            logger.error(f"Error deploying stack {stack_name}: {e}")
            return False, str(e)

    # Execute orchestrated deployment
    result = await orchestrator.execute_plan(plan, stack_executor, stop_on_error=True)

    # Record completion
    state_manager.complete_operation(result.success, {
        "successful_stacks": result.successful_stacks,
        "failed_stacks": result.failed_stacks,
    })

    if not result.success:
        raise Exception(f"Deployment failed: {result.error_message}")
