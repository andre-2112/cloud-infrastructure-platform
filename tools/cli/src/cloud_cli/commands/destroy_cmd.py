from cloud_cli.utils.console_utils import safe_print
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

from cloud_core.deployment import DeploymentManager, StateManager, StackStatus
from cloud_core.orchestrator import Orchestrator
from cloud_core.pulumi import PulumiWrapper, StackOperations
from cloud_core.validation import ManifestValidator
from cloud_core.utils.logger import get_logger
from cloud_core.utils.output_formatter import OutputFormatter, OutputLevel
from cloud_core.utils import AWSErrorHandler

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
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Minimal output (only critical messages)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Detailed output"),
) -> None:
    """Destroy all stacks in a deployment (reverse order)"""

    try:
        # Determine output level
        if quiet:
            output_level = OutputLevel.QUIET
        elif verbose:
            output_level = OutputLevel.VERBOSE
        else:
            output_level = OutputLevel.NORMAL

        output = OutputFormatter(level=output_level, console=console)

        # Load deployment
        deployment_manager = DeploymentManager()
        deployment_dir = deployment_manager.get_deployment_dir(deployment_id)

        if not deployment_dir.exists():
            output.error(f"Deployment {deployment_id} not found")
            raise typer.Exit(1)

        # Load manifest
        manifest_path = deployment_dir / "deployment-manifest.yaml"
        validator = ManifestValidator()

        if not validator.validate(str(manifest_path)):
            output.error("Invalid deployment manifest")
            for error in validator.errors:
                output.error(f"  - {error}")
            raise typer.Exit(1)

        manifest = validator.manifest

        # Create orchestrator
        orchestrator = Orchestrator()

        # Build reverse orchestration plan (destroy in reverse order)
        output.section("Building destroy plan...")

        # Get stacks configuration
        stacks_config = manifest.get("stacks", {})

        # Get destroy order (reversed layers)
        destroy_layers = orchestrator.get_destroy_order(stacks_config)

        # Create a simple plan object for display
        class DestroyPlan:
            def __init__(self, layers):
                self.layers = layers
                self.total_stacks = sum(len(layer) for layer in layers)

        plan = DestroyPlan(destroy_layers)

        if not plan.layers:
            output.warning("No stacks to destroy")
            return

        # Display plan
        output.section(f"Destroy plan for {deployment_id} ({environment}):")
        output.info(f"Total stacks: {plan.total_stacks}")
        output.info(f"Layers: {len(plan.layers)}")
        output.info("")

        for i, layer in enumerate(plan.layers, 1):
            output.info(f"Layer {i}: {', '.join(layer)}")

        if dry_run:
            output.warning("\nDry run - no resources will be destroyed")
            return

        # Confirm destruction
        if not yes:
            output.info("")
            confirm = typer.confirm(
                f"Are you sure you want to destroy all stacks in {deployment_id} ({environment})?"
            )
            if not confirm:
                output.info("Destruction cancelled")
                return

        # Execute destroy
        output.section("Destroying stacks...")

        state_manager = StateManager(deployment_dir)
        state_manager.start_operation("destroy", {"environment": environment})

        # Initialize PulumiWrapper with required parameters
        # Use pulumiOrg (Pulumi Cloud organization), NOT organization (deployment org)
        pulumi_org = manifest.get("pulumiOrg", manifest.get("organization", ""))

        # Build composite project name: DeploymentID-Organization-Project
        deployment_id_str = manifest.get("deployment_id", deployment_id)
        organization = manifest.get("organization", "")
        project = manifest.get("project", "")
        composite_project = f"{deployment_id_str}-{organization}-{project}"

        pulumi_wrapper = PulumiWrapper(organization=pulumi_org, project=composite_project)
        stack_ops = StackOperations(pulumi_wrapper)

        # Get stack dir (assuming stacks are in cloud/stacks/)
        cloud_root = Path(__file__).parent.parent.parent.parent.parent.parent  # Go to cloud root
        stacks_root = cloud_root / "stacks"

        async def run_destroy():
            try:
                # Stack destroyer function
                async def stack_destroyer(stack_name: str):
                    try:
                        console.print(f"  Destroying stack: [cyan]{stack_name}[/cyan]")

                        # Get stack directory
                        stack_dir = stacks_root / stack_name

                        if not stack_dir.exists():
                            return False, f"Stack directory not found: {stack_dir}"

                        # Use deployment context for Pulumi.yaml management
                        with pulumi_wrapper.deployment_context(stack_dir, manifest, deployment_dir):
                            # Destroy stack within context
                            success, error = stack_ops.destroy_stack(
                                deployment_id=deployment_id,
                                stack_name=stack_name,
                                environment=environment,
                                stack_dir=stack_dir,
                            )
                        # Pulumi.yaml automatically restored here

                        if success:
                            state_manager.set_stack_status(stack_name, StackStatus.NOT_DEPLOYED, environment)
                        else:
                            state_manager.set_stack_status(stack_name, StackStatus.FAILED, environment)

                        return success, error

                    except Exception as e:
                        error_message = str(e)
                        logger.error(f"Error destroying stack {stack_name}: {e}")

                        # Log stack-specific error to deployment directory
                        AWSErrorHandler.log_error_to_deployment(
                            error_message,
                            deployment_dir,
                            deployment_id,
                            stack_name=stack_name,
                            environment=environment,
                            operation="destroy"
                        )

                        return False, error_message

                # Create an OrchestrationPlan-like object that execute_plan expects
                from cloud_core.orchestrator import OrchestrationPlan, DependencyResolver, LayerCalculator

                # Build minimal dependency resolver and layer calculator
                dep_resolver = DependencyResolver()
                dep_resolver.build_graph(stacks_config)
                layer_calc = LayerCalculator(dep_resolver)

                # Create plan object
                exec_plan = OrchestrationPlan(destroy_layers, dep_resolver, layer_calc)

                # Execute destroy plan
                result = await orchestrator.execute_plan(
                    plan=exec_plan,
                    stack_executor=stack_destroyer,
                    stop_on_error=True
                )

                return result.success

            except Exception as e:
                logger.error(f"Destroy failed: {e}")
                return False

        success = asyncio.run(run_destroy())

        if success:
            # Mark deployment as destroyed
            from cloud_core.deployment import DeploymentStatus
            state_manager.set_deployment_status(DeploymentStatus.DESTROYED)
            state_manager.complete_operation(success=True)

            output.success(f"Deployment {deployment_id} ({environment}) destroyed successfully")
            output.info("")
            output.info("Deployment resources have been destroyed.")
            output.info(f"Deployment history and logs are preserved in: {deployment_dir}")
            output.info("")
            output.warning("Note: Do not use Pulumi commands directly. Use 'cloud' CLI commands to manage deployments.")
        else:
            state_manager.complete_operation(success=False)
            output.error("Destroy failed - see logs for details")
            raise typer.Exit(1)

    except Exception as e:
        error_message = str(e)

        # Check if it's an AWS limit error and format appropriately
        aws_error = AWSErrorHandler.detect_aws_limit_error(error_message)
        if aws_error:
            console.print(aws_error.format_error())
        else:
            console.print(f"[red][ERROR][/red] {error_message}")

        # Log error to deployment directory if we have deployment_dir
        if 'deployment_dir' in locals() and deployment_dir:
            AWSErrorHandler.log_error_to_deployment(
                error_message,
                deployment_dir,
                deployment_id,
                environment=environment,
                operation="destroy"
            )
            console.print(f"\n[dim]Error details logged to: {deployment_dir}/logs/[/dim]")

        logger.error(f"Destroy command failed: {e}", exc_info=True)
        raise typer.Exit(1)
