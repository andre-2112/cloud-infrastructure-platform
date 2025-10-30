from cloud_cli.utils.console_utils import safe_print
"""
Stack Management Commands

Commands for managing stack registration and lifecycle.
"""

import typer
from typing import Optional
from rich.console import Console
from rich.table import Table
from pathlib import Path
import yaml

from cloud_core.templates import TemplateManager
from cloud_core.templates.stack_template_manager import StackTemplateManager
from cloud_core.validation import ManifestValidator
from cloud_core.validation.stack_code_validator import StackCodeValidator
from cloud_core.utils.logger import get_logger
from cloud_cli.parser import ParameterExtractor

app = typer.Typer()
console = Console()
logger = get_logger(__name__)


@app.command(name="register-stack")
def register_stack_command(
    stack_name: str = typer.Argument(..., help="Stack name"),
    description: str = typer.Option(..., "--description", "-d", help="Stack description"),
    dependencies: Optional[str] = typer.Option(
        None, "--dependencies", help="Comma-separated list of dependencies"
    ),
    priority: int = typer.Option(100, "--priority", "-p", help="Stack priority (lower = earlier)"),
    auto_extract: bool = typer.Option(
        True, "--auto-extract/--no-auto-extract", help="Auto-extract parameters from code"
    ),
    validate: bool = typer.Option(
        False, "--validate", help="Validate code after registration"
    ),
    strict: bool = typer.Option(
        False, "--strict", help="Enable strict validation"
    ),
    defaults_file: Optional[str] = typer.Option(
        None, "--defaults-file", help="YAML file with default configuration"
    ),
) -> None:
    """Register a new stack with the platform (Enhanced)"""

    try:
        # Validate stack directory exists
        stack_dir = Path.cwd() / "stacks" / stack_name
        if not stack_dir.exists():
            console.print(f"[red]Error:[/red] Stack directory not found: {stack_dir}")
            raise typer.Exit(1)

        # Check required files
        index_ts = stack_dir / "index.ts"
        pulumi_yaml = stack_dir / "Pulumi.yaml"

        if not index_ts.exists():
            console.print(f"[red]Error:[/red] index.ts not found in {stack_dir}")
            raise typer.Exit(1)

        if not pulumi_yaml.exists():
            console.print(f"[red]Error:[/red] Pulumi.yaml not found in {stack_dir}")
            raise typer.Exit(1)

        # Parse dependencies
        deps = []
        if dependencies:
            deps = [d.strip() for d in dependencies.split(',')]

        # Auto-extract parameters from code
        parameters = {}
        if auto_extract:
            console.print(f"[cyan]Extracting parameters from {stack_name}...[/cyan]")
            extractor = ParameterExtractor()
            extraction = extractor.extract_from_stack(stack_dir, stack_name)

            if extraction["success"]:
                parameters = extraction["parameters"]

                # Show extracted parameters
                input_count = len(parameters.get("inputs", {}))
                output_count = len(parameters.get("outputs", {}))
                console.print(f"  Found {input_count} input(s) and {output_count} output(s)")

                if extraction.get("warnings"):
                    console.print("[yellow]Warnings:[/yellow]")
                    for warning in extraction["warnings"]:
                        console.print(f"  ! {warning}")
            else:
                console.print(f"[yellow]Warning:[/yellow] Failed to auto-extract parameters: {extraction.get('error')}")
                console.print("  Continuing with manual configuration...")

        # Load additional defaults from file if provided
        if defaults_file:
            defaults_path = Path(defaults_file)
            if defaults_path.exists():
                with open(defaults_path, 'r') as f:
                    file_defaults = yaml.safe_load(f) or {}

                # Merge with extracted parameters
                if "parameters" in file_defaults:
                    # Merge inputs
                    if "inputs" in file_defaults["parameters"]:
                        parameters.setdefault("inputs", {}).update(
                            file_defaults["parameters"]["inputs"]
                        )
                    # Merge outputs
                    if "outputs" in file_defaults["parameters"]:
                        parameters.setdefault("outputs", {}).update(
                            file_defaults["parameters"]["outputs"]
                        )
            else:
                console.print(f"[yellow]Warning:[/yellow] Defaults file not found: {defaults_file}")

        # Create stack template with enhanced format
        template_data = {
            "name": stack_name,
            "description": description,
            "dependencies": deps,
            "priority": priority,
        }

        # Add parameters section if we have any
        if parameters:
            template_data["parameters"] = parameters

        # Save template using StackTemplateManager
        template_manager = StackTemplateManager()
        template_file = template_manager.save_template(
            stack_name,
            template_data,
            overwrite=True
        )

        safe_print(console, f"[green]✓[/green] Stack '{stack_name}' registered successfully")
        console.print(f"  Template: {template_file}")
        console.print(f"  Dependencies: {', '.join(deps) if deps else 'none'}")
        console.print(f"  Priority: {priority}")

        if parameters:
            console.print(f"  Parameters: {len(parameters.get('inputs', {}))} inputs, {len(parameters.get('outputs', {}))} outputs")

        # Validate if requested
        if validate:
            console.print(f"\n[cyan]Validating stack code...[/cyan]")
            validator = StackCodeValidator()
            result = validator.validate(stack_dir, template_data, stack_name, strict)

            if result.valid:
                safe_print(console, f"[green]✓ Validation passed[/green]")
            else:
                safe_print(console, f"[red]✗ Validation failed[/red]")

            if result.warnings:
                console.print(f"[yellow]Warnings: {len(result.warnings)}[/yellow]")
                for issue in result.warnings[:5]:  # Show first 5
                    console.print(f"  ! {issue.message}")

            if result.errors:
                console.print(f"[red]Errors: {len(result.errors)}[/red]")
                for issue in result.errors[:5]:  # Show first 5
                    safe_print(console, f"  ✗ {issue.message}")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        logger.error(f"Register-stack command failed: {e}", exc_info=True)
        raise typer.Exit(1)


@app.command(name="list-stacks")
def list_stacks_command() -> None:
    """List all registered stacks"""

    try:
        template_dir = Path.cwd() / "tools" / "templates" / "config"

        if not template_dir.exists():
            console.print("[yellow]No stacks registered[/yellow]")
            return

        # Find all stack template files
        template_files = list(template_dir.glob("*.yaml"))

        if not template_files:
            console.print("[yellow]No stacks registered[/yellow]")
            return

        # Create table
        table = Table(title="Registered Stacks")
        table.add_column("Stack Name", style="cyan")
        table.add_column("Description")
        table.add_column("Dependencies")
        table.add_column("Priority", justify="right")

        for template_file in sorted(template_files):
            with open(template_file, 'r') as f:
                data = yaml.safe_load(f)

            deps = data.get("dependencies", [])
            table.add_row(
                data.get("name", template_file.stem),
                data.get("description", "N/A"),
                ", ".join(deps) if deps else "none",
                str(data.get("priority", 100)),
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        logger.error(f"List-stacks command failed: {e}", exc_info=True)
        raise typer.Exit(1)


@app.command(name="update-stack")
def update_stack_command(
    stack_name: str = typer.Argument(..., help="Stack name"),
    description: Optional[str] = typer.Option(None, "--description", "-d"),
    dependencies: Optional[str] = typer.Option(None, "--dependencies"),
    priority: Optional[int] = typer.Option(None, "--priority", "-p"),
) -> None:
    """Update a registered stack's configuration"""

    try:
        template_file = Path.cwd() / "tools" / "templates" / "config" / f"{stack_name}.yaml"

        if not template_file.exists():
            console.print(f"[red]Error:[/red] Stack '{stack_name}' not registered")
            console.print("Run 'cloud list-stacks' to see registered stacks")
            raise typer.Exit(1)

        # Load existing template
        with open(template_file, 'r') as f:
            data = yaml.safe_load(f)

        # Update fields
        if description:
            data["description"] = description
        if dependencies is not None:
            data["dependencies"] = [d.strip() for d in dependencies.split(',') if d.strip()]
        if priority is not None:
            data["priority"] = priority

        # Save template
        with open(template_file, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

        safe_print(console, f"[green]✓[/green] Stack '{stack_name}' updated successfully")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        logger.error(f"Update-stack command failed: {e}", exc_info=True)
        raise typer.Exit(1)


@app.command(name="unregister-stack")
def unregister_stack_command(
    stack_name: str = typer.Argument(..., help="Stack name"),
    force: bool = typer.Option(False, "--force", "-f", help="Force unregister"),
) -> None:
    """Unregister a stack from the platform"""

    try:
        template_file = Path.cwd() / "tools" / "templates" / "config" / f"{stack_name}.yaml"

        if not template_file.exists():
            console.print(f"[red]Error:[/red] Stack '{stack_name}' not registered")
            raise typer.Exit(1)

        if not force:
            confirm = typer.confirm(f"Are you sure you want to unregister stack '{stack_name}'?")
            if not confirm:
                console.print("Unregister cancelled")
                return

        # Remove template file
        template_file.unlink()

        safe_print(console, f"[green]✓[/green] Stack '{stack_name}' unregistered successfully")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        logger.error(f"Unregister-stack command failed: {e}", exc_info=True)
        raise typer.Exit(1)


@app.command(name="validate-stack")
def validate_stack_command(
    stack_name: str = typer.Argument(..., help="Stack name"),
    strict: bool = typer.Option(
        False, "--strict", help="Enable strict validation"
    ),
    check_files: bool = typer.Option(
        True, "--check-files/--no-check-files", help="Check required files"
    ),
) -> None:
    """Validate a stack's code against template declarations (Enhanced)"""

    try:
        # Check stack directory
        stack_dir = Path.cwd() / "stacks" / stack_name

        if not stack_dir.exists():
            console.print(f"[red]Error:[/red] Stack directory not found: {stack_dir}")
            raise typer.Exit(1)

        basic_errors: list[str] = []
        basic_warnings: list[str] = []

        # Check required files if requested
        if check_files:
            required_files = ["index.ts", "Pulumi.yaml", "package.json"]
            for file in required_files:
                if not (stack_dir / file).exists():
                    basic_errors.append(f"Missing required file: {file}")

        # Check if registered
        template_manager = StackTemplateManager()
        if not template_manager.template_exists(stack_name):
            console.print(f"[yellow]Warning:[/yellow] Stack not registered")
            console.print(f"  Run: cloud register-stack {stack_name} --description \"...\"")
            console.print("\nSkipping template validation (no template found)")

            if basic_errors:
                safe_print(console, f"\n[red]✗ Basic validation failed:[/red]")
                for error in basic_errors:
                    safe_print(console, f"  ✗ {error}")
                raise typer.Exit(1)

            safe_print(console, f"[green]✓ Basic file structure is valid[/green]")
            return

        # Load template
        template_data = template_manager.load_template(stack_name)

        # Report basic issues first
        if basic_errors:
            safe_print(console, f"[red]✗ Basic validation failed:[/red]")
            for error in basic_errors:
                safe_print(console, f"  ✗ {error}")
            console.print("\nFix basic issues before template validation")
            raise typer.Exit(1)

        # Perform template-based validation
        console.print(f"[cyan]Validating {stack_name} against template...[/cyan]")
        validator = StackCodeValidator()
        result = validator.validate(stack_dir, template_data, stack_name, strict)

        # Display results
        console.print("\n" + "=" * 60)
        if result.valid and not result.has_issues():
            safe_print(console, f"[green]✓ Stack '{stack_name}' is valid[/green]")
            console.print("  Code matches template declarations")
        elif result.valid and result.warnings:
            safe_print(console, f"[green]✓ Stack '{stack_name}' is valid (with warnings)[/green]")
        else:
            safe_print(console, f"[red]✗ Stack '{stack_name}' validation failed[/red]")

        # Show errors
        if result.errors:
            console.print(f"\n[red]Errors ({len(result.errors)}):[/red]")
            for issue in result.errors:
                location = f" [{issue.location}]" if issue.location else ""
                safe_print(console, f"  ✗ {issue.message}{location}")

        # Show warnings
        if result.warnings:
            console.print(f"\n[yellow]Warnings ({len(result.warnings)}):[/yellow]")
            for issue in result.warnings:
                location = f" [{issue.location}]" if issue.location else ""
                console.print(f"  ! {issue.message}{location}")

        console.print("=" * 60)

        # Exit with error if validation failed
        if not result.valid:
            raise typer.Exit(1)

    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        logger.error(f"Validate-stack command failed: {e}", exc_info=True)
        raise typer.Exit(1)
