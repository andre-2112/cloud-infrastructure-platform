from cloud_cli.utils.console_utils import safe_print
"""
Template Management Commands

Commands for managing deployment templates.
"""

import typer
from typing import Optional
from rich.console import Console
from rich.syntax import Syntax
from pathlib import Path
import yaml
import shutil

from cloud_core.templates import TemplateManager
from cloud_core.utils.logger import get_logger

app = typer.Typer()
console = Console()
logger = get_logger(__name__)
# Calculate cloud root from this file's location
CLOUD_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent


@app.command(name="list-templates")
def list_templates_command() -> None:
    """List all available deployment templates"""

    try:
        template_manager = TemplateManager()
        templates = template_manager.list_templates()

        if not templates:
            console.print("[yellow]No templates found[/yellow]")
            return

        console.print("[bold]Available Templates:[/bold]\n")
        for template in templates:
            console.print(f"  • {template}")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        logger.error(f"List-templates command failed: {e}", exc_info=True)
        raise typer.Exit(1)


@app.command(name="show-template")
def show_template_command(
    template_name: str = typer.Argument(..., help="Template name"),
) -> None:
    """Show template contents"""

    try:
        template_manager = TemplateManager()

        if not template_manager.template_exists(template_name):
            console.print(f"[red]Error:[/red] Template '{template_name}' not found")
            available = template_manager.list_templates()
            if available:
                console.print("\n[yellow]Available templates:[/yellow]")
                for t in available:
                    console.print(f"  • {t}")
            raise typer.Exit(1)

        # Load template
        template_content = template_manager.load_template(template_name)

        # Display as YAML with syntax highlighting
        syntax = Syntax(
            yaml.dump(template_content, default_flow_style=False, sort_keys=False),
            "yaml",
            theme="monokai",
            line_numbers=True,
        )
        console.print(f"\n[bold]Template: {template_name}[/bold]\n")
        console.print(syntax)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        logger.error(f"Show-template command failed: {e}", exc_info=True)
        raise typer.Exit(1)


@app.command(name="create-template")
def create_template_command(
    template_name: str = typer.Argument(..., help="Template name"),
    source_deployment: Optional[str] = typer.Option(
        None, "--from-deployment", help="Create from existing deployment"
    ),
    source_template: Optional[str] = typer.Option(
        None, "--from-template", help="Create from existing template"
    ),
) -> None:
    """Create a new deployment template"""

    try:
        template_dir = CLOUD_ROOT / "tools" / "templates" / "default"
        template_file = template_dir / f"{template_name}.yaml"

        if template_file.exists():
            console.print(f"[red]Error:[/red] Template '{template_name}' already exists")
            raise typer.Exit(1)

        template_data = {}

        if source_deployment:
            # Load from deployment manifest
            from cloud_core.deployment import DeploymentManager
            deploy_manager = DeploymentManager()
            deploy_dir = deploy_manager.get_deployment_dir(source_deployment)
            manifest_path = deploy_dir / "deployment-manifest.yaml"

            if not manifest_path.exists():
                console.print(f"[red]Error:[/red] Deployment manifest not found")
                raise typer.Exit(1)

            with open(manifest_path, 'r') as f:
                template_data = yaml.safe_load(f)

        elif source_template:
            # Copy existing template
            source_file = template_dir / f"{source_template}.yaml"
            if not source_file.exists():
                console.print(f"[red]Error:[/red] Source template '{source_template}' not found")
                raise typer.Exit(1)

            with open(source_file, 'r') as f:
                template_data = yaml.safe_load(f)

        else:
            # Create minimal template
            template_data = {
                "deployment": {
                    "org": "YOUR_ORG",
                    "project": "YOUR_PROJECT",
                    "domain": "example.com",
                    "region": "us-east-1",
                },
                "environments": ["dev", "stage", "prod"],
                "stacks": {},
            }

        # Save template
        with open(template_file, 'w') as f:
            yaml.dump(template_data, f, default_flow_style=False, sort_keys=False)

        safe_print(console, f"[green]✓[/green] Template '{template_name}' created successfully")
        console.print(f"  Location: {template_file}")
        console.print(f"\nEdit the template file to customize stacks and configuration")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        logger.error(f"Create-template command failed: {e}", exc_info=True)
        raise typer.Exit(1)


@app.command(name="update-template")
def update_template_command(
    template_name: str = typer.Argument(..., help="Template name"),
    file: str = typer.Option(..., "--file", "-f", help="YAML file with updates"),
) -> None:
    """Update an existing template"""

    try:
        template_dir = CLOUD_ROOT / "tools" / "templates" / "default"
        template_file = template_dir / f"{template_name}.yaml"

        if not template_file.exists():
            console.print(f"[red]Error:[/red] Template '{template_name}' not found")
            raise typer.Exit(1)

        # Load updates
        update_file = Path(file)
        if not update_file.exists():
            console.print(f"[red]Error:[/red] Update file not found: {file}")
            raise typer.Exit(1)

        with open(update_file, 'r') as f:
            updates = yaml.safe_load(f)

        # Load existing template
        with open(template_file, 'r') as f:
            template_data = yaml.safe_load(f)

        # Merge updates (simple deep merge)
        def merge_dict(base, updates):
            for key, value in updates.items():
                if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                    merge_dict(base[key], value)
                else:
                    base[key] = value

        merge_dict(template_data, updates)

        # Save template
        with open(template_file, 'w') as f:
            yaml.dump(template_data, f, default_flow_style=False, sort_keys=False)

        safe_print(console, f"[green]✓[/green] Template '{template_name}' updated successfully")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        logger.error(f"Update-template command failed: {e}", exc_info=True)
        raise typer.Exit(1)


@app.command(name="validate-template")
def validate_template_command(
    template_name: str = typer.Argument(..., help="Template name"),
) -> None:
    """Validate a deployment template"""

    try:
        template_manager = TemplateManager()

        if not template_manager.template_exists(template_name):
            console.print(f"[red]Error:[/red] Template '{template_name}' not found")
            raise typer.Exit(1)

        # Load and validate
        template_content = template_manager.load_template(template_name)

        errors = []
        warnings = []

        # Check required fields
        if "deployment" not in template_content:
            errors.append("Missing 'deployment' section")
        else:
            deployment = template_content["deployment"]
            for field in ["org", "project", "domain", "region"]:
                if field not in deployment:
                    errors.append(f"Missing deployment.{field}")

        if "stacks" not in template_content:
            warnings.append("No stacks defined")

        # Validate stack references
        if "stacks" in template_content:
            stack_names = set(template_content["stacks"].keys())
            for stack_name, stack_config in template_content["stacks"].items():
                deps = stack_config.get("dependencies", [])
                for dep in deps:
                    if dep not in stack_names:
                        errors.append(f"Stack '{stack_name}' depends on undefined stack '{dep}'")

        # Report results
        if errors:
            console.print(f"[red]Validation failed for template '{template_name}':[/red]")
            for error in errors:
                safe_print(console, f"  ✗ {error}")
            raise typer.Exit(1)

        safe_print(console, f"[green]✓ Template '{template_name}' is valid[/green]")

        if warnings:
            console.print("\n[yellow]Warnings:[/yellow]")
            for warning in warnings:
                console.print(f"  ! {warning}")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        logger.error(f"Validate-template command failed: {e}", exc_info=True)
        raise typer.Exit(1)
