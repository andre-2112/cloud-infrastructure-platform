from cloud_cli.utils.console_utils import safe_print
"""
Validation Commands

Commands for validating deployments, dependencies, AWS, and Pulumi.
"""

import typer
from rich.console import Console
from pathlib import Path

from cloud_core.deployment import DeploymentManager
from cloud_core.validation import (
    ManifestValidator,
    DependencyValidator,
    AWSValidator,
    PulumiValidator,
)
from cloud_core.utils.logger import get_logger

app = typer.Typer(invoke_without_command=True, no_args_is_help=True)
console = Console()
logger = get_logger(__name__)


@app.callback()
def validate_callback(
    ctx: typer.Context,
) -> None:
    """Validation commands for deployments, dependencies, AWS, and Pulumi"""
    pass


@app.command()
def validate(
    deployment_id: str = typer.Argument(..., help="Deployment ID"),
) -> None:
    """Run full deployment validation"""

    try:
        # Load deployment
        deployment_manager = DeploymentManager()
        deployment_dir = deployment_manager.get_deployment_dir(deployment_id)

        if not deployment_dir.exists():
            console.print(f"[red]Error:[/red] Deployment {deployment_id} not found")
            raise typer.Exit(1)

        console.print(f"[bold]Validating deployment {deployment_id}...[/bold]\n")

        all_valid = True

        # 1. Validate manifest
        console.print("1. Validating manifest...")
        manifest_path = deployment_dir / "deployment-manifest.yaml"
        manifest_validator = ManifestValidator()

        if manifest_validator.validate(str(manifest_path)):
            safe_print(console, "   [green]✓ Manifest is valid[/green]")
            manifest = manifest_validator.manifest
        else:
            safe_print(console, "   [red]✗ Manifest validation failed:[/red]")
            for error in manifest_validator.errors:
                console.print(f"      - {error}")
            all_valid = False
            manifest = None

        # 2. Validate dependencies
        if manifest:
            console.print("\n2. Validating dependencies...")
            dep_validator = DependencyValidator()

            if dep_validator.validate(manifest):
                safe_print(console, "   [green]✓ No dependency cycles found[/green]")
            else:
                safe_print(console, "   [red]✗ Dependency validation failed:[/red]")
                for error in dep_validator.errors:
                    console.print(f"      - {error}")
                all_valid = False

        # 3. Validate AWS credentials
        console.print("\n3. Validating AWS credentials...")
        aws_validator = AWSValidator()

        if aws_validator.validate():
            safe_print(console, "   [green]✓ AWS credentials are valid[/green]")
        else:
            safe_print(console, "   [red]✗ AWS validation failed:[/red]")
            for error in aws_validator.errors:
                console.print(f"      - {error}")
            all_valid = False

        # 4. Validate Pulumi access
        console.print("\n4. Validating Pulumi access...")
        pulumi_validator = PulumiValidator()

        if pulumi_validator.validate():
            safe_print(console, "   [green]✓ Pulumi access is configured[/green]")
        else:
            safe_print(console, "   [red]✗ Pulumi validation failed:[/red]")
            for error in pulumi_validator.errors:
                console.print(f"      - {error}")
            all_valid = False

        # Summary
        console.print()
        if all_valid:
            safe_print(console, "[green]✓ All validations passed[/green]")
        else:
            safe_print(console, "[red]✗ Some validations failed[/red]")
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        logger.error(f"Validate command failed: {e}", exc_info=True)
        raise typer.Exit(1)


@app.command(name="validate-dependencies")
def validate_dependencies_command(
    deployment_id: str = typer.Argument(..., help="Deployment ID"),
) -> None:
    """Validate deployment dependencies for cycles"""

    try:
        deployment_manager = DeploymentManager()
        deployment_dir = deployment_manager.get_deployment_dir(deployment_id)

        if not deployment_dir.exists():
            console.print(f"[red]Error:[/red] Deployment {deployment_id} not found")
            raise typer.Exit(1)

        # Load manifest
        manifest_path = deployment_dir / "deployment-manifest.yaml"
        manifest_validator = ManifestValidator()

        if not manifest_validator.validate(str(manifest_path)):
            console.print("[red]Error:[/red] Invalid manifest")
            for error in manifest_validator.errors:
                console.print(f"  - {error}")
            raise typer.Exit(1)

        # Validate dependencies
        dep_validator = DependencyValidator()

        if dep_validator.validate(manifest_validator.manifest):
            safe_print(console, "[green]✓ No dependency cycles found[/green]")
        else:
            safe_print(console, "[red]✗ Dependency validation failed:[/red]")
            for error in dep_validator.errors:
                console.print(f"  - {error}")
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        logger.error(f"Validate-dependencies command failed: {e}", exc_info=True)
        raise typer.Exit(1)


@app.command(name="validate-aws")
def validate_aws_command() -> None:
    """Validate AWS credentials and basic permissions"""

    try:
        console.print("[bold]Validating AWS credentials...[/bold]\n")

        aws_validator = AWSValidator()

        if aws_validator.validate():
            safe_print(console, "[green]✓ AWS credentials are valid[/green]")
            if hasattr(aws_validator, 'account_id'):
                console.print(f"  Account ID: {aws_validator.account_id}")
            if hasattr(aws_validator, 'region'):
                console.print(f"  Region: {aws_validator.region}")
        else:
            safe_print(console, "[red]✗ AWS validation failed:[/red]")
            for error in aws_validator.errors:
                console.print(f"  - {error}")
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        logger.error(f"Validate-aws command failed: {e}", exc_info=True)
        raise typer.Exit(1)


@app.command(name="validate-pulumi")
def validate_pulumi_command() -> None:
    """Validate Pulumi CLI and access token"""

    try:
        console.print("[bold]Validating Pulumi configuration...[/bold]\n")

        pulumi_validator = PulumiValidator()

        if pulumi_validator.validate():
            safe_print(console, "[green]✓ Pulumi is configured correctly[/green]")
            if hasattr(pulumi_validator, 'cli_version'):
                console.print(f"  CLI Version: {pulumi_validator.cli_version}")
        else:
            safe_print(console, "[red]✗ Pulumi validation failed:[/red]")
            for error in pulumi_validator.errors:
                console.print(f"  - {error}")
            console.print("\n[yellow]Setup instructions:[/yellow]")
            console.print("  1. Install Pulumi CLI: https://www.pulumi.com/docs/get-started/install/")
            console.print("  2. Set access token: pulumi login")
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        logger.error(f"Validate-pulumi command failed: {e}", exc_info=True)
        raise typer.Exit(1)
