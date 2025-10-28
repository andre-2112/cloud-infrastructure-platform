"""
Init Command

Initialize a new deployment from a template.
"""

import typer
from typing import Optional
from rich.console import Console
from pathlib import Path

from cloud_core.deployment import DeploymentManager
from cloud_core.templates import TemplateManager
from cloud_core.utils.deployment_id import generate_deployment_id, validate_deployment_id
from cloud_core.utils.logger import get_logger

app = typer.Typer()
console = Console()
logger = get_logger(__name__)


@app.command(name="init")
def init_command(
    deployment_id: Optional[str] = typer.Argument(
        None, help="Deployment ID (auto-generated if not provided)"
    ),
    org: str = typer.Option(..., "--org", "-o", help="Organization name"),
    project: str = typer.Option(..., "--project", "-p", help="Project name"),
    domain: str = typer.Option(..., "--domain", "-d", help="Primary domain"),
    template: str = typer.Option(
        "default", "--template", "-t", help="Template name"
    ),
    region: str = typer.Option(
        "us-east-1", "--region", "-r", help="Primary AWS region"
    ),
    account_dev: str = typer.Option(..., "--account-dev", help="Dev AWS account ID"),
    account_stage: Optional[str] = typer.Option(
        None, "--account-stage", help="Stage AWS account ID"
    ),
    account_prod: Optional[str] = typer.Option(
        None, "--account-prod", help="Prod AWS account ID"
    ),
) -> None:
    """Initialize a new deployment from a template"""

    try:
        # Generate deployment ID if not provided
        if not deployment_id:
            deployment_id = generate_deployment_id()
            console.print(f"[cyan]Generated deployment ID:[/cyan] {deployment_id}")
        elif not validate_deployment_id(deployment_id):
            console.print(
                f"[red]Error:[/red] Invalid deployment ID format: {deployment_id}"
            )
            console.print("Format should be: D + 6 alphanumeric characters (e.g., D1BRV40)")
            raise typer.Exit(1)

        # Check if template exists
        template_manager = TemplateManager()
        if not template_manager.template_exists(template):
            console.print(f"[red]Error:[/red] Template '{template}' not found")
            available = template_manager.list_templates()
            if available:
                console.print("[yellow]Available templates:[/yellow]")
                for t in available:
                    console.print(f"  - {t}")
            raise typer.Exit(1)

        # Build accounts dictionary
        accounts = {
            "dev": account_dev,
            "stage": account_stage or account_dev,
            "prod": account_prod or account_dev,
        }

        console.print()
        console.print("[bold]Creating new deployment:[/bold]")
        console.print(f"  Deployment ID: [cyan]{deployment_id}[/cyan]")
        console.print(f"  Organization:  {org}")
        console.print(f"  Project:       {project}")
        console.print(f"  Domain:        {domain}")
        console.print(f"  Template:      {template}")
        console.print(f"  Region:        {region}")
        console.print()

        # Create deployment
        deployment_manager = DeploymentManager()
        deployment_dir = deployment_manager.create_deployment(
            template_name=template,
            organization=org,
            project=project,
            domain=domain,
            region=region,
            accounts=accounts,
            deployment_id=deployment_id,
        )

        console.print(
            f"[green]✓[/green] Deployment created successfully at:"
        )
        console.print(f"  {deployment_dir}")
        console.print()
        console.print("[bold]Next steps:[/bold]")
        console.print(f"  1. Review manifest: {deployment_dir}/deployment-manifest.yaml")
        console.print(f"  2. Validate deployment: [cyan]cloud validate {deployment_id}[/cyan]")
        console.print(f"  3. Deploy to dev: [cyan]cloud deploy {deployment_id} --environment dev[/cyan]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        logger.error(f"Init command failed: {e}", exc_info=True)
        raise typer.Exit(1)
