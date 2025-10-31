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
from cloud_core.utils import sanitize_org_and_project
from cloud_core.utils.output_formatter import OutputFormatter, OutputLevel
from cloud_core.ui import InteractivePrompt
from cloud_cli.utils.console_utils import safe_print

app = typer.Typer()
console = Console()
logger = get_logger(__name__)


@app.command()
def init(
    deployment_id: Optional[str] = typer.Argument(
        None, help="Deployment ID (auto-generated if not provided)"
    ),
    org: str = typer.Option("Test Organization", "--org", "-o", help="Organization name"),
    project: str = typer.Option("Test Project", "--project", "-p", help="Project name"),
    domain: str = typer.Option("genesis3d.com", "--domain", "-d", help="Primary domain"),
    pulumi_org: str = typer.Option("andre-2112", "--pulumi-org", help="Pulumi organization"),
    template: str = typer.Option(
        "default", "--template", "-t", help="Template name"
    ),
    region: str = typer.Option(
        "us-east-1", "--region", "-r", help="Primary AWS region"
    ),
    account_dev: str = typer.Option("211050572089", "--account-dev", help="Dev AWS account ID"),
    account_stage: Optional[str] = typer.Option(
        None, "--account-stage", help="Stage AWS account ID"
    ),
    account_prod: Optional[str] = typer.Option(
        None, "--account-prod", help="Prod AWS account ID"
    ),
    interactive: bool = typer.Option(False, "--interactive", "-i", help="Interactive mode (prompt for all parameters)"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Minimal output (only critical messages)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Detailed output"),
) -> None:
    """Initialize a new deployment from a template"""

    try:
        # Determine output level
        if quiet:
            output_level = OutputLevel.QUIET
        elif verbose:
            output_level = OutputLevel.VERBOSE
        else:
            output_level = OutputLevel.NORMAL

        output = OutputFormatter(level=output_level, console=console)

        # Interactive mode: prompt for all parameters
        if interactive:
            prompt = InteractivePrompt(console=console)

            output.section("Interactive Deployment Configuration")

            # Generate or prompt for deployment ID
            if not deployment_id:
                use_auto_id = prompt.confirm("Auto-generate deployment ID?", default=True)
                if use_auto_id:
                    deployment_id = generate_deployment_id()
                    output.info(f"Generated deployment ID: {deployment_id}")
                else:
                    deployment_id = prompt.text("Deployment ID", required=True)
                    if not validate_deployment_id(deployment_id):
                        output.error("Invalid deployment ID format")
                        output.error("Format should be: D + 6 alphanumeric characters (e.g., D1BRV40)")
                        raise typer.Exit(1)

            # Prompt for all parameters
            org = prompt.text("Organization name", default=org)
            project = prompt.text("Project name", default=project)
            domain = prompt.text("Primary domain", default=domain)
            pulumi_org = prompt.text("Pulumi organization", default=pulumi_org)

            # List available templates
            template_manager = TemplateManager()
            available_templates = template_manager.list_templates()
            if available_templates and len(available_templates) > 1:
                template = prompt.choice(
                    "Select template",
                    choices=available_templates,
                    default=template if template in available_templates else available_templates[0]
                )
            else:
                template = prompt.text("Template name", default=template)

            region = prompt.text("Primary AWS region", default=region)
            account_dev = prompt.text("Dev AWS account ID", default=account_dev)

            use_multi_account = prompt.confirm("Use separate accounts for stage/prod?", default=False)
            if use_multi_account:
                account_stage = prompt.text("Stage AWS account ID", default=account_stage or account_dev)
                account_prod = prompt.text("Prod AWS account ID", default=account_prod or account_dev)

            output.info("")

        # Generate deployment ID if not provided
        if not deployment_id:
            deployment_id = generate_deployment_id()
            output.info(f"[cyan]Generated deployment ID:[/cyan] {deployment_id}")
        elif not validate_deployment_id(deployment_id):
            output.error(f"Invalid deployment ID format: {deployment_id}")
            output.error("Format should be: D + 6 alphanumeric characters (e.g., D1BRV40)")
            raise typer.Exit(1)

        # Check if template exists
        template_manager = TemplateManager()
        if not template_manager.template_exists(template):
            output.error(f"Template '{template}' not found")
            available = template_manager.list_templates()
            if available:
                output.warning("Available templates:")
                for t in available:
                    output.info(f"  - {t}")
            raise typer.Exit(1)

        # Sanitize organization and project names
        org_sanitized, project_sanitized = sanitize_org_and_project(org, project)

        # Notify user if names were sanitized
        if org_sanitized != org:
            output.warning(f"Organization name sanitized: '{org}' -> '{org_sanitized}'")
        if project_sanitized != project:
            output.warning(f"Project name sanitized: '{project}' -> '{project_sanitized}'")

        # Build accounts dictionary
        accounts = {
            "dev": account_dev,
            "stage": account_stage or account_dev,
            "prod": account_prod or account_dev,
        }

        output.section("Creating new deployment:")
        output.detail("Deployment ID", f"[cyan]{deployment_id}[/cyan]")
        output.detail("Organization", org_sanitized)
        output.detail("Pulumi Org", pulumi_org)
        output.detail("Project", project_sanitized)
        output.detail("Domain", domain)
        output.detail("Template", template)
        output.detail("Region", region)
        output.info("")

        # Create deployment
        deployment_manager = DeploymentManager()
        deployment_dir = deployment_manager.create_deployment(
            template_name=template,
            organization=org_sanitized,
            pulumi_org=pulumi_org,
            project=project_sanitized,
            domain=domain,
            region=region,
            accounts=accounts,
            deployment_id=deployment_id,
        )

        output.success(f"Deployment created successfully at:")
        output.quiet(f"  {deployment_dir}")
        output.info("")
        output.section("Next steps:")
        output.info(f"  1. Review manifest: {deployment_dir}/deployment-manifest.yaml")
        output.info(f"  2. Validate deployment: [cyan]cloud validate {deployment_id}[/cyan]")
        output.info(f"  3. Deploy to dev: [cyan]cloud deploy {deployment_id} --environment dev[/cyan]")

    except Exception as e:
        console.print(f"[red]✗[/red] {e}")
        logger.error(f"Init command failed: {e}", exc_info=True)
        raise typer.Exit(1)
