# Session 2.1 - Core Implementation (Python CLI Edition)

**Session Type:** Core Platform Implementation
**Target:** Complete Tasks 5.1-5.10 (Implementation Only)
**Status:** Ready to Execute
**Expected Duration:** Full session (~80-100K tokens)
**Architecture Version:** 3.1 (with Pulumi state management updates)
**CLI Technology:** Python 3.11+ (Changed from TypeScript)

**IMPORTANT CHANGES IN v3.1:**
- Pulumi Projects now represent business projects (not stacks)
- Stack naming: `<deployment-id>-<stack-name>-<environment>`
- All StackReference code must use new format
- Deployment directories: `<deployment-id>-<org>-<project>/`
- Manifest at deployment root (no src/ subdirectory)
- Template structure: `docs/`, `stack/`, `config/`, `default/`, `custom/`

**MAJOR CHANGES IN Session 2.1:**
- **CLI now uses Python** (not TypeScript/Node.js)
- Fixed stack directory structure (index.ts at stack root, not in src/)
- Fixed CLI directory structure to match authoritative diagram
- All paths verified against Directory_Structure_Diagram.3.1.md

---

## ⚠️ IMPORTANT: About Prompt-12

**Prompt-12 is a HISTORICAL REFERENCE document** showing the original task breakdown.

**All tasks have been extracted, updated, and incorporated into THIS document.**

**DO NOT use Prompt-12 as an execution guide:**
- ❌ References Architecture 3.0 (we're on 3.1)
- ❌ Uses outdated naming conventions (multi-stack, staging, etc.)
- ❌ Missing v3.1 Pulumi state management updates
- ❌ Less detailed than this document
- ❌ Incomplete path specifications

**✅ Use THIS document (Session-2.1.md) as the authoritative guide.**

Prompt-12 location (for reference only):
`/c/Users/Admin/Documents/Workspace/cloud/tools/docs/Prompt-12 - Implement Final Version.md`

---

## Context & Background

This is **Session 2 of 3** in a multi-session implementation strategy for Multi-Stack Architecture 3.1 (cloud-0.7 platform).

### Session Overview

- **Session 1 (COMPLETED):** Planning & All Documentation (16 documents)
- **Session 2 (THIS):** Core Implementation (directory, stacks, CLI, validation, templates)
- **Session 3 (FUTURE):** Advanced Features (REST API, WebSockets, Database planning)

### What Session 1 Delivered

**16 Complete Documents (v3.1):**
1. Multi_Stack_Architecture.3.1.md (main architecture)
2-4. CLI documents (full, testing, quick reference)
5-7. REST API documents (full, testing, quick reference)
8. Deployment Manifest Specification
9. Directory Structure Diagram
10-16. Seven addendum documents

**All documents located in:** `/c/Users/Admin/Documents/Workspace/cloud/tools/docs/`

### What Session 1 Did NOT Do (Intentionally)

**Session 1 was DOCUMENTATION ONLY:**
- ❌ Did NOT create directory structure
- ❌ Did NOT copy/migrate stacks
- ❌ Did NOT implement any code
- ❌ Did NOT create CLI tool

**These are all Session 2 tasks!**

### What This Session Must Accomplish

**Primary Goal:** Implement core platform functionality

**Deliverables:**
1. New directory structure created (matching Directory_Structure_Diagram.3.1.md)
2. All 16 stacks migrated and adjusted (index.ts at stack root)
3. Python CLI tool implemented (25+ commands)
4. Validation tools implemented (Python)
5. Generic templates created
6. Platform ready for deployment testing

---

## Pre-Session Verification (CRITICAL)

### Before Starting Session 2, Verify:

1. **✅ Session 1 Completed:**
   ```bash
   ls -la /c/Users/Admin/Documents/Workspace/cloud/tools/docs/*.3.1.md | wc -l
   # Should return: 16
   ```

2. **✅ Source Files Exist (Pulumi-2):**
   ```bash
   ls -la /c/Users/Admin/Documents/Workspace/Pulumi-2/aws/build/ | head -20
   # Should show 16 stack directories
   ```

3. **✅ Working Directory:**
   ```bash
   cd /c/Users/Admin/Documents/Workspace
   pwd
   # Should show: /c/Users/Admin/Documents/Workspace
   ```

4. **✅ Python 3.11+ Installed:**
   ```bash
   python3 --version
   # Should show: Python 3.11.x or higher
   ```

5. **✅ User Approval:**
   - All Session 1 documents reviewed
   - Architecture 3.1 approved
   - Python CLI approach approved
   - Ready to proceed with implementation

**If any verification fails, STOP and resolve before proceeding!**

---

## Working Directory Strategy

### Directory Context Throughout Session:

**Starting Point:**
```bash
cd /c/Users/Admin/Documents/Workspace
```

**Source Directory (OLD - Pulumi-2):**
```bash
SOURCE=/c/Users/Admin/Documents/Workspace/Pulumi-2
# Contains existing stacks to migrate
```

**Destination Directory (NEW - cloud):**
```bash
DEST=/c/Users/Admin/Documents/Workspace/cloud
# Will be created in this session
```

**All commands in this document use absolute paths for clarity.**

---

## Pre-Session Reading (CRITICAL)

### Must Read Before Starting:

1. **./cloud/tools/docs/Multi_Stack_Architecture.3.1.md**
   - **PRIMARY REFERENCE** for this session
   - Complete specification for implementation

2. **./cloud/tools/docs/Directory_Structure_Diagram.3.1.md**
   - **AUTHORITATIVE** directory structure
   - Reference for ALL path decisions
   - CLI structure defined here

3. **./cloud/tools/docs/CLI_Commands_Reference.3.1.md**
   - Complete CLI specification
   - All commands to implement

4. **./cloud/tools/docs/Addendum_Platform_Code.3.1.md**
   - Code examples and patterns
   - Implementation guidance

5. **./cloud/tools/docs/Addendum_Verification_Architecture.3.1.md**
   - Validation tool specifications
   - Testing requirements

### Optional (Context Only):

6. **./cloud/tools/docs/Session-1-Prompt.md**
   - Context from previous session

7. **./cloud/tools/docs/Execution_Feasibility_Analysis.md**
   - Multi-session strategy rationale

---

## Authoritative Directory Structure

**From Directory_Structure_Diagram.3.1.md (AUTHORITATIVE):**

### Stack Structure (CRITICAL):

```
./cloud/stacks/<stack-name>/
├── index.ts                    # Main entry point (AT STACK ROOT, NOT in src/)
├── docs/
│   ├── Stack_Prompt_Main.md
│   ├── Stack_Definitions.md
│   └── ... (all stack docs)
├── src/                        # Optional component breakdown
│   ├── vpc.ts                  # Component files (e.g., for network stack)
│   ├── subnets.ts
│   └── outputs.ts
├── Pulumi.yaml
└── package.json
```

**KEY POINT:** `index.ts` is at the stack root, NOT inside `src/`!

### CLI Structure (AUTHORITATIVE):

```
./cloud/tools/cli/
├── src/
│   ├── __init__.py             # Python package init
│   ├── main.py                 # CLI entry point
│   ├── commands/               # Command implementations
│   │   ├── __init__.py
│   │   ├── init_cmd.py
│   │   ├── deploy_cmd.py
│   │   ├── destroy_cmd.py
│   │   ├── validate_cmd.py
│   │   ├── status_cmd.py
│   │   └── ... (25+ commands)
│   ├── orchestrator/           # Orchestration engine
│   │   ├── __init__.py
│   │   ├── orchestrator.py
│   │   ├── dependency_resolver.py
│   │   └── runtime_resolver.py
│   ├── templates/              # Template management
│   │   ├── __init__.py
│   │   ├── template_manager.py
│   │   └── manifest_generator.py
│   ├── deployment/             # Deployment management
│   │   ├── __init__.py
│   │   ├── deployment_manager.py
│   │   └── state_manager.py
│   ├── runtime/                # Runtime resolution
│   │   ├── __init__.py
│   │   ├── placeholder_resolver.py
│   │   └── config_resolver.py
│   ├── pulumi/                 # Pulumi integration
│   │   ├── __init__.py
│   │   ├── pulumi_wrapper.py
│   │   └── stack_operations.py
│   ├── validation/             # Validation
│   │   ├── __init__.py
│   │   ├── manifest_validator.py
│   │   ├── dependency_validator.py
│   │   ├── aws_validator.py
│   │   └── pulumi_validator.py
│   └── utils/                  # Utilities
│       ├── __init__.py
│       ├── deployment_id.py
│       ├── logger.py
│       └── helpers.py
├── tests/
│   ├── __init__.py
│   ├── test_commands/
│   ├── test_orchestrator/
│   └── test_validation/
├── requirements.txt
├── setup.py
├── pyproject.toml
└── README.md
```

**KEY BENEFITS of Python CLI:**
1. **Better Pulumi Integration:** Python Pulumi SDK is mature and well-documented
2. **Simpler Dependency Management:** pip/poetry vs npm/node_modules
3. **Better for DevOps:** Python is standard in infrastructure automation
4. **Rich Ecosystem:** Click/Typer for CLI, Pydantic for validation, rich for output
5. **Type Safety:** Type hints + mypy for static analysis
6. **Easier Maintenance:** Python is easier to read and maintain for ops teams

### Template Structure (for Pulumi Stacks):

```
./cloud/tools/templates/stack/
├── index.ts.template            # AT ROOT of template
├── src/
│   ├── component-example.ts.template
│   └── outputs.ts.template
├── Pulumi.yaml.template
├── package.json.template
└── tsconfig.json.template
```

---

## Session 2 Tasks (Implementation Only)

### Task 5.1: Implement Architecture 3.1 Core

**Objective:**
Systematically implement all aspects of Multi_Stack_Architecture.3.1 entirely.

**Scope:**
- All changes from Task 2 (already incorporated in Arch 3.1)
- Reuse existing Pulumi stack code (see 5.4)
- Follow Architecture 3.1 specifications exactly
- **Use Python for CLI tool**

---

### Task 5.2: Ensure Implementation Conformance

**Must implement:**
- ✅ New Directory Structure and Directory Names (per Directory_Structure_Diagram.3.1.md)
- ✅ Minimal Pulumi Specification
- ✅ Multi-Environment Architecture
- ✅ Configuration Architecture (Tiers, Flow)
- ✅ Stack Registration Management
- ✅ Stack Creation (Flows and Features)
- ✅ Stack Dependencies and Resolution
- ✅ Stack configuration files (Pulumi configuration)
- ✅ Stack source code files (all Pulumi .ts code, index.ts at stack root)
- ✅ Stack templates system
- ✅ Deployment flows and features
- ✅ Deployment Manifest
- ✅ Deployment configuration files
- ✅ Full Deployment Lifecycle support
- ✅ Runtime Resolution Process
- ✅ Orchestration Engine (Python)
- ✅ State Management
- ✅ Error Handling
- ✅ CLI (all commands and params) - **Python implementation**
- ✅ Verification and Validation tools (Python)
- ✅ Monitoring and Logging tools

**Note:** REST API, Database, WebSockets are Session 3

---

### Task 5.3: Create New Directory Structure

**CRITICAL:** Follow Directory_Structure_Diagram.3.1.md exactly!

**Create this structure:**

```bash
/c/Users/Admin/Documents/Workspace/cloud/
├── deploy/                          # Deployment instances
├── stacks/                          # Stack implementations
│   ├── network/
│   │   ├── index.ts                 # ← AT STACK ROOT!
│   │   ├── docs/                    # Stack documentation
│   │   ├── src/                     # Optional component breakdown
│   │   │   ├── vpc.ts
│   │   │   ├── subnets.ts
│   │   │   ├── nat.ts
│   │   │   └── outputs.ts
│   │   ├── Pulumi.yaml
│   │   └── package.json
│   ├── security/
│   │   ├── index.ts
│   │   ├── docs/
│   │   ├── src/
│   │   ├── Pulumi.yaml
│   │   └── package.json
│   ├── dns/
│   ├── secrets/
│   ├── authentication/
│   ├── storage/
│   ├── database-rds/
│   ├── containers-images/
│   ├── containers-apps/
│   ├── services-ecr/
│   ├── services-ecs/
│   ├── services-eks/
│   ├── services-api/
│   ├── compute-ec2/
│   ├── compute-lambda/
│   └── monitoring/
└── tools/                           # Platform tools
    ├── api/                         # REST API (Session 3)
    ├── cli/                         # Python CLI tool
    │   ├── src/
    │   │   ├── __init__.py
    │   │   ├── main.py
    │   │   ├── commands/
    │   │   ├── orchestrator/
    │   │   ├── templates/
    │   │   ├── deployment/
    │   │   ├── runtime/
    │   │   ├── pulumi/
    │   │   ├── validation/
    │   │   └── utils/
    │   ├── tests/
    │   ├── requirements.txt
    │   ├── setup.py
    │   └── README.md
    ├── docs/                        # Platform documentation (already exists)
    └── templates/
        ├── docs/                    # Stack Markdown templates
        ├── stack/                   # Stack Pulumi templates
        │   ├── index.ts.template    # ← AT ROOT of template!
        │   ├── src/
        │   │   ├── component-example.ts.template
        │   │   └── outputs.ts.template
        │   ├── Pulumi.yaml.template
        │   ├── package.json.template
        │   └── tsconfig.json.template
        ├── config/                  # Stack YAML templates
        ├── default/                 # Manifest templates
        └── custom/                  # Custom templates
```

**Implementation:**
1. Create root: `/c/Users/Admin/Documents/Workspace/cloud/`
2. Create all subdirectories per structure above
3. Verify structure matches Directory_Structure_Diagram.3.1.md

---

### Task 5.4: Copy Existing Stacks and Adjust

**Source:** `/c/Users/Admin/Documents/Workspace/Pulumi-2/aws/build/<stack>/v2/`
**Destination:** `/c/Users/Admin/Documents/Workspace/cloud/stacks/<stack>/`

#### 5.4.1: Copy Stack Documents

**For each stack:**

**Source files:**
```
/c/Users/Admin/Documents/Workspace/Pulumi-2/aws/build/<stack>/v2/docs/
├── Stack_Prompt_Main.md
├── Stack_Prompt_Extra.md
├── Stack_Definitions.md
├── Stack_Resources.md
├── Stack_History_Errors.md
├── Stack_History_Fixes.md
└── Stack_History.md
```

**Destination:**
```
/c/Users/Admin/Documents/Workspace/cloud/stacks/<stack>/docs/
```

**Adjustments for EACH file:**
1. Read file content
2. Replace "multi-stack" → "cloud"
3. Replace "staging" → "stage"
4. Update directory paths:
   - `/Pulumi-2/aws/build/` → `/cloud/stacks/`
   - `./aws/build/` → `./cloud/stacks/`
   - `/admin/v2/` → `/cloud/tools/`
   - `./admin/v2/` → `./cloud/tools/`
   - `/resources/` → `/src/` (for component references)
   - `resources/` → `src/` (for component references)
5. Update references to Architecture 2.x → **3.1** (not 3.0)
6. Update stack naming references to v3.1 format:
   - OLD: `D1BRV40-dev` → NEW: `D1BRV40-network-dev`
7. Write to new location

**Stacks to process:** (16 total)
- network
- security
- dns
- secrets
- authentication
- storage
- database-rds
- containers-images
- containers-apps
- services-ecr
- services-ecs
- services-eks
- services-api
- compute-ec2
- compute-lambda
- monitoring

**NOTE:** Stack names have changed! Old names like "storage-s3" are now just "storage", "data-rds" is now "database-rds", etc. Map old names to new names per Directory_Structure_Diagram.3.1.md.

#### 5.4.2: Copy Stack Resources (Code)

**For each stack:**

**Source files:**
```
/c/Users/Admin/Documents/Workspace/Pulumi-2/aws/build/<stack>/v2/resources/
├── index.ts (or index.2.2.ts)       # Main entry point
├── Pulumi.yaml
├── package.json
├── tsconfig.json
└── ... (other .ts component files)
```

**Destination (CRITICAL - Different Structure):**
```
/c/Users/Admin/Documents/Workspace/cloud/stacks/<stack>/
├── index.ts                         # ← AT STACK ROOT!
├── src/                             # ← Component files go here
│   └── ... (other .ts files)
├── Pulumi.yaml
└── package.json
```

**Adjustments for EACH file:**

**For index.ts:**
1. If `index.2.2.ts` exists, rename to `index.ts`
2. **Place at stack root** (not in src/)
3. Update imports for moved components:
   ```typescript
   // If components moved to src/:
   import { VPCComponent } from "./src/vpc";
   import { SubnetComponent } from "./src/subnets";
   ```
4. Replace "multi-stack" → "cloud" in comments
5. Update StackReference naming (CRITICAL for v3.1):
   ```typescript
   // OLD (v2.3): `${orgName}/network/${environment}`
   // OLD (v3.0): `${deploymentId}-${environment}`
   // NEW (v3.1): `${orgName}/${projectName}/${deploymentId}-${stackName}-${environment}`

   // Example:
   const networkStack = new pulumi.StackReference(
       `${orgName}/${projectName}/${deploymentId}-network-${environment}`
   );
   // Actual: acme-corp/ecommerce/D1BRV40-network-dev
   ```
6. Ensure DependencyResolver usage (from Arch 3.1)
7. Update Pulumi Project references to business project (not stack)

**For component files (if they exist):**
1. Move to `src/` subdirectory
2. Update relative imports if needed
3. Keep all other code as-is

**For Pulumi.yaml:**
1. Update `name` field if needed
2. Ensure `main: index.ts` (at root, not src/index.ts)
3. Minimal configuration (per Arch 3.1)
4. Example:
   ```yaml
   name: network
   runtime:
     name: nodejs
     options:
       typescript: true
   description: Network infrastructure stack
   main: index.ts              # ← Points to root index.ts
   ```

**For package.json:**
1. Update dependencies to latest versions
2. Update scripts if needed
3. Ensure consistency across stacks
4. Ensure version is 0.7.0 (platform version)

**For tsconfig.json:**
1. Standard TypeScript configuration
2. Ensure paths work with new structure
3. Example:
   ```json
   {
     "compilerOptions": {
       "target": "ES2020",
       "module": "commonjs",
       "strict": true,
       "esModuleInterop": true,
       "skipLibCheck": true,
       "forceConsistentCasingInFileNames": true,
       "outDir": "./bin",
       "rootDir": "."
     },
     "include": ["index.ts", "src/**/*.ts"],
     "exclude": ["node_modules", "bin"]
   }
   ```

---

### Task 5.5: Consult Existing Documents (If Needed)

**Reference documents** (may contain outdated info):
- Multi_Stack_Architecture.2.2.md
- Prompt-9-1 - PULUMI_CONFIGURATION_QUESTIONS_ANSWERS.md
- Prompt-9-3 - PULUMI_CONFIGURATION_FINAL_SOLUTION.md
- Prompt-9-5 - DEPLOYMENT_INITIALIZATION_ANSWERS.md
- All Prompt-10 Response documents

**⚠️ WARNING:** These documents are OUTDATED. **Architecture 3.1 is authoritative.**

Use these ONLY if:
- You need historical context for a specific decision
- Architecture 3.1 doesn't provide enough detail on a legacy feature
- You're debugging an issue related to old code

---

### Task 5.6: Implement Python CLI Tool

**Reference:** `/c/Users/Admin/Documents/Workspace/cloud/tools/docs/CLI_Commands_Reference.3.1.md`

**Technology Stack:**
- **Language:** Python 3.11+
- **CLI Framework:** Click or Typer (recommend Typer for type safety)
- **Validation:** Pydantic v2
- **Configuration:** PyYAML
- **Rich Output:** Rich library
- **Logging:** Standard logging module
- **Testing:** pytest
- **Type Checking:** mypy

**Structure (per Directory_Structure_Diagram.3.1.md):**
```
/c/Users/Admin/Documents/Workspace/cloud/tools/cli/
├── src/
│   ├── __init__.py
│   ├── main.py                      # CLI entry point
│   ├── commands/                    # Command implementations
│   │   ├── __init__.py
│   │   ├── init_cmd.py              # cloud init
│   │   ├── deploy_cmd.py            # cloud deploy
│   │   ├── deploy_stack_cmd.py      # cloud deploy-stack
│   │   ├── destroy_cmd.py           # cloud destroy
│   │   ├── destroy_stack_cmd.py     # cloud destroy-stack
│   │   ├── rollback_cmd.py          # cloud rollback
│   │   ├── environment_cmd.py       # cloud enable/disable/list-environments
│   │   ├── stack_cmd.py             # cloud register/update/unregister/list-stacks
│   │   ├── validate_cmd.py          # cloud validate*
│   │   ├── template_cmd.py          # cloud *-template
│   │   ├── status_cmd.py            # cloud status
│   │   ├── list_cmd.py              # cloud list
│   │   ├── logs_cmd.py              # cloud logs
│   │   └── discover_cmd.py          # cloud discover-resources
│   ├── orchestrator/                # Orchestration engine
│   │   ├── __init__.py
│   │   ├── orchestrator.py          # Main orchestration logic
│   │   ├── dependency_resolver.py   # Dependency graph resolution
│   │   └── runtime_resolver.py      # Runtime placeholder resolution
│   ├── templates/                   # Template management
│   │   ├── __init__.py
│   │   ├── template_manager.py      # Template loading/rendering
│   │   └── manifest_generator.py    # Manifest generation
│   ├── deployment/                  # Deployment management
│   │   ├── __init__.py
│   │   ├── deployment_manager.py    # Deployment state management
│   │   └── state_manager.py         # Pulumi state integration
│   ├── runtime/                     # Runtime resolution
│   │   ├── __init__.py
│   │   ├── placeholder_resolver.py  # Resolve {{placeholders}}
│   │   └── config_resolver.py       # Config value resolution
│   ├── pulumi/                      # Pulumi integration
│   │   ├── __init__.py
│   │   ├── pulumi_wrapper.py        # Pulumi automation API wrapper
│   │   └── stack_operations.py      # Stack up/destroy/preview
│   ├── validation/                  # Validation
│   │   ├── __init__.py
│   │   ├── manifest_validator.py    # Manifest syntax/structure
│   │   ├── dependency_validator.py  # Circular dependency detection
│   │   ├── aws_validator.py         # AWS credentials/permissions
│   │   └── pulumi_validator.py      # Pulumi state access
│   └── utils/                       # Utilities
│       ├── __init__.py
│       ├── deployment_id.py         # Deployment ID generation
│       ├── logger.py                # Logging utilities
│       └── helpers.py               # General helpers
├── tests/
│   ├── __init__.py
│   ├── test_commands/
│   │   ├── test_init.py
│   │   ├── test_deploy.py
│   │   └── ...
│   ├── test_orchestrator/
│   │   ├── test_dependency_resolver.py
│   │   └── ...
│   └── test_validation/
│       ├── test_manifest_validator.py
│       └── ...
├── requirements.txt                 # Dependencies
├── setup.py                         # Package setup
├── pyproject.toml                   # Modern Python project config
└── README.md
```

**Implementation Approach:**

1. **Setup Project:**
   ```bash
   cd /c/Users/Admin/Documents/Workspace/cloud/tools/cli

   # Create pyproject.toml
   cat > pyproject.toml <<EOF
   [build-system]
   requires = ["setuptools>=68.0", "wheel"]
   build-backend = "setuptools.build_meta"

   [project]
   name = "cloud-cli"
   version = "0.7.0"
   description = "Multi-Stack Cloud Platform CLI"
   requires-python = ">=3.11"
   dependencies = [
       "typer>=0.9.0",
       "pydantic>=2.0",
       "pyyaml>=6.0",
       "rich>=13.0",
       "pulumi>=3.0",
   ]

   [project.scripts]
   cloud = "cloud_cli.main:app"
   EOF

   # Create requirements.txt
   cat > requirements.txt <<EOF
   typer[all]==0.9.0
   pydantic==2.5.0
   pyyaml==6.0.1
   rich==13.7.0
   pulumi==3.98.0
   click==8.1.7
   pytest==7.4.3
   mypy==1.7.1
   EOF

   # Install in development mode
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e .
   ```

2. **Main CLI Entry Point (src/main.py):**
   ```python
   #!/usr/bin/env python3
   """Cloud Platform CLI - Main Entry Point"""

   import typer
   from typing import Optional
   from rich.console import Console

   from cloud_cli.commands import (
       init_cmd,
       deploy_cmd,
       destroy_cmd,
       validate_cmd,
       status_cmd,
       # ... import all command modules
   )

   app = typer.Typer(
       name="cloud",
       help="Multi-Stack Cloud Platform CLI v0.7",
       no_args_is_help=True,
   )
   console = Console()

   # Register commands
   app.add_typer(init_cmd.app, name="init")
   app.add_typer(deploy_cmd.app, name="deploy")
   app.add_typer(destroy_cmd.app, name="destroy")
   # ... register all commands

   @app.callback()
   def main(
       verbose: bool = typer.Option(False, "--verbose", "-v"),
       debug: bool = typer.Option(False, "--debug"),
   ):
       """Cloud Platform CLI"""
       if debug:
           console.print("[yellow]Debug mode enabled[/yellow]")

   if __name__ == "__main__":
       app()
   ```

3. **Example Command (src/commands/init_cmd.py):**
   ```python
   """Cloud init command - Initialize new deployment"""

   import typer
   from pathlib import Path
   from rich.console import Console
   from typing import Optional

   from cloud_cli.deployment.deployment_manager import DeploymentManager
   from cloud_cli.utils.deployment_id import generate_deployment_id

   app = typer.Typer()
   console = Console()

   @app.command()
   def init(
       org: str = typer.Option(..., "--org", help="Organization name"),
       project: str = typer.Option(..., "--project", help="Project name"),
       template: str = typer.Option("default", "--template", "-t"),
       deployment_id: Optional[str] = typer.Option(None, "--id"),
   ):
       """Initialize a new deployment"""

       # Generate deployment ID if not provided
       if not deployment_id:
           deployment_id = generate_deployment_id()

       console.print(f"[green]Initializing deployment:[/green] {deployment_id}")
       console.print(f"  Organization: {org}")
       console.print(f"  Project: {project}")
       console.print(f"  Template: {template}")

       # Use deployment manager to create deployment
       manager = DeploymentManager()
       deployment_dir = manager.create_deployment(
           deployment_id=deployment_id,
           org=org,
           project=project,
           template=template,
       )

       console.print(f"[green]✓[/green] Deployment created at: {deployment_dir}")
   ```

4. **Core Commands to Implement:**
   - `cloud init` - Initialize deployment
   - `cloud deploy` - Deploy all stacks
   - `cloud deploy-stack` - Deploy single stack
   - `cloud destroy` - Destroy all stacks
   - `cloud destroy-stack` - Destroy single stack
   - `cloud validate` - Validate deployment
   - `cloud status` - Show deployment status
   - `cloud list` - List deployments
   - All other commands per CLI_Commands_Reference.3.1.md

5. **Integration with Pulumi:**
   ```python
   # src/pulumi/pulumi_wrapper.py

   import pulumi
   from pulumi import automation as auto

   class PulumiWrapper:
       """Wrapper for Pulumi Automation API"""

       def deploy_stack(
           self,
           stack_name: str,
           project_name: str,
           work_dir: str,
       ):
           """Deploy a Pulumi stack"""
           stack = auto.create_or_select_stack(
               stack_name=stack_name,
               project_name=project_name,
               work_dir=work_dir,
           )

           # Run pulumi up
           up_res = stack.up(on_output=print)
           return up_res
   ```

**IMPORTANT:** All CLI code must use v3.1 naming conventions:
- Stack names: `<deployment-id>-<stack-name>-<environment>`
- Deployment directories: `<deployment-id>-<org>-<project>/`
- Pulumi projects: Business project names (not stack names)

---

### Task 5.7: Implement Validation Tools (Python)

**Reference:** `/c/Users/Admin/Documents/Workspace/cloud/tools/docs/Addendum_Verification_Architecture.3.1.md`

**Validation Tools to Implement (Python):**

1. **Manifest Validator (src/validation/manifest_validator.py)**
   ```python
   from pydantic import BaseModel, ValidationError
   import yaml

   class ManifestValidator:
       """Validates deployment manifest structure"""

       def validate(self, manifest_path: str) -> bool:
           """Validate manifest file"""
           with open(manifest_path) as f:
               data = yaml.safe_load(f)

           # Use Pydantic to validate structure
           try:
               DeploymentManifest(**data)
               return True
           except ValidationError as e:
               print(f"Validation error: {e}")
               return False
   ```

2. **Dependency Validator (src/validation/dependency_validator.py)**
   ```python
   class DependencyValidator:
       """Validates stack dependencies and detects cycles"""

       def validate_dependencies(self, stacks: dict) -> bool:
           """Check for circular dependencies"""
           # Build dependency graph
           # Detect cycles using DFS
           pass
   ```

3. **AWS Credentials Validator (src/validation/aws_validator.py)**
   ```python
   import boto3

   class AWSValidator:
       """Validates AWS credentials and permissions"""

       def validate_credentials(self) -> bool:
           """Check AWS credentials are valid"""
           try:
               sts = boto3.client('sts')
               identity = sts.get_caller_identity()
               return True
           except Exception as e:
               print(f"AWS validation failed: {e}")
               return False
   ```

4. **Pulumi State Validator (src/validation/pulumi_validator.py)**
   ```python
   class PulumiValidator:
       """Validates Pulumi Cloud access"""

       def validate_pulumi_access(self) -> bool:
           """Check Pulumi Cloud is accessible"""
           # Check PULUMI_ACCESS_TOKEN
           # Verify can list stacks
           pass
   ```

**Implementation:**
- Create validator classes in `src/validation/`
- Implement validation logic per Arch 3.1
- Use Pydantic for schema validation
- Create unit tests with pytest
- Integrate with CLI commands (cloud validate-*)

---

### Task 5.8: Generate Generic Document Templates

**Purpose:** Templates for creating new stacks

**Location:** `/c/Users/Admin/Documents/Workspace/cloud/tools/templates/docs/`

**Templates to create:**

1. **Stack_Prompt_Main.md.template**
   - Generic version of stack prompt
   - Based on existing stack prompts
   - Adjusted to Arch 3.1

2. **Stack_Prompt_Extra.md.template**
   - Additional prompt instructions template
   - For custom stack requirements

3. **Stack_Definitions.md.template**
   - Stack definitions template
   - Generated from prompt execution

4. **Stack_Resources.md.template**
   - Stack resources template
   - Generated from prompt execution

5. **Stack_History_Errors.md.template**
   - Error tracking template

6. **Stack_History_Fixes.md.template**
   - Fix tracking template

7. **Stack_History.md.template**
   - Full history template

**Implementation:**
1. Review existing stack docs (from 5.4.1)
2. Extract common patterns
3. Create generic versions with placeholders
4. Example placeholders: `{{STACK_NAME}}`, `{{DESCRIPTION}}`, etc.

---

### Task 5.9: Generate Generic Pulumi File Templates

**Purpose:** Templates for creating new stack implementations

**Location:** `/c/Users/Admin/Documents/Workspace/cloud/tools/templates/stack/`

**CRITICAL:** Match the authoritative structure - `index.ts` at root!

**Templates to create:**

1. **index.ts.template** (AT ROOT)
   ```typescript
   import * as pulumi from "@pulumi/pulumi";
   import * as aws from "@pulumi/aws";

   // Optional: Import components from src/
   // import { VPCComponent } from "./src/vpc";

   // Get configuration
   const config = new pulumi.Config();
   const deploymentId = config.require("deploymentId");
   const stackName = config.require("stackName");
   const environment = config.require("environment");
   const projectName = config.require("projectName");
   const orgName = config.require("orgName");

   // Stack implementation for {{STACK_NAME}}
   // TODO: Implement resources

   // Example: Reference another stack
   /*
   const networkStack = new pulumi.StackReference(
       `${orgName}/${projectName}/${deploymentId}-network-${environment}`
   );
   const vpcId = networkStack.getOutput("vpcId");
   */

   // Export outputs
   export const stack = stackName;
   export const deployment = deploymentId;
   export const env = environment;
   ```

2. **src/component-example.ts.template**
   ```typescript
   import * as pulumi from "@pulumi/pulumi";
   import * as aws from "@pulumi/aws";

   export interface ComponentArgs {
       // Component arguments
   }

   export class ComponentExample extends pulumi.ComponentResource {
       // Component implementation
   }
   ```

3. **src/outputs.ts.template**
   ```typescript
   // Centralized output definitions
   export interface StackOutputs {
       // Output types
   }
   ```

4. **Pulumi.yaml.template**
   ```yaml
   name: {{STACK_NAME}}
   runtime:
     name: nodejs
     options:
       typescript: true
   description: {{STACK_DESCRIPTION}}
   main: index.ts              # ← Points to root index.ts
   ```

5. **package.json.template**
   ```json
   {
     "name": "{{STACK_NAME}}",
     "version": "0.7.0",
     "main": "index.ts",
     "devDependencies": {
       "@types/node": "^20",
       "typescript": "^5.0"
     },
     "dependencies": {
       "@pulumi/pulumi": "^3.0",
       "@pulumi/aws": "^6.0"
     }
   }
   ```

6. **tsconfig.json.template**
   ```json
   {
     "compilerOptions": {
       "target": "ES2020",
       "module": "commonjs",
       "strict": true,
       "esModuleInterop": true,
       "skipLibCheck": true,
       "forceConsistentCasingInFileNames": true,
       "outDir": "./bin",
       "rootDir": "."
     },
     "include": ["index.ts", "src/**/*.ts"],
     "exclude": ["node_modules", "bin"]
   }
   ```

**Implementation:**
1. Review existing stack implementations (from 5.4.2)
2. Extract common patterns
3. Create generic templates with placeholders
4. **Ensure index.ts.template is at root, not in src/**
5. Test templates can be used for new stacks

---

### Task 5.10: No Migration Needed

**Note:** No need to backup or migrate any deployments.

This task is a no-op. Just acknowledge and continue.

---

## Execution Instructions

### Step 1: Pre-Session Verification

Run all checks from "Pre-Session Verification" section above.

**If any check fails, STOP and resolve!**

### Step 2: Create Directory Structure (Task 5.3)

```bash
# Start from Workspace root
cd /c/Users/Admin/Documents/Workspace

# Create root
mkdir -p cloud

# Create main structure
mkdir -p cloud/{deploy,stacks,tools}

# Create tools structure
mkdir -p cloud/tools/{api,cli,docs,templates}

# Create templates structure (CRITICAL: correct subdirectory names)
mkdir -p cloud/tools/templates/{docs,stack,config,default,custom}
mkdir -p cloud/tools/templates/stack/src  # For component templates

# Create Python CLI structure (per authoritative diagram)
mkdir -p cloud/tools/cli/{src,tests}
mkdir -p cloud/tools/cli/src/{commands,orchestrator,templates,deployment,runtime,pulumi,validation,utils}
mkdir -p cloud/tools/cli/tests/{test_commands,test_orchestrator,test_validation}

# Verify structure
ls -la cloud/
ls -la cloud/tools/
ls -la cloud/tools/templates/
ls -la cloud/tools/cli/src/
```

**Expected output:**
```
cloud/
├── deploy/
├── stacks/
└── tools/
    ├── api/
    ├── cli/
    │   ├── src/
    │   │   ├── commands/
    │   │   ├── orchestrator/
    │   │   ├── templates/
    │   │   ├── deployment/
    │   │   ├── runtime/
    │   │   ├── pulumi/
    │   │   ├── validation/
    │   │   └── utils/
    │   └── tests/
    ├── docs/  (already has 16 .3.1.md files)
    └── templates/
        ├── config/
        ├── custom/
        ├── default/
        ├── docs/
        └── stack/        # ← Singular, with src/ subdirectory
            └── src/
```

### Step 3: Verify Documents Already in Place

```bash
# Session 1 already placed documents here
ls -la /c/Users/Admin/Documents/Workspace/cloud/tools/docs/*.3.1.md | wc -l
# Should show: 16
```

**No copying needed - documents are already in place!**

### Step 4: Create Stack Structure

```bash
cd /c/Users/Admin/Documents/Workspace

# Create all 16 stack directories (per Directory_Structure_Diagram.3.1.md)
for stack in network security dns secrets authentication storage database-rds \
             containers-images containers-apps services-ecr services-ecs services-eks \
             services-api compute-ec2 compute-lambda monitoring; do
    mkdir -p cloud/stacks/$stack/{docs,src}
done

# Verify
ls -la cloud/stacks/ | wc -l
# Should show: 18 (16 stacks + . + ..)
```

### Step 5: Copy and Adjust Stacks (Task 5.4)

**Define paths:**
```bash
cd /c/Users/Admin/Documents/Workspace

SOURCE_ROOT=/c/Users/Admin/Documents/Workspace/Pulumi-2
DEST_ROOT=/c/Users/Admin/Documents/Workspace/cloud
```

**Process systematically:**

1. **Map old stack names to new names:**
   ```bash
   # Old Pulumi-2 names → New cloud names
   # storage-s3        → storage
   # compute-ec2       → compute-ec2 (same)
   # compute-ecs       → services-ecs
   # compute-lambda    → compute-lambda (same)
   # data-rds          → database-rds
   # data-dynamodb     → (may not exist in new structure)
   # data-elasticache  → (may not exist in new structure)
   # messaging-sqs     → (check if exists)
   # messaging-sns     → (check if exists)
   # api-gateway       → services-api
   # cdn-cloudfront    → (check if exists)
   # cicd-codepipeline → (check if exists)

   # Verify which stacks exist in Pulumi-2:
   ls -la $SOURCE_ROOT/aws/build/
   ```

2. **Copy docs for each stack:**
   ```bash
   # Example for network stack
   STACK_OLD=network
   STACK_NEW=network

   # Copy docs
   cp -r $SOURCE_ROOT/aws/build/$STACK_OLD/v2/docs/* \
         $DEST_ROOT/stacks/$STACK_NEW/docs/

   # Adjust each doc file (implement replacement logic)
   # - Replace "multi-stack" → "cloud"
   # - Replace "staging" → "stage"
   # - Update paths
   # - Update architecture references to 3.1
   ```

3. **Copy and restructure code:**
   ```bash
   # CRITICAL: Different destination structure!

   # If source has index.ts at resources/ root:
   if [ -f $SOURCE_ROOT/aws/build/$STACK_OLD/v2/resources/index.ts ]; then
       cp $SOURCE_ROOT/aws/build/$STACK_OLD/v2/resources/index.ts \
          $DEST_ROOT/stacks/$STACK_NEW/index.ts  # ← To stack root!
   elif [ -f $SOURCE_ROOT/aws/build/$STACK_OLD/v2/resources/index.2.2.ts ]; then
       cp $SOURCE_ROOT/aws/build/$STACK_OLD/v2/resources/index.2.2.ts \
          $DEST_ROOT/stacks/$STACK_NEW/index.ts  # ← Rename and to root!
   fi

   # Copy other component files to src/
   for file in $SOURCE_ROOT/aws/build/$STACK_OLD/v2/resources/*.ts; do
       filename=$(basename "$file")
       if [[ "$filename" != "index"* ]]; then
           cp "$file" $DEST_ROOT/stacks/$STACK_NEW/src/
       fi
   done

   # Copy config files to stack root
   cp $SOURCE_ROOT/aws/build/$STACK_OLD/v2/resources/Pulumi.yaml \
      $DEST_ROOT/stacks/$STACK_NEW/
   cp $SOURCE_ROOT/aws/build/$STACK_OLD/v2/resources/package.json \
      $DEST_ROOT/stacks/$STACK_NEW/
   cp $SOURCE_ROOT/aws/build/$STACK_OLD/v2/resources/tsconfig.json \
      $DEST_ROOT/stacks/$STACK_NEW/

   # Adjust index.ts for new structure
   # - Update imports: "./component" → "./src/component"
   # - Update StackReference format to v3.1
   # - Update project references
   ```

**Final structure should be:**
```
cloud/stacks/network/
├── index.ts              # ← Main entry at root!
├── docs/
│   └── ... (all docs)
├── src/                  # ← Components here
│   ├── vpc.ts
│   ├── subnets.ts
│   └── outputs.ts
├── Pulumi.yaml
└── package.json
```

### Step 6: Implement Python CLI (Task 5.6)

```bash
cd /c/Users/Admin/Documents/Workspace/cloud/tools/cli

# Create pyproject.toml and requirements.txt (see Task 5.6)
# Create src/__init__.py
# Create src/main.py

# Set up Python environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -e .

# Verify CLI works
cloud --help
```

**Implementation order:**
1. Setup project structure and dependencies
2. Implement main.py with Typer
3. Implement core commands:
   - init, validate, status, list
4. Implement deployment commands:
   - deploy, deploy-stack, destroy, destroy-stack
5. Implement management commands:
   - Stack management, environment management, templates
6. Create unit tests with pytest

### Step 7: Implement Validation (Task 5.7)

1. Create validator classes in `src/validation/`
2. Implement validation logic per Arch 3.1
3. Use Pydantic for schema validation
4. Create unit tests with pytest
5. Integrate with CLI commands

### Step 8: Create Templates (Task 5.8-5.9)

1. **Generate doc templates** (5.8) in `templates/docs/`
2. **Generate Pulumi templates** (5.9) in `templates/stack/`
   - **CRITICAL:** index.ts.template at root
   - src/ subdirectory for component templates
3. Test templates are usable

---

## Critical Notes

### ⚠️ SCOPE BOUNDARY

**WHAT THIS SESSION DOES:**
- ✅ Create directory structure (per Directory_Structure_Diagram.3.1.md)
- ✅ Migrate all 16 stacks (index.ts at stack root)
- ✅ Implement Python CLI tool (25+ commands)
- ✅ Implement validation tools (Python)
- ✅ Create templates (index.ts at template root)

**WHAT THIS SESSION DOES NOT DO:**
- ❌ Implement REST API (Session 3)
- ❌ Implement WebSockets (Session 3)
- ❌ Database integration (Session 3)
- ❌ Deploy to AWS (manual testing later)

### 📝 Key Structure Fixes

1. **Stack Structure:**
   - ✅ index.ts at stack root (not in src/)
   - ✅ src/ for optional component breakdown
   - ✅ Pulumi.yaml at stack root
   - ✅ main: index.ts (points to root)

2. **CLI Structure:**
   - ✅ Python 3.11+ (not TypeScript)
   - ✅ src/ contains all modules
   - ✅ Organized by function (commands/, orchestrator/, etc.)
   - ✅ Uses Typer for CLI framework

3. **Template Structure:**
   - ✅ index.ts.template at templates/stack/ root
   - ✅ src/ subdirectory in template for components
   - ✅ Matches actual stack structure

### 🔗 Continuity to Session 3

**Handoff Deliverables:**

1. Complete directory structure (per authoritative diagram)
2. All 16 stacks migrated (correct structure)
3. Python CLI tool implemented and tested
4. Validation tools working
5. Templates ready for use

**Session 3 Will Add:**
- REST API implementation (Python/FastAPI)
- WebSocket monitoring
- Database integration planning
- Deployment documentation

---

## Success Criteria

### Session 2 is complete when:

1. ✅ Directory structure matches Directory_Structure_Diagram.3.1.md exactly
2. ✅ All 16 stack docs migrated (check docs/ subdirectories)
3. ✅ All 16 stack code migrated (index.ts at root, components in src/)
4. ✅ Python CLI framework implemented (Typer + project structure)
5. ✅ All CLI commands implemented (25+ command files)
6. ✅ Validation tools implemented (Python, src/validation/)
7. ✅ Doc templates created (templates/docs/)
8. ✅ Pulumi templates created (index.ts at templates/stack/ root)
9. ✅ Unit tests created and passing (pytest)
10. ✅ Platform ready for manual testing

### Verification Commands:

```bash
# Check stack structure (index.ts at root)
ls -la /c/Users/Admin/Documents/Workspace/cloud/stacks/network/
# Should show: index.ts, docs/, src/, Pulumi.yaml, package.json

# Check CLI structure
ls -la /c/Users/Admin/Documents/Workspace/cloud/tools/cli/src/
# Should show: main.py, commands/, orchestrator/, validation/, etc.

# Check template structure
ls -la /c/Users/Admin/Documents/Workspace/cloud/tools/templates/stack/
# Should show: index.ts.template, src/, Pulumi.yaml.template, etc.

# Test CLI
cloud --help
cloud --version

# Run tests
cd /c/Users/Admin/Documents/Workspace/cloud/tools/cli
pytest tests/
```

---

## Token Budget Monitoring

**Expected Usage:**
- Task 5.1-5.3 (Setup): ~5-10K tokens
- Task 5.4 (Stack migration): ~25-35K tokens (more complex with restructuring)
- Task 5.6 (Python CLI): ~35-45K tokens (Python vs TypeScript)
- Task 5.7 (Validation): ~15-20K tokens
- Task 5.8-5.9 (Templates): ~10-15K tokens
- **Total: ~90-125K tokens**

**If approaching 180K tokens:**
- Stop implementation
- Save progress
- Document what remains
- Continue in new session

---

## Emergency Recovery

**If session crashes:**

1. **Check progress:**
   ```bash
   # Check directory created
   ls -la /c/Users/Admin/Documents/Workspace/cloud

   # Check stacks migrated
   ls -la /c/Users/Admin/Documents/Workspace/cloud/stacks/

   # Check if index.ts is at root (not in src/)
   find /c/Users/Admin/Documents/Workspace/cloud/stacks/ -name "index.ts"

   # Check Python CLI progress
   ls -la /c/Users/Admin/Documents/Workspace/cloud/tools/cli/src/
   ```

2. Resume from last completed task
3. Use this prompt to continue
4. Reference Architecture 3.1 and Directory_Structure_Diagram.3.1.md

---

## Summary of Fixes in Session 2.1

**Issues Fixed from Session-2-Prompt.3.1.IMPROVED.md:**

1. ✅ **Line 237 Fix:** index.ts now correctly placed at stack root (not in src/)
2. ✅ **Line 357 Fix:** Destination paths verified against Directory_Structure_Diagram.3.1.md
3. ✅ **Line 442 Fix:** CLI directory structure now matches authoritative diagram
4. ✅ **Major Change:** CLI now uses Python 3.11+ (not TypeScript/Node.js)
5. ✅ **Template Structure:** index.ts.template at templates/stack/ root (not in src/)
6. ✅ **All paths:** Verified against authoritative Directory_Structure_Diagram.3.1.md

**Python CLI Advantages:**
- Better Pulumi integration (Python Automation API)
- Simpler dependency management
- Standard for infrastructure/DevOps tools
- Rich ecosystem (Typer, Pydantic, Rich)
- Easier maintenance for ops teams
- Type safety with type hints + mypy

---

## Final Checklist

**Before marking Session 2 complete:**

- [ ] Directory structure matches Directory_Structure_Diagram.3.1.md
- [ ] All 16 stacks have index.ts at root (not in src/)
- [ ] All 16 stacks have src/ subdirectory for components
- [ ] Python CLI framework implemented (Typer + structure)
- [ ] All Python CLI commands implemented (25+ commands)
- [ ] Python validation tools implemented (src/validation/)
- [ ] Doc templates created (templates/docs/)
- [ ] Pulumi templates have index.ts at root (templates/stack/)
- [ ] Python unit tests created and passing (pytest)
- [ ] Token budget within limits
- [ ] Ready for Session 3

---

## Next Steps

**After Session 2 Completion:**

1. Manual testing of Python CLI commands
2. Validation of stack implementations (index.ts at root)
3. Test stack builds: `cd stacks/network && npm install && npm run build`
4. User review of implementation
5. If approved: Proceed to Session 3
6. Session 3: REST API (Python/FastAPI), WebSockets, Database planning

---

**Session 2.1 Status:** Ready to Execute
**Expected Outcome:** Fully functional core platform with Python CLI
**Estimated Duration:** Full session (~90-125K tokens)
**Success Probability:** 95% (with all fixes applied)

---

**Document Version:** 2.1
**Date:** 2025-10-21
**Session:** 2 of 3
**Supersedes:** Session-2-Prompt.3.1.IMPROVED.md (v2.0)
**Changes:** Python CLI, correct directory structure, verified against authoritative diagram
