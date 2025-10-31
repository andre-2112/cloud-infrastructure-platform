# Cloud Infrastructure Orchestration Platform v4.8

**Version:** 4.8
**Platform:** cloud-0.7
**Date:** 2025-10-31
**Status:** Complete Implementation Blueprint
**Classification:** Production-Ready Architecture with Enhanced Template System, Auto-Extraction, Template-First Validation, and Dynamic Pulumi.yaml Management

**Changes from v3.1 to v4.1:**
- **MAJOR:** Python-based CLI implementation (not TypeScript) using Typer framework
- **MAJOR:** Core/CLI architecture split - `tools/core/cloud_core/` (business logic) + `tools/cli/cloud_cli/` (interface)
- **MAJOR:** Enhanced template system with structured `parameters.inputs` and `parameters.outputs`
- **MAJOR:** Auto-extraction system - automatically generate templates from TypeScript stack code
- **MAJOR:** Template-first validation - StackCodeValidator ensures code-template consistency
- **MAJOR:** Pulumi native config format - `stackname:key: "value"` in YAML files
- **MAJOR:** Simplified placeholder syntax - `${stack.output}` or `{{stack.output}}`
- **MAJOR:** Config files moved to `deploy/<id>/config/` subdirectory
- **MAJOR:** Updated Pulumi Stack naming to `<deployment-id>-<stack-name>-<environment>`
- Updated directory structure documentation to reflect Python implementation
- Enhanced cross-stack dependency validation
- Improved manifest specification with better examples

**Changes from v4.1 to v4.6:**
- **MAJOR:** Dynamic Pulumi.yaml generation using context manager pattern
- **MAJOR:** Deployment-specific project naming in Pulumi Cloud organization
- **MAJOR:** All stacks disabled by default in deployment templates
- Pulumi.yaml backup and restore mechanism with retry logic
- Support for concurrent deployments with project-specific backups
- Enhanced PulumiWrapper with deployment_context() method
- Guaranteed Pulumi.yaml restoration after stack operations
- Improved deployment organization: `{pulumiOrg}/{project}/{deployment-id}-{stack-name}-{environment}`

**Changes from v4.6 to v4.8:**
- **MAJOR:** Configuration approach change - switched from `pulumi config set` to `--config-file` parameter
- **MAJOR:** Enhanced CLI commands with rich interactive modes
- **MAJOR:** Improved deployment lifecycle with preserved destroyed deployment history
- Config files now generated and stored in deployment directories (no more pulumi config set)
- `cloud list` now filters destroyed deployments by default
- `cloud list --all` shows all deployments including destroyed ones
- `cloud list --rich` provides interactive mode with actions menu (status/config/deploy/destroy)
- `cloud config --rich` offers enhanced UI with environment selection
- `cloud destroy` improved with proper state management and preserved deployment history
- `cloud status` can support `--watch` mode for periodic refresh
- Deployment state properly tracked (initialized, deployed, partial, failed, destroyed)
- Comprehensive AWS error detection and user-friendly messages
- Errors logged to deployment directory under logs/
- Specific remediation guidance for AWS service limit errors

**Alignment with v4.0 Authoritative Documents:**
This document (v4.8) is fully aligned with and extends the v4.0 authoritative documents:
- Complete_Stack_Management_Guide_v4.md
- Stack_Parameters_and_Registration_Guide_v4.md
- Complete_Guide_Templates_Stacks_Config_and_Registration_v4.md
- Addendum_Dynamic_Pulumi_YAML_Implementation.4.1.md (NEW in v4.6)

---

## Document Purpose

This document serves as the **complete implementation blueprint** for the Cloud Infrastructure Orchestration Platform v4.8. It describes:
- Complete architecture incorporating all enhancements from v2.3, v3.1, v4.0, v4.6, and v4.8
- **Core/CLI architecture split** with Python business logic library and CLI interface
- **Enhanced template system** with structured parameters (inputs/outputs with types, defaults, validation)
- **Auto-extraction system** for generating templates from TypeScript stack code
- **Template-first validation** for ensuring code-template consistency
- **Dynamic Pulumi.yaml management** with context manager pattern (NEW in v4.6)
- Template-based deployment initialization system with stack dependencies
- Centralized configuration management with runtime resolution (Pulumi native format)
- Smart partial re-deployment with skip logic
- Enhanced CLI tool with comprehensive commands (Python implementation)
- REST API for remote orchestration
- Real-time progress monitoring via WebSockets
- Multiple TypeScript file support with explicit imports
- Layer-based execution managed by orchestrator
- Verification and validation tools

**This document is intended for:**
- Platform architects designing the system
- Developers implementing stack code, core library, CLI tool, and REST API
- DevOps engineers deploying and operating the platform
- Project managers planning implementation phases

**Note:** All code examples have been moved to the Platform Code Addendum (Addendum_Platform_Code.3.1.md) to keep this document focused on architecture concepts.

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Architecture Overview](#architecture-overview)
3. [What's New in v4.1](#whats-new-in-v41)
4. [What's New in v4.5](#whats-new-in-v45)
5. [What's New in v4.8](#whats-new-in-v48)
6. [Architecture Goals](#architecture-goals)
6. [Core Concepts](#core-concepts)
7. [Core/CLI Architecture](#corecli-architecture)
8. [Directory Structure](#directory-structure)
9. [Stack Management](#stack-management)
10. [Template System](#template-system)
11. [Enhanced Template System (v4.0+)](#enhanced-template-system-v40)
12. [Auto-Extraction System (v4.0+)](#auto-extraction-system-v40)
13. [Template-First Validation (v4.0+)](#template-first-validation-v40)
14. [Dynamic Pulumi.yaml Management (v4.5+)](#dynamic-pulumiyaml-management-v45)
15. [Deployment Initialization](#deployment-initialization)
16. [Configuration Management](#configuration-management)
17. [Multi-Environment Support](#multi-environment-support)
18. [Dependency Resolution](#dependency-resolution)
19. [Cross-Stack Dependencies (Complete Workflow)](#cross-stack-dependencies-complete-workflow)
20. [Runtime Value Resolution](#runtime-value-resolution)
21. [Deployment Orchestration](#deployment-orchestration)
22. [State Management](#state-management)
23. [CLI Tool Specification](#cli-tool-specification)
24. [REST API Specification](#rest-api-specification)
25. [Verification and Validation](#verification-and-validation)
26. [Security and Access Control](#security-and-access-control)
27. [Monitoring and Logging](#monitoring-and-logging)
28. [Known Issues and Future Work](#known-issues-and-future-work)
29. [Implementation Phases](#implementation-phases)
30. [Migration from Architecture 3.1](#migration-from-architecture-31)

---

## Executive Summary

The Cloud Infrastructure Orchestration Platform v4.5 is an enterprise-grade system for managing complex, interdependent AWS infrastructure deployments using Pulumi. Version 4.5 builds on v4.1's enhancements with **dynamic Pulumi.yaml management** for correct deployment-specific project naming in Pulumi Cloud organization structures.

### Key Capabilities

**Core/CLI Architecture (NEW in v4.1)**
- Python-based business logic library (`cloud_core`) separated from CLI interface (`cloud_cli`)
- Modular design with deployment, orchestration, runtime, templates, and validation modules
- Clean separation of concerns for better maintainability and testing
- Reusable core library for future REST API and other interfaces

**Enhanced Template System (v4.0+)**
- Structured parameter declarations with `inputs` and `outputs` sections
- Type specifications (string, number, boolean, array, object)
- Default values and validation rules
- Required/optional parameter flags
- Better documentation and discoverability

**Auto-Extraction System (v4.0+)**
- Automatically extract parameters from TypeScript stack code
- Generate enhanced templates from stack implementations
- ParameterExtractor analyzes Config.require/requireNumber calls
- TypeScriptParser extracts export statements for outputs
- Reduces manual template maintenance

**Template-First Validation (v4.0+)**
- StackCodeValidator ensures code matches template specifications
- Validates all declared inputs are used in code
- Validates all declared outputs are exported in code
- Strict mode for enforcing complete consistency
- Prevents drift between templates and implementations

**Dynamic Pulumi.yaml Management (NEW in v4.5)**
- Context manager pattern for temporary Pulumi.yaml modification
- Automatic backup and restore of original Pulumi.yaml files
- Deployment-specific project naming in Pulumi Cloud: `{pulumiOrg}/{project}/{deployment-id}-{stack-name}-{environment}`
- Support for concurrent deployments with project-specific backup files
- Retry logic for file operations (handles Windows file locking)
- Guaranteed restoration even on errors or interruptions
- Enables proper stack organization by business project in Pulumi Cloud

**Enhanced Configuration Management (v4.0+)**
- Pulumi native config format: `stackname:key: "value"`
- Config files in dedicated `config/` subdirectory
- Simplified placeholder syntax: `${stack.output}` or `{{stack.output}}`
- Better alignment with Pulumi conventions

**Intelligent Deployment Orchestration**
- Smart partial re-deployment with skip logic
- Layer-based execution managed by orchestrator (not Pulumi)
- Automatic dependency resolution from template declarations
- Progress monitoring via WebSockets (real-time updates)
- Parallel execution within dependency layers

**Advanced Configuration Management**
- Minimal stack-level configuration (name, runtime, description only)
- All deployment-specific configuration in deployment directories
- Three-tier value resolution (template defaults → manifest overrides → runtime discovery)
- Runtime placeholders for cross-stack dependencies and AWS queries
- Cross-stack references using DependencyResolver + Runtime Placeholders

**Multi-File Stack Support**
- Multiple TypeScript files per stack
- Explicit imports between files
- Modular resource organization
- Better code maintainability

**Multi-Environment Orchestration**
- Single manifest file supporting dev, stage, and prod environments
- Per-environment stack configuration
- Sequential promotion workflow (dev → stage → prod)
- Environment-specific resource sizing and features

**Enhanced Deployment Tools**
- Python CLI with 25+ commands using Typer framework
- REST API for remote orchestration with authentication
- Real-time deployment progress via WebSocket
- Automated rollback on failures

**Production-Ready Operations**
- Deployment ID format optimized for AWS resource naming (D1BRV40)
- Comprehensive logging and monitoring
- State consistency guarantees
- Complete audit trail

### Platform Statistics

- **16 Infrastructure Stacks**: Covering all major AWS services
- **4 Deployment Templates**: Covering common deployment scenarios
- **25+ CLI Commands**: Complete lifecycle management (Python implementation)
- **15+ REST API Endpoints**: Full remote control capabilities
- **3 Environments**: Dev, stage, and production support per deployment
- **393+ Core Tests**: Comprehensive test coverage for business logic
- **38+ CLI Tests**: CLI interface validation

### Target Deployments

The platform is designed to support:
- **Scale**: Dozens of organizations, each with dozens of projects
- **Deployments**: Hundreds to thousands of individual deployments
- **Isolation**: Complete separation between organizations, projects, and environments
- **Efficiency**: Shared stack code with deployment-specific configuration (99.9% disk space savings)

---

## Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Platform Overview (v4.1)                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐         ┌──────────────┐        ┌──────────────┐ │
│  │              │         │              │        │              │ │
│  │  CLI Tool    │────────▶│ Core Library │───────▶│ Pulumi Cloud │ │
│  │  (Python)    │         │  (Python)    │        │    (State)   │ │
│  └───────┬──────┘         └──────┬───────┘        └──────────────┘ │
│          │                       │                                  │
│          │                       │                                  │
│  ┌───────▼──────┐         ┌──────▼───────┐        ┌──────────────┐ │
│  │              │         │              │        │              │ │
│  │  REST API    │────────▶│  Templates   │        │   AWS Cloud  │ │
│  │  (Future)    │         │    System    │        │  (Resources) │ │
│  └──────────────┘         └──────────────┘        └──────────────┘ │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Core/CLI Architecture (v4.1)

```
┌──────────────────────────────────────────────────────────────────┐
│                    Core/CLI Architecture                          │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  CLI Layer (cloud_cli)                                           │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ commands/                   # CLI command implementations   │ │
│  │ ├── init.py                                                 │ │
│  │ ├── deploy.py                                               │ │
│  │ ├── validate.py                                             │ │
│  │ └── ...                                                     │ │
│  │                                                              │ │
│  │ parser/                     # Auto-extraction system        │ │
│  │ ├── parameter_extractor.py                                  │ │
│  │ └── typescript_parser.py                                    │ │
│  │                                                              │ │
│  │ main.py                     # Typer CLI entry point         │ │
│  └────────────────────────────────────────────────────────────┘ │
│                          │                                        │
│                          │ Calls                                  │
│                          ▼                                        │
│  Core Library (cloud_core)                                       │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ deployment/                 # Deployment management         │ │
│  │ ├── config_generator.py     # Config file generation       │ │
│  │ ├── deployment_manager.py   # Lifecycle management         │ │
│  │ └── state_manager.py        # State operations             │ │
│  │                                                              │ │
│  │ orchestrator/               # Orchestration engine          │ │
│  │ ├── dependency_resolver.py  # Dependency analysis          │ │
│  │ ├── layer_calculator.py     # Layer-based execution        │ │
│  │ └── execution_engine.py     # Stack execution              │ │
│  │                                                              │ │
│  │ runtime/                    # Runtime resolution            │ │
│  │ ├── placeholder_resolver.py # Placeholder handling         │ │
│  │ └── stack_reference_resolver.py # Cross-stack refs         │ │
│  │                                                              │ │
│  │ templates/                  # Template system               │ │
│  │ ├── stack_template_manager.py # Template loading           │ │
│  │ └── manifest_generator.py   # Manifest generation          │ │
│  │                                                              │ │
│  │ validation/                 # Validation system             │ │
│  │ ├── stack_code_validator.py # Template-first validation    │ │
│  │ └── manifest_validator.py   # Manifest validation          │ │
│  │                                                              │ │
│  │ pulumi/                     # Pulumi integration            │ │
│  │ └── pulumi_wrapper.py       # Pulumi command execution     │ │
│  │                                                              │ │
│  │ utils/                      # Utilities                     │ │
│  │ └── logging.py              # Logging infrastructure       │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Configuration Flow (v4.1)                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Enhanced Template Definitions (with parameters)                     │
│  └─▶ Manifest Generation (TemplateManager)                          │
│      └─▶ Config File Generation (ConfigGenerator)                   │
│          └─▶ Runtime Value Resolution (PlaceholderResolver)         │
│              └─▶ Pulumi Execution (PulumiWrapper)                   │
│                  └─▶ AWS Resource Creation                          │
│                      └─▶ State Storage (Pulumi Cloud)               │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Deployment Lifecycle

```
┌──────────────────────────────────────────────────────────────────────┐
│                      Deployment Lifecycle (v4.1)                      │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  1. Initialize                                                        │
│     ├─ Generate deployment ID (D1BRV40)                              │
│     ├─ Create directory structure                                    │
│     ├─ Generate manifest from enhanced template                      │
│     └─ Generate config files from manifest (Pulumi native format)    │
│                                                                       │
│  2. Configure (Optional)                                              │
│     ├─ Edit manifest for custom requirements                         │
│     ├─ Enable/disable specific stacks                                │
│     ├─ Adjust environment-specific configurations                    │
│     └─ Auto-extract parameters if adding new stacks                  │
│                                                                       │
│  3. Validate                                                          │
│     ├─ Validate manifest syntax                                      │
│     ├─ Validate stack dependencies                                   │
│     ├─ Validate stack code against templates (StackCodeValidator)    │
│     ├─ Check AWS credentials and permissions                         │
│     └─ Verify prerequisites                                          │
│                                                                       │
│  4. Deploy to Dev                                                     │
│     ├─ Resolve runtime placeholders (PlaceholderResolver)            │
│     ├─ Execute stacks in dependency order (ExecutionEngine)          │
│     ├─ Monitor progress and log outputs                              │
│     └─ Update state in Pulumi Cloud                                  │
│                                                                       │
│  5. Validate Dev                                                      │
│     ├─ Verify all resources created successfully                     │
│     ├─ Run smoke tests                                               │
│     └─ Check resource inventory                                      │
│                                                                       │
│  6. Promote to Stage                                                  │
│     ├─ Enable stage environment in manifest                          │
│     ├─ Deploy to stage with stage-specific configuration             │
│     └─ Validate stage deployment                                     │
│                                                                       │
│  7. Promote to Production                                             │
│     ├─ Enable production environment in manifest                     │
│     ├─ Deploy to production with production-specific configuration   │
│     └─ Validate production deployment                                │
│                                                                       │
│  8. Monitor & Maintain                                                │
│     ├─ Monitor resource health                                       │
│     ├─ Track costs                                                   │
│     ├─ Apply updates as needed                                       │
│     └─ Handle incidents                                              │
│                                                                       │
│  9. Decommission (When Needed)                                        │
│     ├─ Destroy resources in reverse dependency order                 │
│     ├─ Archive deployment manifest and logs                          │
│     └─ Clean up Pulumi Cloud state                                   │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
```

---

## What's New in v4.1

### Major Enhancements from Architecture 3.1

#### 1. Python-Based Core/CLI Architecture

**Before (Architecture 3.1):**
- CLI tool implemented in TypeScript
- Monolithic CLI implementation
- Single codebase for all functionality
- Limited reusability

**After (v4.1):**
- Core business logic in Python (`cloud_core` package)
- CLI interface in Python (`cloud_cli` package using Typer)
- Clean separation of concerns
- Reusable core library for REST API and other interfaces
- Better testability with 393+ core tests and 38+ CLI tests

**Impact:**
- Easier maintenance and testing
- Reusable business logic across interfaces
- Better performance and reliability
- Industry-standard Python ecosystem
- Type hints for better IDE support

**Location:**
- Core library: `tools/core/cloud_core/`
- CLI tool: `tools/cli/cloud_cli/`

#### 2. Enhanced Template System with Structured Parameters

**Before (Architecture 3.1):**
- Simple template structure
- Basic stack definitions
- Limited parameter documentation
- Manual parameter tracking

**After (v4.1):**
- Structured `parameters.inputs` section with types, defaults, validation
- Structured `parameters.outputs` section with type specifications
- Required/optional flags for better validation
- Rich descriptions for better documentation

**Template Structure Example:**
```yaml
name: network
version: "1.0"
description: "VPC and networking infrastructure"

parameters:
  inputs:
    vpcCidr:
      type: string
      required: true
      default: "10.0.0.0/16"
      description: "CIDR block for VPC"

    availabilityZones:
      type: number
      required: true
      default: 3
      description: "Number of AZs to span"

  outputs:
    vpcId:
      type: string
      description: "VPC ID for cross-stack references"

    privateSubnetIds:
      type: array
      description: "Private subnet IDs"

dependencies: []
layer: 1
```

**Impact:**
- Better parameter documentation and discoverability
- Automated validation of parameter types and requirements
- Foundation for auto-extraction and template-first validation
- Clearer contract between templates and stack code

#### 3. Auto-Extraction System

**Before (Architecture 3.1):**
- Manual template creation
- Manual parameter documentation
- Risk of template-code mismatch
- Labor-intensive maintenance

**After (v4.1):**
- Automatic parameter extraction from TypeScript code
- `ParameterExtractor` analyzes `Config.require()` and `Config.requireNumber()` calls
- `TypeScriptParser` extracts `export` statements for outputs
- Automatic template generation from stack implementations

**Usage:**
```bash
# Auto-extract and register stack
python -m cloud_cli.main register-stack network --auto-extract

# Output:
# Extracting parameters from stacks/network/index.ts...
# Found inputs: vpcCidr (string, required), availabilityZones (number, required)
# Found outputs: vpcId (string), privateSubnetIds (array)
# Template generated: tools/templates/config/network.yaml
```

**Impact:**
- 80-90% reduction in manual template maintenance
- Automatic synchronization between code and templates
- Reduced errors from manual documentation
- Faster stack registration process

**Implementation:**
- `cloud_cli.parser.parameter_extractor` - Extracts inputs from Config API calls
- `cloud_cli.parser.typescript_parser` - Extracts outputs from export statements

#### 4. Template-First Validation

**Before (Architecture 3.1):**
- No code-template consistency checks
- Risk of drift between templates and implementations
- Manual verification required
- Errors discovered at runtime

**After (v4.1):**
- `StackCodeValidator` enforces code-template consistency
- Validates all declared inputs are used in code
- Validates all declared outputs are exported
- Strict mode for zero-tolerance validation
- Warnings for optional parameters not used

**Usage:**
```bash
# Validate single stack
python -m cloud_cli.main validate-stack network

# Strict validation (fail on warnings)
python -m cloud_cli.main validate-stack network --strict

# Validate all stacks
python -m cloud_cli.main validate-stack --all
```

**Validation Output Example:**
```
Validating stack: network
✓ Template: tools/templates/config/network.yaml
✓ Code: stacks/network/index.ts

Input Parameters:
✓ vpcCidr: declared in template, used in code (Config.require)
✓ availabilityZones: declared in template, used in code (Config.requireNumber)
⚠ enableNatGateway: declared in template, not found in code

Output Parameters:
✓ vpcId: declared in template, exported in code
✓ privateSubnetIds: declared in template, exported in code

Result: PASSED with 1 warning
  Use --strict to treat warnings as errors
```

**Impact:**
- Prevents template-code drift
- Catches missing parameters early
- Enforces architectural standards
- Reduces deployment errors

**Implementation:**
- `cloud_core.validation.stack_code_validator` - Validation logic
- Integrated into CLI validation commands

#### 5. Pulumi Native Config Format

**Before (Architecture 3.1):**
- Nested YAML structure
- Custom configuration format
- Complex parsing required

**After (v4.1):**
- Pulumi native format: `stackname:key: "value"`
- Direct compatibility with Pulumi CLI
- Simpler parsing and generation

**Example:**
```yaml
# Before (v3.1) - Nested format
config:
  network:
    vpcCidr: "10.0.0.0/16"
    availabilityZones: 3

# After (v4.1) - Pulumi native format
network:vpcCidr: "10.0.0.0/16"
network:availabilityZones: "3"
aws:region: "us-east-1"
```

**Impact:**
- Better Pulumi ecosystem compatibility
- Simplified config generation (`ConfigGenerator`)
- Direct use with `pulumi config` commands
- Reduced parsing complexity

#### 6. Simplified Placeholder Syntax

**Before (Architecture 3.1):**
- Complex placeholder syntax: `{{RUNTIME:network:vpcId}}`
- Verbose and error-prone

**After (v4.1):**
- Simplified syntax: `${stack.output}` or `{{stack.output}}`
- More intuitive and readable
- Compatible with common templating conventions

**Example:**
```yaml
# Before (v3.1)
subnets: "{{RUNTIME:network:privateSubnetIds}}"

# After (v4.1)
subnets: "${network.privateSubnetIds}"
# or
subnets: "{{network.privateSubnetIds}}"
```

**Impact:**
- Easier to read and write
- Fewer syntax errors
- Better alignment with industry standards
- Simplified `PlaceholderResolver` implementation

#### 7. Config Subdirectory Organization

**Before (Architecture 3.1):**
- Config files in deployment root: `deploy/D1BRV40/network.dev.yaml`
- Mixed with manifest and logs
- Less organized

**After (v4.1):**
- Config files in dedicated subdirectory: `deploy/D1BRV40/config/network.dev.yaml`
- Clear separation from manifest and logs
- Better organization

**Structure:**
```
deploy/D1BRV40-CompanyA-ecommerce/
├── Deployment_Manifest.yaml
├── config/                    # NEW subdirectory
│   ├── network.dev.yaml
│   ├── network.stage.yaml
│   ├── security.dev.yaml
│   └── ...
└── logs/
    └── ...
```

**Impact:**
- Cleaner directory structure
- Easier to manage config files
- Better separation of concerns
- Aligns with common project organization patterns

#### 8. Updated Stack Naming Convention

**Before (Architecture 3.1):**
- Pulumi stack naming: `<deployment-id>-<environment>`
- Limited information in stack name

**After (v4.1):**
- Pulumi stack naming: `<deployment-id>-<stack-name>-<environment>`
- Full context in stack name

**Example:**
```
# Before (v3.1)
D1BRV40-dev
D1BRV40-stage
D1BRV40-prod

# After (v4.1)
D1BRV40-network-dev
D1BRV40-network-stage
D1BRV40-network-prod
D1BRV40-security-dev
```

**Impact:**
- Clearer stack identification in Pulumi Cloud
- Better filtering and searching
- Easier debugging and monitoring
- More explicit stack references

### Carried Forward from v3.1

All major features from v3.1 are preserved:
- Template-based stack dependencies (single source of truth)
- Smart partial re-deployment with skip logic
- Layer-based execution by orchestrator
- Real-time progress monitoring via WebSocket
- Multiple TypeScript files support
- Cross-stack references with DependencyResolver
- Multi-environment support (dev, stage, prod)

---

## What's New in v4.5

### Major Enhancement from Architecture 4.1

#### Dynamic Pulumi.yaml Management

**The Problem:**

In v4.1, the architecture specified that all stacks for a deployment should be organized under one Pulumi project named after the business project in Pulumi Cloud:

```
andre-2112/ecommerce/D1BRV40-network-dev
andre-2112/ecommerce/D1BRV40-security-dev
andre-2112/ecommerce/D1BRV40-database-dev
```

However, Pulumi validates the project name in CLI commands against the `name:` field in each stack directory's `Pulumi.yaml` file. Since all stack directories have hardcoded names (network, security, database-rds), this created a fundamental incompatibility:
- Commands needed to use deployment project name: `pulumi up --stack andre-2112/ecommerce/D1BRV40-network-dev`
- But Pulumi.yaml contained: `name: network` (stack type name)
- Pulumi rejected operations with "project name doesn't match Pulumi.yaml"

**The Solution:**

v4.5 introduces **Dynamic Pulumi.yaml Management** using a context manager pattern:

1. **Backup**: Before operations, backup original `Pulumi.yaml` with project-specific naming
2. **Generate**: Create temporary `Pulumi.yaml` with deployment project name
3. **Execute**: Run Pulumi operations with correct project context
4. **Restore**: Always restore original `Pulumi.yaml`, even on errors

**Implementation:**

New methods in `PulumiWrapper` class (`tools/core/cloud_core/pulumi/pulumi_wrapper.py`):

```python
@contextmanager
def deployment_context(self, stack_dir: Path, stack_name: str):
    """
    Context manager for deployment-specific Pulumi.yaml

    Usage:
        with pulumi_wrapper.deployment_context(stack_dir, "network"):
            # Pulumi operations here use deployment project name
            pulumi_wrapper.select_stack(...)
            pulumi_wrapper.up(...)
        # Original Pulumi.yaml automatically restored
    """
    backup_path = None
    try:
        backup_path = self._backup_pulumi_yaml(stack_dir)
        self._generate_pulumi_yaml(stack_dir, stack_name)
        yield
    finally:
        self._restore_pulumi_yaml(stack_dir, backup_path)
```

**Usage in Commands:**

All deployment and destruction commands now use the context manager:

```python
# deploy_stack_cmd.py, destroy_stack_cmd.py, deploy_cmd.py
with pulumi_wrapper.deployment_context(stack_dir, stack_name):
    # Deploy or destroy within context
    success, error = stack_ops.deploy_stack(
        deployment_id=deployment_id,
        stack_name=stack_name,
        environment=environment,
        stack_dir=stack_dir,
        config=config,
    )
# Pulumi.yaml automatically restored here
```

**Key Features:**

- **Retry Logic**: Handles Windows file locking with exponential backoff (1s, 2s)
- **Concurrent Safety**: Project-specific backup naming prevents conflicts: `Pulumi.yaml.backup.{project}`
- **Guaranteed Restoration**: Finally block ensures cleanup even on errors
- **Preserved Metadata**: Keeps original runtime and description from stack Pulumi.yaml
- **No Leftovers**: Cleans up stale backups from previous runs

**Impact:**

- ✅ Correct Pulumi Cloud organization structure by business project
- ✅ Proper stack grouping: all stacks for one deployment under one project
- ✅ Better organization and filtering in Pulumi Cloud dashboard
- ✅ Supports concurrent deployments (different projects don't conflict)
- ✅ Zero manual intervention required - fully automatic
- ✅ Backward compatible - original Pulumi.yaml files unchanged

**Before v4.5:**
```
andre-2112/network/D1BRV40-network-dev          # Wrong: scattered by stack type
andre-2112/security/D1BRV40-security-dev
andre-2112/database-rds/D1BRV40-database-dev
```

**After v4.5:**
```
andre-2112/ecommerce/D1BRV40-network-dev        # Correct: grouped by project
andre-2112/ecommerce/D1BRV40-security-dev
andre-2112/ecommerce/D1BRV40-database-dev
```

**Documentation:**

Complete implementation details in: `tools/docs/Addendum_Dynamic_Pulumi_YAML_Implementation.4.1.md`

### Template Changes in v4.5

**All Stacks Disabled by Default**

In v4.5, the default deployment template has been updated to disable all stacks by default:

```yaml
# tools/templates/default/default.yaml
stacks:
  network:
    enabled: false  # Changed from true
    layer: 1
    dependencies: []
```

**Impact:**
- Explicit opt-in model for stack deployment
- Prevents accidental deployment of unnecessary infrastructure
- Forces conscious decision-making about which stacks to enable
- Better for production safety and cost control
- Aligns with principle of least privilege

**Usage:**

Users must explicitly enable desired stacks when initializing deployments:

```bash
python -m cloud_cli.main init \
  --template default \
  --enable-stack network \
  --enable-stack security \
  --enable-stack storage
```

Or edit the generated deployment manifest to enable stacks:

```yaml
# deploy/D1BRV40-.../deployment-manifest.yaml
stacks:
  network:
    enabled: true  # Manually enable
```

### Carried Forward from v4.1

All features from v4.1 are preserved and enhanced:
- Python-based Core/CLI architecture
- Enhanced template system with structured parameters
- Auto-extraction system for parameter discovery
- Template-first validation for code consistency
- Pulumi native config format
- Simplified placeholder syntax
- Config subdirectory organization
- Updated stack naming convention

---

## What's New in v4.8

### Major Enhancements from Architecture 4.6

#### 1. Configuration Approach Change: --config-file Parameter

**The Problem:**

In v4.6, Pulumi configuration was set using `pulumi config set` commands:

```bash
# Old approach (v4.6)
pulumi config set network:vpcCidr "10.0.0.0/16"
pulumi config set network:availabilityZones "3"
pulumi config set aws:region "us-east-1"
pulumi up
```

This approach had several limitations:
- Configuration scattered across multiple commands
- Hard to audit what config values were actually set
- Difficult to reproduce deployments
- No clear config file to version control
- Error-prone manual config setting

**The Solution:**

v4.8 introduces **--config-file parameter** approach:

```bash
# New approach (v4.8)
pulumi up --config-file ../../deploy/D1BRV40/config/network.dev.yaml
```

**Benefits:**

- **Auditable**: All config in one file, easy to review
- **Reproducible**: Config file can be version controlled
- **Maintainable**: Single source of truth for configuration
- **Error-free**: Generated automatically from deployment manifest
- **Transparent**: Clear what config values are being used

**Implementation:**

Config files are generated by `ConfigGenerator` and stored in deployment directories:

```
deploy/D1BRV40-CompanyA-ecommerce/config/
├── network.dev.yaml
├── network.stage.yaml
├── network.prod.yaml
├── security.dev.yaml
└── ...
```

Pulumi is invoked with `--config-file` parameter pointing to the appropriate config file.

**Impact:**

- More maintainable and auditable configuration
- Easier debugging (just inspect the config file)
- Better reproducibility
- Simplified deployment process
- Clearer separation of concerns

#### 2. Enhanced CLI Commands with Rich Interactive Modes

**cloud list Command Improvements:**

```bash
# Default: Show only active deployments (filters out destroyed)
cloud list

# Show all deployments including destroyed ones
cloud list --all

# Interactive mode with actions menu
cloud list --rich
```

**cloud list --rich** provides an interactive menu:
- Navigate through deployments
- View status for each deployment
- View configuration
- Deploy directly from list
- Destroy deployments
- Filter by state (initialized, deployed, partial, failed, destroyed)

**cloud config Command Enhancement:**

```bash
# Enhanced UI with environment selection
cloud config --rich

# Interactive features:
# - Browse deployment manifest
# - Select environment (dev/stage/prod)
# - View stack configurations
# - Edit configuration values
# - Validate changes before saving
```

**cloud status Command:**

```bash
# Check deployment status
cloud status D1BRV40

# Potentially support watch mode (periodic refresh)
cloud status D1BRV40 --watch
```

**Impact:**

- Improved user experience with interactive modes
- Faster navigation and operations
- Less typing for common workflows
- Better visibility into deployment state
- More discoverable features

#### 3. Improved Deployment Lifecycle and State Management

**Deployment State Tracking:**

Deployments now have explicit state tracking:

- **initialized**: Deployment created but not yet deployed
- **deployed**: Successfully deployed (all stacks up)
- **partial**: Partially deployed (some stacks failed)
- **failed**: Deployment failed
- **destroyed**: Resources destroyed but history preserved

**Preserved Destroyed Deployment History:**

When a deployment is destroyed:
- Full deployment history is preserved
- Logs remain available
- Manifest is retained
- State marked as "destroyed"
- Not shown in default `cloud list` output
- Can be viewed with `cloud list --all`

**Benefits:**

- Complete audit trail even after destruction
- Can reference old deployments for troubleshooting
- Clear distinction between active and destroyed deployments
- Easier cleanup of deployment list
- Better compliance and auditing

#### 4. Enhanced Error Handling and User Guidance

**Comprehensive AWS Error Detection:**

The platform now detects specific AWS errors and provides user-friendly messages:

```bash
# Example: Service limit error
Error: AWS service limit reached for VPCs in us-east-1
Current limit: 5 VPCs
Your request: 1 additional VPC

Remediation:
1. Delete unused VPCs in this region
2. Request a service limit increase:
   aws service-quotas request-service-quota-increase \
     --service-code vpc \
     --quota-code L-F678F1CE \
     --desired-value 10 \
     --region us-east-1
3. Consider using a different region
```

**Error Logging:**

All errors logged to deployment directory:

```
deploy/D1BRV40-CompanyA-ecommerce/logs/
├── D1BRV40-network-dev-20251031-140000-error.log
├── D1BRV40-security-dev-20251031-141500-error.log
└── ...
```

**Impact:**

- Faster troubleshooting with specific error messages
- Clear remediation steps for common errors
- Complete error history in logs
- Better user experience
- Reduced support burden

#### 5. cloud destroy Command Improvements

**Proper State Management:**

```bash
# Destroy deployment but preserve history
cloud destroy D1BRV40 --environment dev

# State transitions:
# deployed -> destroying -> destroyed

# Deployment remains visible with --all flag
cloud list --all
```

**Features:**

- Proper state transitions (deployed → destroying → destroyed)
- Preserved deployment history and logs
- Manifest retained for reference
- Can review what was deployed
- Safe cleanup of resources
- Clear audit trail

**Impact:**

- Better lifecycle management
- Complete audit trail
- Easier troubleshooting of destroyed deployments
- Compliance-friendly record keeping

### Carried Forward from v4.6

All features from v4.6 are preserved:
- Dynamic Pulumi.yaml management with context manager pattern
- Deployment-specific project naming in Pulumi Cloud
- All stacks disabled by default in deployment templates
- Pulumi.yaml backup and restore mechanism
- Support for concurrent deployments
- Enhanced PulumiWrapper with deployment_context() method
- Composite project naming for complete deployment isolation

---

## Architecture Goals

### Primary Goals for v4.1

**1. Operational Scalability**
- Support dozens of organizations with hundreds of projects each
- Handle thousands of simultaneous deployments
- Minimize disk space usage (shared stack code, deployment-specific configs)
- Fast deployment initialization (<30 seconds)
- Intelligent partial re-deployment for rapid updates

**2. Configuration Management Excellence**
- Single source of truth for all deployment configuration
- Clear separation between stack code and deployment config
- Template-driven consistency across all deployments
- Runtime resolution of dynamic values
- Stack dependencies in templates (single source)
- Enhanced templates with structured parameters (v4.0+)

**3. Developer Productivity**
- Intuitive Python CLI with comprehensive commands using Typer
- Auto-extraction for reducing manual template maintenance (v4.0+)
- Template-first validation for catching errors early (v4.0+)
- Interactive modes for common workflows
- Clear error messages with actionable guidance
- Real-time deployment progress monitoring
- Multiple file support for better code organization

**4. Operational Reliability**
- Automated validation at every step
- Template-first validation preventing drift (v4.0+)
- Rollback capabilities for failed deployments
- State consistency guarantees
- Complete audit trail
- Smart skip logic for efficient deployments

**5. Enterprise Readiness**
- Role-based access control via REST API
- Authentication and authorization
- Compliance auditing support
- Multi-tenant isolation
- Real-time monitoring and alerting
- Comprehensive test coverage (393+ core tests, 38+ CLI tests)

**6. Maintainability and Extensibility (v4.1)**
- Core/CLI architecture split for better organization
- Reusable Python business logic library
- Modular design with clear responsibilities
- Type hints for better IDE support and error prevention
- Comprehensive test suites

### Non-Goals for v4.1

Deferred to future versions (v5.0+):
- Advanced compliance frameworks (SOC2, ISO27001, HIPAA)
- Multi-region orchestration with global state replication
- Advanced cost optimization engines
- Complex approval workflows
- Self-healing and automated remediation
- Multi-cloud support (Azure, GCP)

---

## Core Concepts

### 1. Stacks

**Definition:** A stack is a self-contained Pulumi program that deploys a specific set of related AWS resources.

**Characteristics:**
- Written in TypeScript using Pulumi SDK
- Stored in `./cloud/stacks/<stack-name>/src/`
- Contains minimal `Pulumi.yaml` (name, runtime, description)
- Declares dependencies on other stacks (in templates)
- Declares inputs and outputs (in enhanced templates - v4.0+)
- Exposes outputs for cross-stack references
- Version controlled independently
- Supports multiple TypeScript files with explicit imports

**Example Stacks:**
- **network**: VPC, subnets, NAT gateways, VPC endpoints
- **security**: Security groups, IAM roles, KMS keys
- **database-rds**: RDS instances, parameter groups, subnet groups
- **compute-ec2**: EC2 instances, auto-scaling groups, load balancers

**Stack Lifecycle:**
1. **Development**: Create stack code in `./cloud/stacks/<stack-name>/`
2. **Registration**: Register stack with template system (optionally use auto-extraction - v4.0+)
3. **Validation**: Validate stack code against template (template-first validation - v4.0+)
4. **Template Integration**: Stack becomes available in deployment templates
5. **Deployment**: Stack deployed as part of deployment manifest
6. **Maintenance**: Updates applied to stack code (re-validate after changes - v4.0+)
7. **Decommission**: Stack removed from templates and deployments

### 2. Deployments

**Definition:** A deployment is an instance of infrastructure created by executing one or more stacks with specific configuration.

**Characteristics:**
- Unique deployment ID (format: `D<base36-timestamp>`, example: `D1BRV40`)
- Directory: `./cloud/deploy/D1BRV40-<org>-<project>/`
- Contains deployment manifest and configuration files (in `config/` subdirectory - v4.1)
- Supports multiple environments (dev, stage, prod)
- Independent state in Pulumi Cloud
- Complete audit trail in logs

**Deployment Structure (v4.1):**
```
./cloud/deploy/D1BRV40-CompanyA-ecommerce/
├── Deployment_Manifest.yaml          # Stack selection and configuration
├── config/                            # Config subdirectory (v4.1)
│   ├── network.dev.yaml               # Pulumi native format (v4.1)
│   ├── network.stage.yaml
│   ├── network.prod.yaml
│   ├── security.dev.yaml
│   └── ... (all stacks × all environments)
└── logs/
    ├── init.log                       # Initialization log
    ├── deploy-dev-20251029.log        # Dev deployment log
    └── deploy-stage-20251030.log      # Stage deployment log
```

**Deployment Lifecycle:**
1. **Initialize**: `python -m cloud_cli.main init D1BRV40 --org CompanyA --project ecommerce`
2. **Configure**: (Optional) Edit manifest for customization
3. **Validate**: `python -m cloud_cli.main validate D1BRV40` (includes template-first validation - v4.0+)
4. **Deploy**: `python -m cloud_cli.main deploy D1BRV40 --environment dev`
5. **Promote**: `python -m cloud_cli.main enable-environment D1BRV40 stage`
6. **Monitor**: `python -m cloud_cli.main status D1BRV40 --all-environments`
7. **Update**: `python -m cloud_cli.main deploy D1BRV40 --environment dev` (apply changes)
8. **Destroy**: `python -m cloud_cli.main destroy D1BRV40 --environment dev`

### 3. Templates

**Definition:** A template is a pre-configured deployment manifest pattern used to initialize new deployments.

**Types:**

**Default Template** - Full platform with all 16 stacks
- All foundation, security, data, container, service, and compute stacks
- All three environments (dev, stage, prod)
- Standard configuration for typical enterprise deployment

**Minimal Template** - Basic infrastructure only
- Foundation stacks: dns, network, security
- Dev environment only
- For testing, prototyping, or minimal deployments

**Microservices Template** - Container-focused platform
- Foundation: network, security, secrets, authentication
- Container layer: ECS, ECR, container images
- Service layer: API Gateway, load balancers
- For containerized microservices applications

**Data Platform Template** - Data processing focus
- Foundation: network, security, storage
- Data layer: RDS, S3, data lakes
- Processing layer: Lambda, batch processing
- For data analytics and processing workloads

**Template Location (v4.1):**
```
./cloud/tools/templates/
├── default/                         # Manifest templates
│   ├── default.yaml
│   ├── minimal.yaml
│   ├── microservices.yaml
│   └── data-platform.yaml
├── custom/                          # Organization-specific manifest templates
│   └── <org>-standard.yaml
└── config/                          # Stack definition templates (enhanced - v4.0+)
    ├── network.yaml                 # With parameters.inputs and parameters.outputs
    ├── dns.yaml
    ├── security.yaml
    └── ... (all 16 stacks)
```

See Platform Code Addendum, Section 3 for complete template examples.

### 4. Environments

**Definition:** An environment is a logical separation of infrastructure (dev, stage, prod) within a single deployment.

**Characteristics:**
- All environments defined in single deployment manifest
- Per-environment stack configuration
- Different AWS accounts supported per environment
- Different regions supported per environment
- Independent state per environment in Pulumi Cloud

**Promotion Workflow:**
```
Dev (enabled: true) → Test → Enable Stage
  ↓
Stage (enabled: true) → Test → Enable Prod
  ↓
Prod (enabled: true) → Monitor
```

See Platform Code Addendum, Section 4 for environment configuration examples.

### 5. Configuration Tiers

**Three-Tier Configuration Resolution:**

**Tier 1: Template Defaults** (Static)
- Defined in `./cloud/tools/templates/config/<stack>.yaml`
- Includes enhanced parameter specifications (v4.0+)
- Provides sensible defaults for all parameters
- Same across all deployments using same template
- Example: `vpcCidr: type: string, default: "10.0.0.0/16"` for dev environment

**Tier 2: Manifest Overrides** (User-Specified)
- Defined in `./cloud/deploy/D1BRV40-*/Deployment_Manifest.yaml`
- User customizations overriding template defaults
- Deployment-specific values
- Example: `vpcCidr: "10.50.0.0/16"` (custom CIDR range)

**Tier 3: Runtime Resolution** (Dynamic)
- Resolved during deployment execution
- Cross-stack references: `${network.vpcId}` or `{{network.vpcId}}` (simplified syntax - v4.1)
- AWS queries: `${aws.latestAmiId.amazonLinux2}`
- Calculations: `${calculate.subnets.10.0.0.0/16.24.3}`

**Resolution Flow:**
```
Enhanced Template Default (with type, validation, default value)
  ↓
Manifest Override (10.50.0.0/16) ← User customization
  ↓
Runtime Resolution (no runtime placeholder) ← Final value: 10.50.0.0/16
```

### 6. Dependencies

**Definition:** Dependencies define the order in which stacks must be deployed based on resource relationships.

**Dependency Types:**

**Template-Declared Dependencies** - Single source of truth
- Declared in `./cloud/tools/templates/config/<stack>.yaml`
- Automatically included in manifests
- Validated during initialization and deployment

**Cross-Stack References** - Implicit via runtime placeholders
- Derived from `${stack.output}` usage (simplified syntax - v4.1)
- Automatically detected and validated

**Dependency Resolution:**
```
┌──────────────────────────────────────────────────┐
│    Topological Sort Algorithm (v4.1)             │
├──────────────────────────────────────────────────┤
│                                                   │
│  1. Load enhanced templates                       │
│  2. Build dependency graph from templates         │
│  3. Detect cycles (error if found)                │
│  4. Identify stacks with no dependencies          │
│  5. Remove from graph and add to execution plan  │
│  6. Repeat steps 4-5 until all stacks processed  │
│  7. Result: Ordered list of execution layers     │
│                                                   │
│  Implementation: DependencyResolver (cloud_core)  │
│                                                   │
└──────────────────────────────────────────────────┘
```

**Execution Order Example:**
```
Layer 1 (Parallel): dns, network
Layer 2 (Parallel): security (depends on network)
Layer 3 (Parallel): secrets (depends on security), storage (depends on network, security)
Layer 4 (Parallel): database-rds (depends on network, security, secrets), authentication
Layer 5 (Sequential): compute-ec2, compute-lambda, services-ecs
Layer 6 (Final): monitoring (depends on all layers)
```

See Platform Code Addendum, Section 6 for dependency declaration examples.

---

## Core/CLI Architecture

### Architecture Overview (v4.1)

The v4.1 platform introduces a **two-tier architecture** separating business logic from user interface:

**Tier 1: Core Library (`cloud_core`)**
- Python package containing all business logic
- Located at `tools/core/cloud_core/`
- No CLI dependencies - pure business logic
- Reusable across multiple interfaces (CLI, REST API, etc.)
- Comprehensive test coverage (393+ tests)

**Tier 2: CLI Interface (`cloud_cli`)**
- Python package providing command-line interface
- Located at `tools/cli/cloud_cli/`
- Uses Typer framework for CLI implementation
- Thin wrapper around core library
- CLI-specific test coverage (38+ tests)

### Core Library Modules

**deployment/** - Deployment Management
- `config_generator.py` - Generate Pulumi config files from manifests (Pulumi native format)
- `deployment_manager.py` - Manage deployment lifecycle
- `state_manager.py` - Handle Pulumi state operations

**orchestrator/** - Orchestration Engine
- `dependency_resolver.py` - Analyze and resolve stack dependencies
- `layer_calculator.py` - Calculate execution layers from dependencies
- `execution_engine.py` - Execute stacks in correct order with parallelization

**runtime/** - Runtime Resolution
- `placeholder_resolver.py` - Resolve runtime placeholders (${stack.output})
- `stack_reference_resolver.py` - Handle cross-stack references

**templates/** - Template System
- `stack_template_manager.py` - Load and manage enhanced templates
- `manifest_generator.py` - Generate manifests from templates

**validation/** - Validation System (v4.0+)
- `stack_code_validator.py` - Template-first validation
- `manifest_validator.py` - Manifest schema validation

**pulumi/** - Pulumi Integration
- `pulumi_wrapper.py` - Wrap Pulumi CLI commands
- Handles stack creation, deployment, destruction

**utils/** - Utilities
- `logging.py` - Structured logging infrastructure
- `file_utils.py` - File operations
- `yaml_utils.py` - YAML parsing and generation

### CLI Modules

**commands/** - CLI Commands
- `init.py` - Initialize deployment command
- `deploy.py` - Deploy stacks command
- `validate.py` - Validation commands
- `register_stack.py` - Stack registration command
- `enable_environment.py` - Environment management
- ... (25+ command implementations)

**parser/** - Auto-Extraction System (v4.0+)
- `parameter_extractor.py` - Extract parameters from TypeScript code
  - Analyzes `Config.require()` calls for inputs
  - Detects parameter types (string, number, boolean)
  - Identifies required vs optional parameters
- `typescript_parser.py` - Parse TypeScript for exports
  - Extracts `export const` statements for outputs
  - Infers output types from Pulumi resource properties

**main.py** - CLI Entry Point
- Typer application setup
- Command registration
- Global error handling
- Logging configuration

### Design Principles

**1. Separation of Concerns**
```
CLI Layer (cloud_cli)
  ├─ User interaction
  ├─ Command parsing
  ├─ Output formatting
  └─ Calls Core Library
         │
         ▼
Core Library (cloud_core)
  ├─ Business logic
  ├─ No UI dependencies
  ├─ Pure Python functions
  └─ Fully testable
```

**2. Dependency Flow**
```
CLI depends on Core ✓
Core does NOT depend on CLI ✓
Core is independently usable ✓
```

**3. Testing Strategy**
```
Core Library Tests (393+)
  ├─ Unit tests for each module
  ├─ Integration tests for workflows
  └─ No UI mocking required

CLI Tests (38+)
  ├─ Command execution tests
  ├─ Mock core library calls
  └─ Output formatting tests
```

### Usage Example

**Using Core Library Directly (Python):**
```python
from cloud_core.deployment import ConfigGenerator
from cloud_core.templates import StackTemplateManager
from pathlib import Path

# Load template
template_mgr = StackTemplateManager()
template = template_mgr.load_template('network')

# Generate config
config_gen = ConfigGenerator(Path('./deploy/D1BRV40'))
config_gen.generate_stack_config('network', 'dev', template)
```

**Using CLI (Command Line):**
```bash
# Same operation via CLI
python -m cloud_cli.main init D1BRV40 --template default --org CompanyA --project ecommerce

# CLI internally calls:
# - StackTemplateManager.load_template()
# - ConfigGenerator.generate_stack_config()
```

### Benefits of Core/CLI Split

**Reusability**
- Core library usable by REST API (future)
- Core library usable by web UI (future)
- Core library usable in automated scripts

**Testability**
- Core logic tested independently
- No CLI mocking in core tests
- Clear separation of concerns

**Maintainability**
- Changes to UI don't affect business logic
- Business logic changes don't break UI
- Clear module boundaries

**Performance**
- Core library can be imported without CLI overhead
- REST API can use core library directly (no subprocess calls)

---

## Directory Structure

### Complete Platform Directory Layout (v4.1)

```
./cloud/                                    # Cloud Platform Root
├── .claude/                                # Claude AI session management
│   ├── CLAUDE.md                           # Memory bank configuration
│   └── memory/                             # Session documents
│
├── tools/                                  # Platform Tools
│   ├── docs/                               # Architecture Documentation
│   │   ├── Multi_Stack_Architecture.4.1.md     ← THIS DOCUMENT
│   │   ├── Directory_Structure_Diagram.4.1.md  # v4.1 directory reference
│   │   ├── Deployment_Manifest_Specification.4.1.md  # v4.1 manifest spec
│   │   ├── Complete_Stack_Management_Guide_v4.md     # v4.0 authoritative
│   │   ├── Stack_Parameters_and_Registration_Guide_v4.md  # v4.0 authoritative
│   │   ├── Complete_Guide_Templates_Stacks_Config_and_Registration_v4.md  # v4.0 authoritative
│   │   ├── CLI_Commands_Reference.3.1.md
│   │   ├── REST_API_Documentation.3.1.md
│   │   ├── Addendum_Platform_Code.3.1.md
│   │   └── ... (additional documents)
│   │
│   ├── core/                               # Core Business Logic Library (Python - v4.1)
│   │   ├── setup.py                        # Package setup
│   │   ├── cloud_core/                     # Core package
│   │   │   ├── __init__.py
│   │   │   ├── deployment/                 # Deployment management
│   │   │   │   ├── __init__.py
│   │   │   │   ├── config_generator.py     # Generate Pulumi configs
│   │   │   │   ├── deployment_manager.py   # Deployment lifecycle
│   │   │   │   └── state_manager.py        # State operations
│   │   │   │
│   │   │   ├── orchestrator/               # Orchestration engine
│   │   │   │   ├── __init__.py
│   │   │   │   ├── dependency_resolver.py  # Dependency analysis
│   │   │   │   ├── layer_calculator.py     # Layer-based execution
│   │   │   │   └── execution_engine.py     # Stack execution
│   │   │   │
│   │   │   ├── runtime/                    # Runtime resolution
│   │   │   │   ├── __init__.py
│   │   │   │   ├── placeholder_resolver.py # Placeholder handling
│   │   │   │   └── stack_reference_resolver.py  # Cross-stack refs
│   │   │   │
│   │   │   ├── templates/                  # Template system
│   │   │   │   ├── __init__.py
│   │   │   │   ├── stack_template_manager.py  # Template loading
│   │   │   │   └── manifest_generator.py   # Manifest generation
│   │   │   │
│   │   │   ├── validation/                 # Validation system (v4.0+)
│   │   │   │   ├── __init__.py
│   │   │   │   ├── stack_code_validator.py # Template-first validation
│   │   │   │   └── manifest_validator.py   # Manifest validation
│   │   │   │
│   │   │   ├── pulumi/                     # Pulumi integration
│   │   │   │   ├── __init__.py
│   │   │   │   └── pulumi_wrapper.py       # Pulumi CLI wrapper
│   │   │   │
│   │   │   └── utils/                      # Utilities
│   │   │       ├── __init__.py
│   │   │       ├── logging.py              # Logging infrastructure
│   │   │       ├── file_utils.py           # File operations
│   │   │       └── yaml_utils.py           # YAML parsing
│   │   │
│   │   └── tests/                          # Core library tests (393+ tests)
│   │       ├── test_deployment/
│   │       ├── test_orchestrator/
│   │       ├── test_runtime/
│   │       ├── test_templates/
│   │       ├── test_validation/
│   │       └── test_pulumi/
│   │
│   ├── cli/                                # CLI Tool (Python - v4.1)
│   │   ├── setup.py                        # Package setup
│   │   ├── cloud_cli/                      # CLI package
│   │   │   ├── __init__.py
│   │   │   ├── main.py                     # Typer CLI entry point
│   │   │   │
│   │   │   ├── commands/                   # Command implementations
│   │   │   │   ├── __init__.py
│   │   │   │   ├── init.py                 # Init command
│   │   │   │   ├── deploy.py               # Deploy commands
│   │   │   │   ├── validate.py             # Validation commands
│   │   │   │   ├── register_stack.py       # Stack registration
│   │   │   │   ├── enable_environment.py   # Environment management
│   │   │   │   └── ... (25+ commands)
│   │   │   │
│   │   │   └── parser/                     # Auto-extraction system (v4.0+)
│   │   │       ├── __init__.py
│   │   │       ├── parameter_extractor.py  # Extract inputs from code
│   │   │       └── typescript_parser.py    # Parse TypeScript exports
│   │   │
│   │   └── tests/                          # CLI tests (38+ tests)
│   │       ├── test_commands/
│   │       └── test_parser/
│   │
│   ├── templates/                          # Deployment Templates
│   │   │
│   │   ├── docs/                           # Stack Markdown Templates
│   │   │   ├── Stack_Prompt_Main.md.template
│   │   │   ├── Stack_Prompt_Extra.md.template
│   │   │   ├── Stack_Definitions.md.template
│   │   │   ├── Stack_Resources.md.template
│   │   │   ├── Stack_History_Errors.md.template
│   │   │   ├── Stack_History_Fixes.md.template
│   │   │   └── Stack_History.md.template
│   │   │
│   │   ├── stack/                          # Stack Pulumi Templates
│   │   │   ├── index.ts.template           # Main entry point template
│   │   │   ├── src/
│   │   │   │   ├── component-example.ts.template  # Optional components
│   │   │   │   └── outputs.ts.template     # Exported outputs template
│   │   │   ├── Pulumi.yaml.template        # Stack metadata template
│   │   │   ├── package.json.template       # NPM package template
│   │   │   └── tsconfig.json.template      # TypeScript config template
│   │   │
│   │   ├── config/                         # Stack Definitions (enhanced - v4.0+)
│   │   │   ├── network.yaml                # Network stack template
│   │   │   │   # Enhanced with parameters.inputs and parameters.outputs
│   │   │   ├── dns.yaml                    # DNS stack template
│   │   │   ├── security.yaml               # Security stack template
│   │   │   ├── secrets.yaml                # Secrets stack template
│   │   │   ├── authentication.yaml         # Authentication stack template
│   │   │   ├── storage.yaml                # Storage stack template
│   │   │   ├── database-rds.yaml           # Database stack template
│   │   │   ├── containers-images.yaml      # Container images stack template
│   │   │   ├── containers-apps.yaml        # Container apps stack template
│   │   │   ├── services-ecr.yaml           # ECR service stack template
│   │   │   ├── services-ecs.yaml           # ECS service stack template
│   │   │   ├── services-eks.yaml           # EKS service stack template
│   │   │   ├── services-api.yaml           # API Gateway stack template
│   │   │   ├── compute-ec2.yaml            # EC2 stack template
│   │   │   ├── compute-lambda.yaml         # Lambda stack template
│   │   │   └── monitoring.yaml             # Monitoring stack template
│   │   │
│   │   ├── default/                        # Manifest Templates
│   │   │   ├── default.yaml                # Full platform template
│   │   │   ├── minimal.yaml                # Minimal infrastructure
│   │   │   ├── microservices.yaml          # Container-focused
│   │   │   └── data-platform.yaml          # Data processing focus
│   │   │
│   │   └── custom/                         # Organization-specific Custom Templates
│   │
│   └── api/                                # REST API Source Code (Future)
│       ├── src/
│       │   ├── index.ts                    # API entry point
│       │   ├── routes/                     # API route handlers
│       │   ├── auth/                       # Authentication logic
│       │   ├── cli-wrapper/                # CLI integration
│       │   ├── websocket/                  # Real-time updates
│       │   └── utils/                      # API utilities
│       ├── tests/
│       ├── package.json
│       └── openapi.yaml
│
├── stacks/                                 # Stack Definitions (TypeScript)
│   ├── shared/                             # Shared utilities
│   │   ├── index.ts                        # Re-export all
│   │   ├── state.ts                        # State helpers
│   │   ├── types.ts                        # Type definitions
│   │   └── utils.ts                        # Common utilities
│   │
│   ├── dns/                                # DNS Stack
│   │   ├── index.ts                        # Main entry point (AT ROOT)
│   │   ├── src/                            # Optional component files
│   │   │   ├── route53.ts                  # Route53 resources
│   │   │   └── acm.ts                      # Certificate Manager
│   │   ├── docs/                           # Stack documentation
│   │   ├── Pulumi.yaml                     # Minimal config (at root)
│   │   ├── package.json
│   │   └── tsconfig.json
│   │
│   ├── network/                            # Network Stack
│   │   ├── index.ts                        # Main entry point (AT ROOT)
│   │   ├── src/                            # Optional component files
│   │   │   ├── vpc.ts                      # VPC resources
│   │   │   ├── subnets.ts                  # Subnet resources
│   │   │   ├── routing.ts                  # Route tables
│   │   │   ├── nat-gateway.ts              # NAT gateways
│   │   │   └── endpoints.ts                # VPC endpoints
│   │   ├── docs/
│   │   ├── Pulumi.yaml                     # Minimal config (at root)
│   │   ├── package.json
│   │   └── tsconfig.json
│   │
│   ├── security/                           # Security Stack
│   │   ├── index.ts                        # Main entry point (AT ROOT)
│   │   ├── src/                            # Optional component files
│   │   ├── docs/
│   │   ├── Pulumi.yaml
│   │   ├── package.json
│   │   └── tsconfig.json
│   │
│   ├── secrets/                            # Secrets Stack
│   │   ├── index.ts
│   │   ├── src/
│   │   ├── docs/
│   │   ├── Pulumi.yaml
│   │   ├── package.json
│   │   └── tsconfig.json
│   │
│   ├── authentication/                     # Authentication Stack
│   │   ├── index.ts
│   │   ├── src/
│   │   ├── docs/
│   │   ├── Pulumi.yaml
│   │   ├── package.json
│   │   └── tsconfig.json
│   │
│   ├── storage/                            # Storage Stack
│   │   ├── index.ts
│   │   ├── src/
│   │   ├── docs/
│   │   ├── Pulumi.yaml
│   │   ├── package.json
│   │   └── tsconfig.json
│   │
│   ├── database-rds/                       # Database Stack
│   │   ├── index.ts
│   │   ├── src/
│   │   ├── docs/
│   │   ├── Pulumi.yaml
│   │   ├── package.json
│   │   └── tsconfig.json
│   ├── containers-images/                  # Container Images
│   │   ├── index.ts
│   │   ├── src/
│   │   ├── docs/
│   │   ├── Pulumi.yaml
│   │   ├── package.json
│   │   └── tsconfig.json
│   │
│   ├── containers-apps/                    # Container Apps
│   │   ├── index.ts
│   │   ├── src/
│   │   ├── docs/
│   │   ├── Pulumi.yaml
│   │   ├── package.json
│   │   └── tsconfig.json
│   │
│   ├── services-ecr/                       # ECR Stack
│   │   ├── index.ts
│   │   ├── src/
│   │   ├── docs/
│   │   ├── Pulumi.yaml
│   │   ├── package.json
│   │   └── tsconfig.json
│   │
│   ├── services-ecs/                       # ECS Stack
│   │   ├── index.ts
│   │   ├── src/
│   │   ├── docs/
│   │   ├── Pulumi.yaml
│   │   ├── package.json
│   │   └── tsconfig.json
│   │
│   ├── services-eks/                       # EKS Stack
│   │   ├── index.ts
│   │   ├── src/
│   │   ├── docs/
│   │   ├── Pulumi.yaml
│   │   ├── package.json
│   │   └── tsconfig.json
│   │
│   ├── services-api/                       # API Gateway Stack
│   │   ├── index.ts
│   │   ├── src/
│   │   ├── docs/
│   │   ├── Pulumi.yaml
│   │   ├── package.json
│   │   └── tsconfig.json
│   │
│   ├── compute-ec2/                        # EC2 Stack
│   │   ├── index.ts
│   │   ├── src/
│   │   ├── docs/
│   │   ├── Pulumi.yaml
│   │   ├── package.json
│   │   └── tsconfig.json
│   │
│   ├── compute-lambda/                     # Lambda Stack
│   │   ├── index.ts
│   │   ├── src/
│   │   ├── docs/
│   │   ├── Pulumi.yaml
│   │   ├── package.json
│   │   └── tsconfig.json
│   │
│   └── monitoring/                         # Monitoring Stack
│       ├── index.ts
│       ├── src/
│       ├── docs/
│       ├── Pulumi.yaml
│       ├── package.json
│       └── tsconfig.json
│
└── deploy/                                 # Active Deployments
    ├── D1BRV40-CompanyA-ecommerce/         # Deployment Example 1
    │   ├── Deployment_Manifest.yaml        # Deployment config
    │   ├── config/                         # Config subdirectory (v4.1)
    │   │   ├── network.dev.yaml            # Pulumi native format (v4.1)
    │   │   ├── network.stage.yaml
    │   │   ├── network.prod.yaml
    │   │   └── ... (all stacks × environments)
    │   └── logs/
    │       ├── init.log
    │       ├── deploy-dev-20251029.log
    │       └── deploy-stage-20251030.log
    │
    ├── D1BRV45-CompanyB-mobile/            # Deployment Example 2
    └── D1BRV50-CompanyA-analytics/         # Deployment Example 3
```

### Key Directory Changes from Architecture 3.1

**Path Changes:**
```
Old (3.1)                                   New (4.1)
─────────────────────────────────────────────────────────────────
./cloud/tools/cli/src/                  →   ./cloud/tools/cli/cloud_cli/
  (TypeScript implementation)                 (Python implementation with Typer)

N/A                                     →   ./cloud/tools/core/cloud_core/
                                              (New: Core business logic library)

./cloud/deploy/D1BRV40/*.yaml          →   ./cloud/deploy/D1BRV40/config/*.yaml
                                              (Config files in subdirectory)
```

**New in v4.1:**
- `tools/core/cloud_core/` - Core business logic library (Python)
- `tools/cli/cloud_cli/parser/` - Auto-extraction system
- `tools/core/cloud_core/validation/` - Template-first validation
- `deploy/<id>/config/` - Dedicated config subdirectory

**Updated in v4.1:**
- `tools/cli/` - Now Python-based with Typer (was TypeScript)
- `tools/templates/config/` - Now with enhanced parameters (inputs/outputs)
- `deploy/<id>/config/*.yaml` - Now Pulumi native format

---

## Stack Management

### Stack Anatomy

Each stack consists of:

1. **Pulumi.yaml** (Minimal Configuration)
2. **index.ts** (Main Program)
3. **Resource Modules** (Organized by AWS service - multiple TypeScript files)
4. **package.json** (NPM Workspace Member)
5. **tsconfig.json** (TypeScript Configuration)

### Minimal Pulumi.yaml Specification

**Purpose:** Identify stack and runtime only. All deployment-specific configuration lives in deployment directories.

**Required Attributes:**
- `name`: Stack identifier (matches directory name)
- `runtime`: Programming language (nodejs)
- `description`: Human-readable description

**Prohibited Attributes:**
- No `config` section (configuration in deployment directories)
- No `main` attribute (defaults to index.ts)
- No deployment-specific values

See Platform Code Addendum, Section 7.1 for Pulumi.yaml examples.

### Stack Code Structure with Multiple Files

**Main Program (index.ts):**
- Imports resource modules
- Coordinates resource creation
- Exports outputs
- See Platform Code Addendum, Section 7.2

**Resource Modules (e.g., vpc.ts, subnets.ts):**
- Focused on specific AWS services
- Export creation functions
- Clear separation of concerns
- See Platform Code Addendum, Section 7.3

**Explicit Imports:**
All imports between files must be explicit. The main index.ts imports from resource modules using standard ES6 import syntax.

### Stack Registration (v4.1 with Auto-Extraction)

**Purpose:** Register a new stack with the template system, making it available for future deployments.

**Command (Basic Registration):**
```bash
python -m cloud_cli.main register-stack <stack-name> \
  --description "Stack description" \
  --defaults-file ./stack-defaults.yaml \
  --dependencies network,security
```

**Command (With Auto-Extraction - v4.0+):**
```bash
python -m cloud_cli.main register-stack <stack-name> \
  --auto-extract \
  --defaults-file ./stack-defaults.yaml
```

**Auto-Extraction Process (v4.0+):**
1. Verify stack directory exists in `./cloud/stacks/<stack-name>/src/`
2. Parse `Pulumi.yaml` to extract stack metadata
3. Run `ParameterExtractor` on TypeScript files
   - Analyze `Config.require()` calls to extract inputs
   - Analyze `Config.requireNumber()` calls to extract number inputs
   - Analyze `Config.get()` calls to extract optional inputs
   - Infer types from method names
4. Run `TypeScriptParser` on TypeScript files
   - Extract `export const` statements for outputs
   - Infer types from Pulumi resource properties
5. Generate enhanced template with `parameters.inputs` and `parameters.outputs`
6. Create stack template in `./cloud/tools/templates/config/<stack-name>.yaml`
7. Add dependencies if specified
8. Add stack to registry for discovery

**Manual Registration Process:**
1. Verify stack directory exists
2. Parse `Pulumi.yaml` to extract stack metadata
3. Load defaults from defaults file or interactive prompts
4. Create basic template in `./cloud/tools/templates/config/<stack-name>.yaml`
5. Add dependencies to stack template
6. Add stack to registry for discovery

See Platform Code Addendum, Section 7.4 for stack template structure with dependencies.

### Stack Dependencies

**Template-Declared Dependencies (Single Source of Truth):**
Dependencies are declared in stack templates and automatically propagated to manifests. See Platform Code Addendum, Section 7.5.

**Implicit Dependencies:**
Derived from runtime placeholders (`${stack.output}` - v4.1). See Platform Code Addendum, Section 7.6.

**Dependency Validation:**
- Detect circular dependencies (error)
- Verify all dependencies are enabled in manifest
- Ensure dependency stacks exist in stack directory
- Validate dependency chains from templates
- Template-first validation ensures outputs exist (v4.0+)

### Stack Outputs

**Purpose:** Expose values for cross-stack references and monitoring.

**Export Pattern:** See Platform Code Addendum, Section 7.7

**Query Pattern (from other stacks via DependencyResolver):** See Platform Code Addendum, Section 7.8

**Runtime Placeholder Pattern (v4.1):**
```yaml
# Simplified placeholder syntax
subnets: "${network.privateSubnetIds}"
# or
subnets: "{{network.privateSubnetIds}}"
```

See Platform Code Addendum, Section 7.9 for implementation details.

---

## Template System

### Template Architecture

```
┌──────────────────────────────────────────────────────────────┐
│               Template System (v4.1)                          │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  Manifest Templates                Enhanced Stack Templates  │
│  ┌──────────────┐                  ┌──────────────┐          │
│  │ default.yaml │                  │network.yaml  │          │
│  │ minimal.yaml │──────combines───▶│ +parameters  │          │
│  │ micro..yaml  │      with        │ +deps        │          │
│  │ data...yaml  │                  │dns.yaml      │          │
│  └──────────────┘                  │ +parameters  │          │
│         │                           │ +deps        │          │
│         │                           │... (16 total)│          │
│         │                           └──────────────┘          │
│         │                                  │                 │
│         ▼                                  ▼                 │
│  ┌────────────────────────────────────────────────┐         │
│  │  Template Variables + User Input               │         │
│  │  - Organization, Project, Domain               │         │
│  │  - AWS Accounts, Regions                       │         │
│  │  - Stack Selection, Environment Config         │         │
│  │  - Parameter defaults from enhanced templates  │         │
│  └────────────────┬───────────────────────────────┘         │
│                   │                                          │
│                   ▼                                          │
│  ┌────────────────────────────────────────────────┐         │
│  │  Rendered Deployment Manifest                  │         │
│  │  ./cloud/deploy/D1BRV40-.../Deployment...yaml │         │
│  └────────────────┬───────────────────────────────┘         │
│                   │                                          │
│                   ▼                                          │
│  ┌────────────────────────────────────────────────┐         │
│  │  Generated Config Files (Pulumi native format) │         │
│  │  ./cloud/deploy/D1BRV40/.../config/*.yaml     │         │
│  └────────────────────────────────────────────────┘         │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### Manifest Template Structure

**Location:** `./cloud/tools/templates/default/<template-name>.yaml`

See Platform Code Addendum, Section 8.1 for complete manifest template examples.

### Stack Template Structure (v3.1 - Basic)

**Location:** `./cloud/tools/templates/config/<stack-name>.yaml`

**Basic Structure (v3.1):**
```yaml
name: network
description: "VPC and networking infrastructure"
dependencies:
  - dns
layer: 1
```

### Enhanced Stack Template Structure (v4.0+ - NEW)

**Key Enhancement:** Structured parameter declarations with types, defaults, and validation.

**Enhanced Structure (v4.1):**
```yaml
name: network
version: "1.0"
description: "VPC and networking infrastructure"

parameters:
  inputs:
    vpcCidr:
      type: string
      required: true
      default: "10.0.0.0/16"
      description: "CIDR block for VPC"

    availabilityZones:
      type: number
      required: true
      default: 3
      description: "Number of AZs to span"

    enableNatGateway:
      type: boolean
      required: false
      default: true
      description: "Enable NAT Gateway for private subnets"

  outputs:
    vpcId:
      type: string
      description: "VPC ID for cross-stack references"

    privateSubnetIds:
      type: array
      description: "List of private subnet IDs"

    publicSubnetIds:
      type: array
      description: "List of public subnet IDs"

dependencies:
  - dns
layer: 1
```

**Key Differences v3.1 → v4.1:**
- Added `parameters.inputs` section with type specifications
- Added `parameters.outputs` section with type specifications
- Required/optional flags for better validation
- Default values documented in template
- Rich descriptions for better documentation
- Version field for template versioning

See Platform Code Addendum, Section 8.2 for complete stack template examples.

### Template Variables

**Global Variables** (all templates):
- `{{DEPLOYMENT_ID}}`: Auto-generated (D1BRV40) or user-provided
- `{{TIMESTAMP}}`: ISO 8601 timestamp of initialization
- `{{USER_EMAIL}}`: User email from system or Git config
- `{{ORGANIZATION}}`: Organization name (user input)
- `{{PROJECT_NAME}}`: Project name (user input)
- `{{DOMAIN}}`: Primary domain (user input)
- `{{PULUMI_ORG}}`: Pulumi organization (derived from org name)
- `{{PRIMARY_REGION}}`: Primary AWS region (user input, default: us-east-1)
- `{{SECONDARY_REGION}}`: Secondary AWS region (user input, default: us-west-2)
- `{{AWS_ACCOUNT_DEV}}`: Dev AWS account ID (user input)
- `{{AWS_ACCOUNT_STAGE}}`: Stage AWS account ID (user input)
- `{{AWS_ACCOUNT_PROD}}`: Prod AWS account ID (user input)
- `{{TEAM}}`: Team name (user input, default: infrastructure)
- `{{COST_CENTER}}`: Cost center (user input, default: engineering)
- `{{DESCRIPTION}}`: Deployment description (auto-generated or user input)

**Stack-Specific Variables:**
- Automatically derived from enhanced template `parameters.inputs` defaults (v4.0+)
- `{{VPC_CIDR_DEV}}`: VPC CIDR for dev (default from template)
- `{{VPC_CIDR_STAGE}}`: VPC CIDR for stage (default from template)
- `{{VPC_CIDR_PROD}}`: VPC CIDR for prod (default from template)
- ... (all stack parameters)

### Template Rendering (v4.1)

**Rendering Process:**
1. Load manifest template by name (default, minimal, microservices, data-platform)
2. Load all enhanced stack templates referenced in manifest template (v4.0+)
3. Extract dependencies from stack templates (single source of truth)
4. Extract parameter defaults from enhanced templates (v4.0+)
5. Collect user input (CLI flags or interactive prompts)
6. Resolve all template variables
7. Render manifest template with variables and parameter defaults
8. Render stack templates with variables, dependencies, and parameters
9. Combine rendered stack templates into manifest
10. Validate rendered manifest and dependency chains
11. Validate parameter types and requirements (v4.0+)
12. Write manifest to deployment directory
13. Generate Pulumi native config files from manifest (v4.1)

See Platform Code Addendum, Section 8.3 for rendering algorithm details.

### Template Management Commands

```bash
# List available templates
python -m cloud_cli.main list-templates

# Show template contents
python -m cloud_cli.main show-template default

# Validate template
python -m cloud_cli.main validate-template default

# Create custom template (from existing deployment)
python -m cloud_cli.main create-template my-template \
  --from-deployment D1BRV40 \
  --description "My custom template"

# Update template
python -m cloud_cli.main update-template my-template \
  --enable-stack monitoring \
  --disable-stack services-eks
```

---

## Enhanced Template System (v4.0+)

### Overview

The Enhanced Template System introduces **structured parameter declarations** that provide:
- Type safety and validation
- Default values and documentation
- Required vs optional parameter distinctions
- Foundation for auto-extraction and template-first validation

### Parameter Input Structure

**Definition Location:** `tools/templates/config/<stack>.yaml`

**Structure:**
```yaml
parameters:
  inputs:
    parameterName:
      type: string | number | boolean | array | object
      required: true | false
      default: <value>
      description: "Parameter description"
```

**Supported Types:**
- `string` - Text values
- `number` - Numeric values
- `boolean` - True/false values
- `array` - Lists of values
- `object` - Complex nested structures

**Required vs Optional:**
- `required: true` - Must be provided, will fail validation if missing
- `required: false` - Optional, uses default if not provided

### Parameter Output Structure

**Definition Location:** `tools/templates/config/<stack>.yaml`

**Structure:**
```yaml
parameters:
  outputs:
    outputName:
      type: string | array | object
      description: "Output description"
```

**Purpose:**
- Document what outputs the stack exposes
- Enable validation that stack code exports declared outputs
- Support cross-stack dependency validation
- Improve discoverability of available cross-stack references

### Complete Enhanced Template Example

```yaml
name: database-rds
version: "1.0"
description: "RDS database stack with automated backups"

parameters:
  inputs:
    # Database configuration
    instanceClass:
      type: string
      required: true
      default: "db.t3.micro"
      description: "RDS instance class"

    allocatedStorage:
      type: number
      required: true
      default: 20
      description: "Allocated storage in GB"

    databaseName:
      type: string
      required: true
      default: "myapp"
      description: "Name of the default database"

    multiAz:
      type: boolean
      required: false
      default: false
      description: "Enable multi-AZ deployment"

    backupRetentionDays:
      type: number
      required: false
      default: 7
      description: "Number of days to retain backups"

    # Dependencies (cross-stack references)
    vpcId:
      type: string
      required: true
      description: "VPC ID from network stack"

    subnetIds:
      type: array
      required: true
      description: "Subnet IDs for RDS placement"

    securityGroupId:
      type: string
      required: true
      description: "Security group ID from security stack"

  outputs:
    dbEndpoint:
      type: string
      description: "RDS endpoint hostname"

    dbPort:
      type: number
      description: "RDS port number"

    dbName:
      type: string
      description: "Database name"

    connectionString:
      type: string
      description: "Full connection string (without credentials)"

dependencies:
  - network
  - security
  - secrets
layer: 4
```

### Benefits of Enhanced Templates

**Documentation:**
- Self-documenting stack requirements
- Clear parameter types and purposes
- Default values visible to users

**Validation:**
- Type checking during deployment
- Required parameter enforcement
- Foundation for template-first validation

**Auto-Extraction:**
- Parameter structure enables automatic extraction
- Outputs structure enables automatic export detection
- Reduces manual template maintenance

**Developer Experience:**
- Clear contract between templates and code
- Better IDE support with type information
- Easier onboarding for new developers

---

## Auto-Extraction System (v4.0+)

### Overview

The Auto-Extraction System automatically generates enhanced templates from TypeScript stack code, reducing manual maintenance and preventing template-code drift.

**Key Components:**
- `ParameterExtractor` - Extracts input parameters from TypeScript code
- `TypeScriptParser` - Parses TypeScript to extract exports and types
- Integrated into stack registration workflow

**Location:**
- `tools/cli/cloud_cli/parser/parameter_extractor.py`
- `tools/cli/cloud_cli/parser/typescript_parser.py`

### ParameterExtractor

**Purpose:** Analyze TypeScript code to extract input parameters from Pulumi Config API calls.

**Extraction Logic:**

**1. Required String Parameters:**
```typescript
const vpcCidr = config.require("vpcCidr");

// Extracted as:
vpcCidr:
  type: string
  required: true
  description: "Auto-extracted from code"
```

**2. Required Number Parameters:**
```typescript
const azCount = config.requireNumber("availabilityZones");

// Extracted as:
availabilityZones:
  type: number
  required: true
  description: "Auto-extracted from code"
```

**3. Optional Parameters:**
```typescript
const enableNat = config.getBoolean("enableNatGateway") ?? true;

// Extracted as:
enableNatGateway:
  type: boolean
  required: false
  default: true  # from default value in code
  description: "Auto-extracted from code"
```

**4. Array Parameters:**
```typescript
const subnetIds = config.requireObject<string[]>("subnetIds");

// Extracted as:
subnetIds:
  type: array
  required: true
  description: "Auto-extracted from code"
```

**Supported Config Methods:**
- `config.require(key)` → string, required
- `config.requireNumber(key)` → number, required
- `config.requireBoolean(key)` → boolean, required
- `config.requireObject<T>(key)` → array/object, required
- `config.get(key)` → string, optional
- `config.getNumber(key)` → number, optional
- `config.getBoolean(key)` → boolean, optional
- `config.getObject<T>(key)` → array/object, optional

### TypeScriptParser

**Purpose:** Parse TypeScript code to extract output exports.

**Extraction Logic:**

**1. Simple Exports:**
```typescript
export const vpcId = vpc.id;

// Extracted as:
vpcId:
  type: string  # inferred from Pulumi resource property
  description: "Auto-extracted from code"
```

**2. Array Exports:**
```typescript
export const privateSubnetIds = subnets.map(s => s.id);

// Extracted as:
privateSubnetIds:
  type: array
  description: "Auto-extracted from code"
```

**3. Object Exports:**
```typescript
export const dbConnection = {
  endpoint: db.endpoint,
  port: db.port,
  name: dbName
};

// Extracted as:
dbConnection:
  type: object
  description: "Auto-extracted from code"
```

**Type Inference:**
- Analyzes Pulumi resource properties (e.g., `vpc.id` is string)
- Detects array operations (`.map()`, `[]`)
- Detects object literals (`{...}`)
- Falls back to `string` for unknown types

### Auto-Extraction Workflow

**Command:**
```bash
python -m cloud_cli.main register-stack network --auto-extract
```

**Process:**
1. **Locate Stack Files:**
   - Find `stacks/network/src/index.ts`
   - Find additional TypeScript files in `stacks/network/src/`

2. **Extract Inputs (ParameterExtractor):**
   - Parse all TypeScript files
   - Find all `config.require*()` and `config.get*()` calls
   - Extract parameter names and types
   - Detect default values from code
   - Determine required vs optional

3. **Extract Outputs (TypeScriptParser):**
   - Parse all TypeScript files
   - Find all `export const` statements
   - Infer output types from Pulumi properties
   - Extract output names

4. **Generate Enhanced Template:**
   - Create `parameters.inputs` section
   - Create `parameters.outputs` section
   - Add metadata (name, description, version)
   - Include dependencies if specified

5. **Prompt User:**
   - Show extracted parameters
   - Ask for confirmation
   - Allow manual edits before saving

6. **Save Template:**
   - Write to `tools/templates/config/network.yaml`
   - Register in template system

### Auto-Extraction Output Example

**Input:** `stacks/network/src/index.ts`
```typescript
import * as pulumi from "@pulumi/pulumi";
import * as aws from "@pulumi/aws";

const config = new pulumi.Config();
const vpcCidr = config.require("vpcCidr");
const azCount = config.requireNumber("availabilityZones");
const enableNat = config.getBoolean("enableNatGateway") ?? true;

// ... VPC creation ...

export const vpcId = vpc.id;
export const privateSubnetIds = privateSubnets.map(s => s.id);
export const publicSubnetIds = publicSubnets.map(s => s.id);
```

**Command:**
```bash
python -m cloud_cli.main register-stack network --auto-extract
```

**Output:**
```
Extracting parameters from stacks/network/index.ts...

Found inputs:
  - vpcCidr (string, required)
  - availabilityZones (number, required)
  - enableNatGateway (boolean, optional, default: true)

Found outputs:
  - vpcId (string)
  - privateSubnetIds (array)
  - publicSubnetIds (array)

Generate enhanced template? [Y/n]: y

✓ Template generated: tools/templates/config/network.yaml
✓ Stack registered successfully
```

**Generated Template:** `tools/templates/config/network.yaml`
```yaml
name: network
version: "1.0"
description: "VPC and networking infrastructure (auto-generated)"

parameters:
  inputs:
    vpcCidr:
      type: string
      required: true
      description: "Auto-extracted from code"

    availabilityZones:
      type: number
      required: true
      description: "Auto-extracted from code"

    enableNatGateway:
      type: boolean
      required: false
      default: true
      description: "Auto-extracted from code"

  outputs:
    vpcId:
      type: string
      description: "Auto-extracted from code"

    privateSubnetIds:
      type: array
      description: "Auto-extracted from code"

    publicSubnetIds:
      type: array
      description: "Auto-extracted from code"

dependencies: []
layer: 1
```

### Benefits of Auto-Extraction

**Reduced Manual Work:**
- 80-90% reduction in template creation time
- No manual parameter documentation needed
- Automatic synchronization with code changes

**Accuracy:**
- Eliminates human error in template creation
- Ensures template matches actual code
- Detects all parameters automatically

**Maintainability:**
- Re-run extraction after code changes
- Keeps templates synchronized
- Foundation for template-first validation

**Developer Experience:**
- Faster stack registration
- Less context switching
- Focus on code, not documentation

### Limitations and Considerations

**Limitations:**
- Cannot extract parameter descriptions (uses generic descriptions)
- Cannot extract validation rules
- Cannot detect complex conditional logic
- Limited to standard Pulumi Config API patterns

**Manual Refinement Recommended:**
- Edit generated template to add meaningful descriptions
- Add validation rules manually
- Adjust default values if needed
- Review and approve before saving

**Best Practice:**
1. Use auto-extraction for initial template creation
2. Manually refine descriptions and validation
3. Re-run extraction only when adding/removing parameters
4. Use template-first validation to maintain consistency

---

## Template-First Validation (v4.0+)

### Overview

Template-First Validation enforces consistency between stack templates and stack code, preventing drift and catching errors early.

**Key Component:**
- `StackCodeValidator` - Validates stack code against template specifications

**Location:**
- `tools/core/cloud_core/validation/stack_code_validator.py`

**Philosophy:** Templates are the source of truth. Code must match templates.

### StackCodeValidator

**Purpose:** Ensure stack code uses all declared inputs and exports all declared outputs.

**Validation Rules:**

**1. Input Validation:**
- Every input declared in template must be used in code
- Code must use appropriate Config method for type
  - `string` → `config.require()` or `config.get()`
  - `number` → `config.requireNumber()` or `config.getNumber()`
  - `boolean` → `config.requireBoolean()` or `config.getBoolean()`
  - `array/object` → `config.requireObject()` or `config.getObject()`

**2. Output Validation:**
- Every output declared in template must be exported in code
- Export names must match exactly

**3. Strict Mode:**
- Optional: Treat warnings as errors
- Enforces zero tolerance for mismatches

### Validation Workflow

**Command:**
```bash
# Validate single stack
python -m cloud_cli.main validate-stack network

# Strict validation (warnings = errors)
python -m cloud_cli.main validate-stack network --strict

# Validate all stacks
python -m cloud_cli.main validate-stack --all
```

**Process:**
1. **Load Template:**
   - Read `tools/templates/config/network.yaml`
   - Extract `parameters.inputs` and `parameters.outputs`

2. **Load Stack Code:**
   - Read `stacks/network/src/index.ts`
   - Read additional TypeScript files

3. **Validate Inputs:**
   - For each input in template:
     - Search code for `config.require*()` or `config.get*()` call
     - Verify correct method for type
     - Flag if not found (ERROR) or wrong method (WARNING)

4. **Validate Outputs:**
   - For each output in template:
     - Search code for `export const <name>`
     - Flag if not found (ERROR)

5. **Report Results:**
   - List all validations
   - Show errors and warnings
   - Return PASSED or FAILED

### Validation Output Examples

**Example 1: All Valid**
```
Validating stack: network
✓ Template: tools/templates/config/network.yaml
✓ Code: stacks/network/index.ts

Input Parameters:
✓ vpcCidr: declared in template, used in code (Config.require)
✓ availabilityZones: declared in template, used in code (Config.requireNumber)
✓ enableNatGateway: declared in template, used in code (Config.getBoolean)

Output Parameters:
✓ vpcId: declared in template, exported in code
✓ privateSubnetIds: declared in template, exported in code
✓ publicSubnetIds: declared in template, exported in code

Result: PASSED
```

**Example 2: Missing Input**
```
Validating stack: network
✓ Template: tools/templates/config/network.yaml
✓ Code: stacks/network/index.ts

Input Parameters:
✓ vpcCidr: declared in template, used in code (Config.require)
✓ availabilityZones: declared in template, used in code (Config.requireNumber)
✗ enableNatGateway: declared in template, NOT FOUND in code

Output Parameters:
✓ vpcId: declared in template, exported in code
✓ privateSubnetIds: declared in template, exported in code

Result: FAILED
  1 error found

Fix: Add the following to stacks/network/src/index.ts:
  const enableNatGateway = config.getBoolean("enableNatGateway");
```

**Example 3: Missing Output**
```
Validating stack: network
✓ Template: tools/templates/config/network.yaml
✓ Code: stacks/network/index.ts

Input Parameters:
✓ vpcCidr: declared in template, used in code (Config.require)
✓ availabilityZones: declared in template, used in code (Config.requireNumber)

Output Parameters:
✓ vpcId: declared in template, exported in code
✗ privateSubnetIds: declared in template, NOT EXPORTED in code
✓ publicSubnetIds: declared in template, exported in code

Result: FAILED
  1 error found

Fix: Add the following to stacks/network/src/index.ts:
  export const privateSubnetIds = ...;
```

**Example 4: Warning (Optional Parameter Not Used)**
```
Validating stack: network
✓ Template: tools/templates/config/network.yaml
✓ Code: stacks/network/index.ts

Input Parameters:
✓ vpcCidr: declared in template, used in code (Config.require)
✓ availabilityZones: declared in template, used in code (Config.requireNumber)
⚠ enableNatGateway: declared in template (optional), not found in code

Output Parameters:
✓ vpcId: declared in template, exported in code
✓ privateSubnetIds: declared in template, exported in code

Result: PASSED with 1 warning
  Use --strict to treat warnings as errors
```

### Strict Mode

**Purpose:** Enforce zero tolerance for template-code mismatches.

**Command:**
```bash
python -m cloud_cli.main validate-stack network --strict
```

**Behavior:**
- Warnings treated as errors
- Fails if ANY mismatch found
- Recommended for CI/CD pipelines
- Ensures complete consistency

**Example:**
```
Validating stack: network (STRICT MODE)
✓ Template: tools/templates/config/network.yaml
✓ Code: stacks/network/index.ts

Input Parameters:
✓ vpcCidr: declared in template, used in code (Config.require)
✓ availabilityZones: declared in template, used in code (Config.requireNumber)
✗ enableNatGateway: declared in template (optional), not found in code
    (STRICT MODE: optional parameter not used)

Result: FAILED (strict mode)
  1 strict mode violation found
```

### Integration with Deployment Workflow

**Pre-Deployment Validation:**
```bash
# Automatically run before deployment
python -m cloud_cli.main deploy D1BRV40 --environment dev

# Internally runs:
#   validate-stack --all
#   (fails deployment if validation fails)
```

**CI/CD Integration:**
```yaml
# .github/workflows/validate.yml
- name: Validate Stack Templates
  run: |
    python -m cloud_cli.main validate-stack --all --strict
```

### Benefits of Template-First Validation

**Early Error Detection:**
- Catch missing parameters before deployment
- Catch missing outputs before cross-stack references fail
- Prevent runtime errors

**Consistency Enforcement:**
- Templates and code always match
- No drift over time
- Clear source of truth (templates)

**Better Developer Experience:**
- Clear error messages with fixes
- Catch errors locally before push
- Faster feedback loop

**Architectural Standards:**
- Enforces parameter declarations
- Enforces output declarations
- Maintains clean contracts between stacks

### Limitations and Considerations

**Limitations:**
- Cannot validate parameter usage logic (only presence)
- Cannot validate output values (only presence)
- Limited to standard Pulumi Config API patterns
- Cannot validate conditional logic

**Best Practices:**
1. Run validation after code changes
2. Use strict mode in CI/CD
3. Keep templates as source of truth
4. Re-run auto-extraction if parameters change significantly
5. Manual validation before deployment

**Recommended Workflow:**
1. Write/update stack code
2. Run auto-extraction if major changes
3. Run validation to ensure consistency
4. Fix any errors or warnings
5. Commit changes
6. CI/CD runs strict validation
7. Deploy if validation passes

---

## Dynamic Pulumi.yaml Management (v4.5+)

### Overview

The Dynamic Pulumi.yaml Management system solves a fundamental incompatibility between Pulumi's validation requirements and the architecture's deployment-specific project naming strategy. It enables proper stack organization in Pulumi Cloud by business project while maintaining clean, reusable stack directories.

**Key Innovation:** Context manager pattern for temporary Pulumi.yaml modification with guaranteed restoration.

### The Problem

**Architecture Requirement (v4.1):**
All stacks for a deployment should be organized under one Pulumi project in Pulumi Cloud:
```
{pulumiOrg}/{project}/{deployment-id}-{stack-name}-{environment}
andre-2112/ecommerce/D1BRV40-network-dev
andre-2112/ecommerce/D1BRV40-security-dev
andre-2112/ecommerce/D1BRV40-database-dev
```

**Pulumi Validation:**
Pulumi CLI validates the project name in commands against the `name:` field in `Pulumi.yaml`:
```yaml
# stacks/network/Pulumi.yaml
name: network  # Stack type name (hardcoded)
runtime: nodejs
```

**The Conflict:**
- Commands need deployment project: `pulumi up --stack andre-2112/ecommerce/D1BRV40-network-dev`
- Pulumi.yaml contains stack type: `name: network`
- Pulumi rejects: "error: provided project name 'ecommerce' doesn't match Pulumi.yaml"

**Why Not Change Pulumi.yaml Permanently?**
- Stack directories are shared across all deployments (99.9% disk space savings)
- Changing `name:` to deployment project breaks other deployments
- Need one stack directory (network) to serve hundreds of deployments

### The Solution

Dynamic generation of deployment-specific Pulumi.yaml during operations with automatic restoration.

**Core Mechanism:**

```python
@contextmanager
def deployment_context(self, stack_dir: Path, stack_name: str):
    """
    Temporarily modify Pulumi.yaml for deployment-specific operations

    1. Backup original Pulumi.yaml (with project-specific name)
    2. Generate temporary Pulumi.yaml (with deployment project name)
    3. Execute Pulumi operations
    4. Restore original Pulumi.yaml (guaranteed via finally block)
    """
    backup_path = None
    try:
        backup_path = self._backup_pulumi_yaml(stack_dir)
        self._generate_pulumi_yaml(stack_dir, stack_name)
        yield
    finally:
        self._restore_pulumi_yaml(stack_dir, backup_path)
```

### Implementation Details

#### Backup Process (`_backup_pulumi_yaml`)

**Location:** `tools/core/cloud_core/pulumi/pulumi_wrapper.py`

**Features:**
- Project-specific backup naming: `Pulumi.yaml.backup.{project}`
- Cleans up stale backups from previous runs
- Retry logic with exponential backoff (1s, 2s) for Windows file locking
- Fails after 3 attempts with clear error message

**Code:**
```python
def _backup_pulumi_yaml(self, stack_dir: Path) -> Optional[Path]:
    pulumi_yaml = stack_dir / "Pulumi.yaml"
    if not pulumi_yaml.exists():
        logger.warning(f"No Pulumi.yaml found in {stack_dir}")
        return None

    # Project-specific backup prevents concurrent deployment conflicts
    backup_path = stack_dir / f"Pulumi.yaml.backup.{self.project}"

    # Clean up stale backup
    if backup_path.exists():
        logger.warning(f"Found stale backup {backup_path}, removing")
        backup_path.unlink()

    # Retry with exponential backoff
    for attempt in range(3):
        try:
            shutil.copy2(pulumi_yaml, backup_path)
            logger.debug(f"Backed up Pulumi.yaml to {backup_path}")
            return backup_path
        except (PermissionError, IOError) as e:
            if attempt < 2:
                wait_time = 2 ** attempt
                logger.warning(f"Backup failed, retrying in {wait_time}s: {e}")
                time.sleep(wait_time)
            else:
                raise PulumiError(f"Cannot backup Pulumi.yaml after 3 attempts: {e}")
```

#### Generation Process (`_generate_pulumi_yaml`)

**Features:**
- Preserves original `runtime` and `description` metadata
- Uses deployment project name for `name:` field
- Standard YAML format compatible with Pulumi
- Handles missing or corrupted original files gracefully

**Code:**
```python
def _generate_pulumi_yaml(self, stack_dir: Path, stack_name: str) -> None:
    pulumi_yaml = stack_dir / "Pulumi.yaml"

    # Read original to preserve runtime and description
    original_content = {}
    if pulumi_yaml.exists():
        try:
            with open(pulumi_yaml, 'r') as f:
                original_content = yaml.safe_load(f) or {}
        except Exception as e:
            logger.warning(f"Could not read original Pulumi.yaml: {e}")

    # Generate with deployment project name
    new_content = {
        'name': self.project,  # Deployment project (e.g., "ecommerce")
        'runtime': original_content.get('runtime', 'nodejs'),
        'description': original_content.get('description', f'{stack_name} stack'),
    }

    try:
        with open(pulumi_yaml, 'w') as f:
            yaml.safe_dump(new_content, f, default_flow_style=False)
        logger.info(f"Generated Pulumi.yaml with project: {self.project}")
    except Exception as e:
        raise PulumiError(f"Cannot generate Pulumi.yaml: {e}")
```

#### Restoration Process (`_restore_pulumi_yaml`)

**Features:**
- Best-effort restoration (doesn't raise exceptions)
- Retry logic for file operations
- Logs errors but doesn't fail (cleanup context)
- Uses `shutil.move()` for atomic operation

**Code:**
```python
def _restore_pulumi_yaml(self, stack_dir: Path, backup_path: Optional[Path]) -> None:
    if not backup_path or not backup_path.exists():
        return

    pulumi_yaml = stack_dir / "Pulumi.yaml"

    # Retry up to 3 times
    for attempt in range(3):
        try:
            shutil.move(str(backup_path), str(pulumi_yaml))
            logger.debug(f"Restored Pulumi.yaml from backup")
            return
        except (PermissionError, IOError) as e:
            if attempt < 2:
                wait_time = 2 ** attempt
                logger.warning(f"Restore failed, retrying in {wait_time}s: {e}")
                time.sleep(wait_time)
            else:
                # Don't raise - we're in cleanup, best effort only
                logger.error(f"Cannot restore Pulumi.yaml after 3 attempts: {e}")
```

### Usage Pattern

**All deployment and destruction commands use the context manager:**

```python
# deploy_stack_cmd.py (line 129-140)
# destroy_stack_cmd.py (line 106-115)
# deploy_cmd.py (line 206-217)

with pulumi_wrapper.deployment_context(stack_dir, stack_name):
    # All Pulumi operations within this context use deployment project name
    success, error = stack_ops.deploy_stack(
        deployment_id=deployment_id,
        stack_name=stack_name,
        environment=environment,
        stack_dir=stack_dir,
        config=config,
    )
# Original Pulumi.yaml automatically restored here by context manager
```

### Concurrent Deployment Safety

**Problem:** Multiple deployments running simultaneously could conflict.

**Solution:** Project-specific backup file naming.

**Example:**
```
# Deployment 1 (project: ecommerce)
stacks/network/Pulumi.yaml.backup.ecommerce

# Deployment 2 (project: analytics) running concurrently
stacks/network/Pulumi.yaml.backup.analytics

# No conflicts - each deployment has its own backup
```

### Error Handling

**Guaranteed Restoration:**
- `finally` block ensures restoration even on exceptions
- Errors during deployment don't leave stale generated files
- Interruptions (Ctrl+C) trigger cleanup via context manager exit

**Retry Logic:**
- Handles Windows file locking issues
- Exponential backoff: 1s, 2s (total 3 attempts)
- Clear error messages for debugging

**Stale Backup Cleanup:**
- Detects leftover backups from crashed runs
- Automatically removes before creating new backup
- Prevents accumulation of backup files

### Benefits

1. **Correct Pulumi Cloud Organization:**
   - All stacks for a deployment grouped under one project
   - Easier filtering, searching, and management
   - Better dashboard organization

2. **Shared Stack Directories:**
   - Maintains 99.9% disk space savings
   - One stack implementation serves hundreds of deployments
   - No duplication of stack code

3. **Zero Manual Intervention:**
   - Fully automatic backup and restore
   - No user action required
   - Transparent to deployment operations

4. **Concurrent Deployment Support:**
   - Multiple deployments don't conflict
   - Project-specific backup naming
   - Safe for CI/CD parallelization

5. **Backward Compatible:**
   - Original Pulumi.yaml files unchanged
   - Existing deployments continue working
   - No migration required

### Verification

**Check Original Pulumi.yaml Preserved:**
```bash
cat cloud/stacks/network/Pulumi.yaml
# Output should show:
# name: network  (stack type, not deployment project)
# runtime: nodejs
# description: Network infrastructure stack
```

**Check No Backup Files Left:**
```bash
ls -la cloud/stacks/network/Pulumi.yaml.backup.*
# Output should show: No such file or directory
```

**Check Correct Pulumi Cloud Organization:**
```bash
pulumi stack ls --all
# Output should show:
# andre-2112/ecommerce/D1BRV40-network-dev     (grouped by project)
# andre-2112/ecommerce/D1BRV40-security-dev
# andre-2112/analytics/D2XYZ89-network-dev     (different project)
```

### Further Reading

Complete implementation details, edge cases, and testing strategy documented in:
`tools/docs/Addendum_Dynamic_Pulumi_YAML_Implementation.4.1.md`

---

## Deployment Initialization

### Initialization Overview

Deployment initialization creates a new deployment instance from enhanced templates with structured parameters, dependencies resolved, and Pulumi native configuration files generated.

**Process Flow:**
1. Generate or accept deployment ID (D<base36-timestamp> format)
2. Create deployment directory structure with config/ subdirectory
3. Load enhanced templates with structured parameters
4. Resolve dependency chains from template declarations
5. Collect user input (CLI flags or interactive prompts)
6. Render manifest from template with parameter defaults
7. Generate Pulumi native format config files in config/ subdirectory
8. Validate generated manifest and configuration
9. Log initialization process
10. Report results to user

### Deployment ID Format

**Format:** `D<base36-timestamp>`

**Characteristics:**
- **Length**: 7 characters (D + 6 base36 digits)
- **Uniqueness**: Unix timestamp encoded in base36 guarantees uniqueness
- **Sortable**: Chronologically ordered (alphabetically sortable)
- **Readable**: Easy to reference in commands, logs, and documentation
- **AWS-Compatible**: Fits within all AWS resource naming limits (63 characters)
- **Example**: D1BRV40 (timestamp: 1696881600 seconds since epoch)

**Generation Algorithm:**
```python
import time
import base64

def generate_deployment_id():
    timestamp = int(time.time())
    # Convert to base36 (0-9, a-z)
    chars = '0123456789abcdefghijklmnopqrstuvwxyz'
    base36 = ''
    while timestamp:
        base36 = chars[timestamp % 36] + base36
        timestamp //= 36
    return f'D{base36.upper()}'
```

### Directory Structure Creation

**Generated Structure:**
```
./cloud/deploy/D1BRV40-CompanyA-ecommerce/
├── Deployment_Manifest.yaml        # Deployment configuration
├── config/                          # Configuration subdirectory
│   ├── network.dev.yaml            # Pulumi native format
│   ├── network.stage.yaml
│   ├── network.prod.yaml
│   ├── security.dev.yaml
│   ├── security.stage.yaml
│   └── ... (one file per stack × environment)
└── logs/
    └── init.log                     # Initialization log
```

**Directory Naming:**
- Format: `<deployment-id>-<org-sanitized>-<project-sanitized>`
- Example: `D1BRV40-CompanyA-ecommerce`
- Sanitization: Lowercase, alphanumeric and dashes only, collapse multiple dashes
- Ensures filesystem compatibility across all platforms

### Initialization Commands

**Auto-Generated ID:**
```bash
python -m cloud_cli.main init \
  --org "Company-A" \
  --project "ecommerce" \
  --domain "ecommerce.companyA.com" \
  --template default \
  --region us-east-1 \
  --account-dev 111111111111 \
  --account-stage 222222222222 \
  --account-prod 333333333333
```

**Explicit ID:**
```bash
python -m cloud_cli.main init D1CUSTOM \
  --org "Company-A" \
  --project "ecommerce" \
  --template minimal
```

**Interactive Mode:**
```bash
python -m cloud_cli.main init --interactive
```

**From Configuration File:**
```bash
python -m cloud_cli.main init --from-file ./config/deployment.yaml
```

### Configuration File Generation

**Process:**
1. Load deployment manifest
2. Load enhanced stack templates with parameter specifications
3. For each enabled environment (dev, stage, prod):
   - For each enabled stack:
     - Extract stack configuration from manifest
     - Apply parameter defaults from enhanced template
     - Apply user overrides from manifest
     - Generate Pulumi native format YAML
     - Write to config/<stack>.<env>.yaml

**Generated File Example:**
```yaml
# config/network.dev.yaml (Pulumi native format)
network:deploymentId: "D1BRV40"
network:vpcCidr: "10.0.0.0/16"
network:availabilityZones: "3"
network:enableNatGateway: "true"
aws:region: "us-east-1"
aws:profile: "companya-dev"
```

**File Count:**
```
Total Config Files = Number of Stacks × Number of Enabled Environments

Example:
- 16 stacks
- 3 environments (dev, stage, prod)
- Total: 48 config files
```

---

## Configuration Management

### Configuration Architecture

The v4.1 configuration system uses a three-tier resolution strategy with enhanced templates, Pulumi native format, and runtime placeholder resolution.

**Architecture Layers:**

**Layer 1: Enhanced Template Defaults**
- Location: `tools/templates/config/<stack>.yaml`
- Contains: Structured parameters with types, defaults, validation rules
- Scope: All deployments using the template
- Purpose: Provide sensible, documented defaults

**Layer 2: Deployment Manifest**
- Location: `deploy/<id>/Deployment_Manifest.yaml`
- Contains: User customizations and overrides
- Scope: Specific deployment
- Purpose: Deployment-specific configuration

**Layer 3: Generated Configuration**
- Location: `deploy/<id>/config/<stack>.<env>.yaml`
- Format: Pulumi native (`stackname:key: "value"`)
- Contains: Resolved configuration ready for Pulumi
- Purpose: Pulumi execution input

**Layer 4: Runtime Resolution**
- Process: PlaceholderResolver execution during deployment
- Resolves: `${stack.output}` placeholders to actual values
- Scope: Deployment execution
- Purpose: Cross-stack references and dynamic values

### Configuration Resolution Flow

```
Enhanced Template
  └─ parameters.inputs with defaults
      ↓
Deployment Manifest
  └─ User overrides (optional)
      ↓
Generated Config Files (Pulumi Native Format)
  └─ Merged defaults + overrides
      ↓
Runtime Placeholder Resolution
  └─ ${stack.output} → actual values
      ↓
Pulumi Execution
  └─ Resources created with resolved config
```

### Pulumi Native Configuration Format

**Format Specification:**
```yaml
# Format: <namespace>:<key>: "<value>"
# All values are strings (Pulumi requirement)

# Stack parameters (namespace = stack name)
network:vpcCidr: "10.0.0.0/16"
network:availabilityZones: "3"
network:enableNatGateway: "true"

# AWS provider configuration
aws:region: "us-east-1"
aws:profile: "myprofile"

# Cross-stack references (resolved at runtime)
security:vpcId: "${network.vpcId}"
```

**Benefits:**
- Direct Pulumi CLI compatibility
- Standard format across ecosystem
- Simple parsing and generation
- Native tooling support

### Stack Configuration Pattern

**Minimal Pulumi.yaml (Stack Directory):**
```yaml
name: network
runtime: nodejs
description: VPC and networking infrastructure
```

**Enhanced Template (Template System):**
```yaml
name: network
version: "1.0"
parameters:
  inputs:
    vpcCidr:
      type: string
      required: true
      default: "10.0.0.0/16"
```

**Generated Config (Deployment Directory):**
```yaml
# deploy/D1BRV40/config/network.dev.yaml
network:vpcCidr: "10.0.0.0/16"
network:availabilityZones: "3"
aws:region: "us-east-1"
```

**Stack Code (TypeScript):**
```typescript
const config = new pulumi.Config();
const vpcCidr = config.require("vpcCidr");
// Reads from network:vpcCidr in config file
```

### Configuration Usage in Stack Code

**Reading Simple Values:**
```typescript
import * as pulumi from "@pulumi/pulumi";

const config = new pulumi.Config();

// String values
const vpcCidr = config.require("vpcCidr");
const region = config.require("region");

// Number values
const azCount = config.requireNumber("availabilityZones");
const instanceCount = config.requireNumber("instanceCount");

// Boolean values
const enableNat = config.requireBoolean("enableNatGateway");

// Optional values with defaults
const environment = config.get("environment") || "dev";
```

**Reading Complex Values:**
```typescript
// Array values
const subnetIds = config.requireObject<string[]>("subnetIds");

// Object values
const tags = config.requireObject<Record<string, string>>("tags");

// JSON strings
const metadata = JSON.parse(config.require("metadata"));
```

**Cross-Stack References:**
```typescript
// References are resolved before Pulumi execution
// Stack code receives final values, not placeholders
const vpcId = config.require("vpcId");
// Receives: "vpc-0abc123" (not "${network.vpcId}")
```

---

## Multi-Environment Support

### Environment Architecture

The platform supports multiple environments (dev, stage, prod) within a single deployment, each with independent configuration, AWS accounts, and Pulumi state.

**Environment Characteristics:**
- **Independence**: Separate AWS accounts, regions, and resources
- **Isolation**: Independent Pulumi state per environment
- **Configuration**: Per-environment parameters and settings
- **Promotion**: Sequential workflow (dev → stage → prod)
- **Flexibility**: Different resource sizing and features per environment

### Environment Configuration Structure

**Manifest Definition:**
```yaml
environments:
  dev:
    enabled: true
    account: "111111111111"
    region: "us-east-1"

  stage:
    enabled: false  # Enable after dev validation
    account: "222222222222"
    region: "us-east-1"

  prod:
    enabled: false  # Enable after stage validation
    account: "333333333333"
    region: "us-west-2"  # Different region for DR
```

**Per-Stack Environment Config:**
```yaml
stacks:
  network:
    enabled: true
    config:
      dev:
        vpcCidr: "10.0.0.0/16"
        availabilityZones: 2
      stage:
        vpcCidr: "10.1.0.0/16"
        availabilityZones: 2
      prod:
        vpcCidr: "10.2.0.0/16"
        availabilityZones: 3  # More AZs for production
```

### Environment Promotion Workflow

**Stage 1: Development**
```bash
# Deploy to dev
python -m cloud_cli.main deploy D1BRV40 --environment dev

# Validate
python -m cloud_cli.main status D1BRV40 --environment dev
python -m cloud_cli.main validate D1BRV40 --environment dev

# Test applications and infrastructure
# Monitor for 24-48 hours
```

**Stage 2: Staging**
```bash
# Enable stage environment
python -m cloud_cli.main enable-environment D1BRV40 stage

# Deploy to stage
python -m cloud_cli.main deploy D1BRV40 --environment stage

# Run integration tests
# Perform load testing
# Monitor for 48-72 hours
```

**Stage 3: Production**
```bash
# Enable production environment
python -m cloud_cli.main enable-environment D1BRV40 prod

# Deploy to production (requires confirmation)
python -m cloud_cli.main deploy D1BRV40 --environment prod --confirm

# Monitor closely
python -m cloud_cli.main logs D1BRV40 --environment prod --follow
```

### Pulumi Stack Naming Convention

**Format:** `<deployment-id>-<stack-name>-<environment>`

**Examples:**
```
D1BRV40-network-dev
D1BRV40-network-stage
D1BRV40-network-prod
D1BRV40-security-dev
D1BRV40-security-stage
D1BRV40-security-prod
D1BRV40-database-rds-dev
D1BRV40-database-rds-stage
D1BRV40-database-rds-prod
```

**Pulumi Cloud Organization:**
```
Pulumi Organization: CompanyA
└── Project: ecommerce  # Business project
    ├── Stack: D1BRV40-network-dev
    ├── Stack: D1BRV40-network-stage
    ├── Stack: D1BRV40-network-prod
    ├── Stack: D1BRV40-security-dev
    ├── Stack: D1BRV40-security-stage
    └── ... (all stacks for this deployment)
```

### Environment Isolation Strategy

**AWS Account Separation:**
- Dev: Shared account (multiple deployments)
- Stage: Shared account (multiple deployments)
- Production: Dedicated account per deployment (security)

**Network Isolation:**
- Dev: VPC CIDR 10.0.0.0/16
- Stage: VPC CIDR 10.1.0.0/16
- Production: VPC CIDR 10.2.0.0/16

**Resource Sizing:**
```yaml
# Dev: Small instances
compute-ec2:
  dev:
    instanceType: "t3.micro"
    count: 1

# Stage: Medium instances
compute-ec2:
  stage:
    instanceType: "t3.small"
    count: 2

# Production: Large instances
compute-ec2:
  prod:
    instanceType: "c5.xlarge"
    count: 4
    autoScaling: true
```

---

## Dependency Resolution

### Dependency Resolution System

The DependencyResolver in `cloud_core.orchestrator` analyzes stack dependencies and calculates execution order using topological sorting.

**Dependency Sources:**
1. **Template-Declared Dependencies**: Explicit `dependencies: []` in stack templates
2. **Implicit Dependencies**: Derived from `${stack.output}` placeholders in configuration
3. **Priority Hints**: Optional execution order hints within layers

### Dependency Resolution Algorithm

**Implementation:** `cloud_core.orchestrator.dependency_resolver.DependencyResolver`

**Algorithm:**
```python
def resolve_dependencies(stacks: List[Stack]) -> List[Layer]:
    """
    Topological sort with cycle detection.

    Returns ordered layers for parallel execution within layers.
    """
    # 1. Build dependency graph
    graph = build_graph(stacks)

    # 2. Detect cycles using DFS
    if has_cycle(graph):
        raise CircularDependencyError()

    # 3. Calculate layers
    layers = []
    remaining = set(stacks)

    while remaining:
        # Find stacks with no unmet dependencies
        layer = [s for s in remaining if dependencies_met(s, deployed)]

        if not layer:
            raise UnresolvableDependencyError()

        layers.append(layer)
        remaining -= set(layer)
        deployed.update(layer)

    return layers
```

**Execution Order Example:**
```
Layer 1 (Parallel Execution):
  - dns (no dependencies)
  - network (no dependencies)

Layer 2 (Parallel Execution):
  - security (depends on: network)

Layer 3 (Parallel Execution):
  - secrets (depends on: security)
  - storage (depends on: network, security)

Layer 4 (Parallel Execution):
  - database-rds (depends on: network, security, secrets)
  - authentication (depends on: security)

Layer 5 (Parallel Execution):
  - compute-ec2 (depends on: network, security)
  - compute-lambda (depends on: network, security)
  - services-ecs (depends on: network, security, storage)

Layer 6 (Sequential Execution):
  - monitoring (depends on: all previous stacks)
```

### Dependency Validation

**Pre-Deployment Validation:**

**1. Existence Validation:**
```python
# Verify all declared dependencies exist
for stack in stacks:
    for dep in stack.dependencies:
        if dep not in stack_names:
            raise MissingDependencyError(f"{stack} depends on {dep} which doesn't exist")
```

**2. Circular Dependency Detection:**
```python
# Detect cycles using DFS
visited = set()
rec_stack = set()

def detect_cycle(node):
    visited.add(node)
    rec_stack.add(node)

    for neighbor in graph[node]:
        if neighbor not in visited:
            if detect_cycle(neighbor):
                return True
        elif neighbor in rec_stack:
            raise CircularDependencyError(f"Cycle: {node} -> {neighbor}")

    rec_stack.remove(node)
    return False
```

**3. Cross-Stack Reference Validation:**
```python
# Validate ${stack.output} references
for stack in stacks:
    for placeholder in extract_placeholders(stack.config):
        ref_stack, ref_output = parse_placeholder(placeholder)

        # Verify referenced stack exists
        if ref_stack not in stacks:
            raise InvalidReferenceError(f"{stack} references non-existent {ref_stack}")

        # Verify output exists in template (template-first validation)
        if ref_output not in templates[ref_stack].outputs:
            raise InvalidOutputError(f"{ref_stack} doesn't export {ref_output}")
```

**4. Enablement Validation:**
```python
# Verify all dependencies are enabled
for stack in enabled_stacks:
    for dep in stack.dependencies:
        if dep not in enabled_stacks:
            raise DisabledDependencyError(f"{stack} depends on disabled {dep}")
```

### Dependency Visualization

**Command:**
```bash
python -m cloud_cli.main visualize-dependencies D1BRV40 --output deps.png
```

**Output:**
```
        dns
         |
      network
       /   \
   security  \
   /  |  \    \
secrets |  storage
   \    |    /
  database-rds
```

---

## Cross-Stack Dependencies (Complete Workflow)

### Complete Cross-Stack Reference Workflow

**Step 1: Define Output in Stack Template**
```yaml
# tools/templates/config/network.yaml
name: network
parameters:
  outputs:
    vpcId:
      type: string
      description: "VPC ID for cross-stack references"
    privateSubnetIds:
      type: array
      description: "Private subnet IDs"
```

**Step 2: Implement Output in Stack Code**
```typescript
// stacks/network/src/index.ts
import * as aws from "@pulumi/aws";

const vpc = new aws.ec2.Vpc("vpc", {
    cidrBlock: vpcCidr,
    // ... configuration
});

const privateSubnets = azs.map((az, i) =>
    new aws.ec2.Subnet(`private-${az}`, {
        vpcId: vpc.id,
        // ... configuration
    })
);

// Export outputs as declared in template
export const vpcId = vpc.id;
export const privateSubnetIds = privateSubnets.map(s => s.id);
```

**Step 3: Validate Stack Code (Template-First Validation)**
```bash
python -m cloud_cli.main validate-stack network

# Output:
# ✓ vpcId: declared in template, exported in code
# ✓ privateSubnetIds: declared in template, exported in code
# Result: PASSED
```

**Step 4: Reference Output in Dependent Stack Template**
```yaml
# tools/templates/config/security.yaml
name: security
parameters:
  inputs:
    vpcId:
      type: string
      required: true
      description: "VPC ID from network stack"

dependencies:
  - network  # Explicit dependency declaration
```

**Step 5: Configure Reference in Deployment Manifest**
```yaml
# deploy/D1BRV40/Deployment_Manifest.yaml
stacks:
  network:
    enabled: true
    config:
      dev:
        vpcCidr: "10.0.0.0/16"

  security:
    enabled: true
    config:
      dev:
        vpcId: "${network.vpcId}"  # Runtime placeholder
```

**Step 6: Generated Configuration File**
```yaml
# deploy/D1BRV40/config/security.dev.yaml
security:vpcId: "${network.vpcId}"  # Placeholder preserved
```

**Step 7: Runtime Resolution During Deployment**
```python
# PlaceholderResolver execution
from cloud_core.runtime import PlaceholderResolver
from cloud_core.pulumi import PulumiWrapper

resolver = PlaceholderResolver()
pulumi = PulumiWrapper()

# Read config file
config = load_yaml("deploy/D1BRV40/config/security.dev.yaml")

# Detect placeholder: ${network.vpcId}
placeholders = resolver.detect_placeholders(config)

# Resolve placeholder
for placeholder in placeholders:
    stack_name = "network"
    output_name = "vpcId"

    # Query Pulumi state
    value = pulumi.get_stack_output(
        stack="D1BRV40-network-dev",
        output=output_name
    )
    # Returns: "vpc-0abc123def456"

    # Replace placeholder
    config = resolver.replace(config, placeholder, value)

# Write resolved config
write_yaml("deploy/D1BRV40/config/security.dev.yaml.resolved", config)
```

**Step 8: Pulumi Execution**
```bash
# Executed by ExecutionEngine
pulumi up \
  --stack D1BRV40-security-dev \
  --config-file deploy/D1BRV40/config/security.dev.yaml.resolved \
  --cwd stacks/security/src
```

**Step 9: Stack Code Receives Resolved Value**
```typescript
// stacks/security/src/index.ts
const config = new pulumi.Config();
const vpcId = config.require("vpcId");
// Receives: "vpc-0abc123def456" (resolved value, not placeholder)

// Use the value
const securityGroup = new aws.ec2.SecurityGroup("sg", {
    vpcId: vpcId,  // Actual VPC ID from network stack
    // ... configuration
});
```

### Cross-Stack Reference Patterns

**Single Value Reference:**
```yaml
security:
  config:
    dev:
      vpcId: "${network.vpcId}"
```

**Array Reference:**
```yaml
compute-ec2:
  config:
    dev:
      subnetIds: "${network.privateSubnetIds}"
```

**Multiple References:**
```yaml
database-rds:
  config:
    dev:
      vpcId: "${network.vpcId}"
      subnetIds: "${network.privateSubnetIds}"
      securityGroupId: "${security.dbSecurityGroupId}"
      kmsKeyArn: "${secrets.kmsKeyArn}"
```

**Nested Object Reference:**
```yaml
application:
  config:
    dev:
      database:
        endpoint: "${database-rds.dbEndpoint}"
        port: "${database-rds.dbPort}"
        name: "${database-rds.dbName}"
```

### Cross-Stack Reference Benefits

**Type Safety:**
- Output types declared in enhanced templates
- Validation ensures correct types

**Early Validation:**
- Template-first validation catches missing outputs
- Dependency resolution ensures correct order

**Automatic Resolution:**
- PlaceholderResolver handles all queries
- No manual StackReference code needed

**Clear Dependencies:**
- Explicit template dependencies
- Implicit dependencies from placeholders

**Debugging:**
- Clear error messages for missing outputs
- Validation before deployment

---

## Runtime Value Resolution

### Runtime Resolution System

The PlaceholderResolver (`cloud_core.runtime.placeholder_resolver`) resolves dynamic values during deployment execution.

**Resolution Types:**
1. Cross-stack references: `${stack.output}`
2. AWS API queries: `${aws.query.params}`
3. Calculations: `${calculate.type.params}`
4. Environment variables: `${env.VAR_NAME}`

### Placeholder Syntax

**Format:**
```yaml
${<type>.<parameters>}
# or
{{<type>.<parameters>}}
```

**Cross-Stack References:**
```yaml
vpcId: "${network.vpcId}"
subnets: "${network.privateSubnetIds}"
endpoint: "${database.dbEndpoint}"
```

**AWS Queries:**
```yaml
amiId: "${aws.latestAmi.amazonLinux2.x86_64}"
zones: "${aws.availabilityZones.us-east-1}"
parameter: "${aws.ssm./myapp/database/password}"
```

**Calculations:**
```yaml
timestamp: "${calculate.timestamp.iso8601}"
password: "${calculate.password.32}"
uuid: "${calculate.uuid}"
```

**Environment Variables:**
```yaml
apiKey: "${env.API_KEY}"
region: "${env.AWS_REGION}"
```

### Resolution Process

**Process Flow:**
```python
class PlaceholderResolver:
    def resolve(self, config: Dict, context: DeploymentContext) -> Dict:
        """Resolve all placeholders in configuration."""

        # 1. Detect placeholders
        placeholders = self.detect_placeholders(config)

        # 2. Group by type
        cross_stack = [p for p in placeholders if p.type == 'stack']
        aws_queries = [p for p in placeholders if p.type == 'aws']
        calculations = [p for p in placeholders if p.type == 'calculate']
        env_vars = [p for p in placeholders if p.type == 'env']

        # 3. Resolve in order (respecting dependencies)
        for placeholder in cross_stack:
            value = self._resolve_cross_stack(placeholder, context)
            config = self._replace(config, placeholder, value)

        for placeholder in aws_queries:
            value = self._resolve_aws_query(placeholder, context)
            config = self._replace(config, placeholder, value)

        for placeholder in calculations:
            value = self._resolve_calculation(placeholder, context)
            config = self._replace(config, placeholder, value)

        for placeholder in env_vars:
            value = self._resolve_env_var(placeholder, context)
            config = self._replace(config, placeholder, value)

        return config
```

### AWS Query Resolution

**Latest AMI Query:**
```yaml
# Placeholder
amiId: "${aws.latestAmi.amazonLinux2.x86_64.us-east-1}"

# Resolution
import boto3
ec2 = boto3.client('ec2', region_name='us-east-1')
response = ec2.describe_images(
    Owners=['amazon'],
    Filters=[
        {'Name': 'name', 'Values': ['amzn2-ami-hvm-*-x86_64-gp2']},
        {'Name': 'state', 'Values': ['available']}
    ]
)
latest = sorted(response['Images'], key=lambda x: x['CreationDate'])[-1]
ami_id = latest['ImageId']  # ami-0abc123456def7890
```

**Availability Zones Query:**
```yaml
# Placeholder
zones: "${aws.availabilityZones.us-east-1}"

# Resolution
ec2 = boto3.client('ec2', region_name='us-east-1')
response = ec2.describe_availability_zones(
    Filters=[{'Name': 'state', 'Values': ['available']}]
)
zones = [z['ZoneName'] for z in response['AvailabilityZones']]
# ['us-east-1a', 'us-east-1b', 'us-east-1c', ...]
```

**SSM Parameter Query:**
```yaml
# Placeholder
password: "${aws.ssm./myapp/database/password}"

# Resolution
ssm = boto3.client('ssm', region_name='us-east-1')
response = ssm.get_parameter(
    Name='/myapp/database/password',
    WithDecryption=True
)
password = response['Parameter']['Value']
```

### Calculation Resolution

**Timestamp:**
```yaml
# Placeholder
deployedAt: "${calculate.timestamp.iso8601}"

# Resolution
from datetime import datetime
timestamp = datetime.utcnow().isoformat() + 'Z'
# "2025-10-29T14:30:00Z"
```

**Random Password:**
```yaml
# Placeholder
password: "${calculate.password.32}"

# Resolution
import secrets
import string
chars = string.ascii_letters + string.digits + string.punctuation
password = ''.join(secrets.choice(chars) for _ in range(32))
# "aB3$xY9...32 characters"
```

**UUID:**
```yaml
# Placeholder
resourceId: "${calculate.uuid}"

# Resolution
import uuid
resource_id = str(uuid.uuid4())
# "550e8400-e29b-41d4-a716-446655440000"
```

---

## Deployment Orchestration

### Orchestration Engine

The ExecutionEngine (`cloud_core.orchestrator.execution_engine`) orchestrates stack deployment with layer-based parallel execution and smart skip logic.

**Components:**
- **DependencyResolver**: Builds dependency graph, detects cycles
- **LayerCalculator**: Groups stacks into execution layers
- **ExecutionEngine**: Executes stacks with parallelization
- **SkipDetector**: Identifies unchanged stacks
- **PlaceholderResolver**: Resolves runtime placeholders
- **PulumiWrapper**: Executes Pulumi commands

### Execution Planning

**Planning Process:**
```python
class ExecutionEngine:
    def plan(self, deployment: Deployment, environment: str) -> ExecutionPlan:
        """Create execution plan for deployment."""

        # 1. Load enabled stacks
        stacks = deployment.get_enabled_stacks(environment)

        # 2. Resolve dependencies
        resolver = DependencyResolver()
        graph = resolver.build_graph(stacks)
        resolver.detect_cycles(graph)

        # 3. Calculate layers
        calculator = LayerCalculator()
        layers = calculator.calculate_layers(graph)

        # 4. Detect unchanged stacks
        detector = SkipDetector()
        unchanged = detector.detect_unchanged(stacks, environment)

        # 5. Create execution plan
        plan = ExecutionPlan()
        for layer_num, layer_stacks in enumerate(layers):
            layer = Layer(number=layer_num)
            for stack in layer_stacks:
                if stack in unchanged:
                    layer.add_task(SkipTask(stack))
                else:
                    layer.add_task(DeployTask(stack))
            plan.add_layer(layer)

        return plan
```

### Smart Skip Logic

**Change Detection:**
```python
class SkipDetector:
    def detect_unchanged(self, stacks: List[Stack], env: str) -> Set[Stack]:
        """Detect stacks that haven't changed since last deployment."""
        unchanged = set()

        for stack in stacks:
            # 1. Check config changes
            current_config = self._load_config(stack, env)
            last_config = self._load_last_deployed_config(stack, env)
            if current_config != last_config:
                continue  # Config changed

            # 2. Check code changes
            current_hash = self._hash_stack_code(stack)
            last_hash = self._load_last_deployed_hash(stack, env)
            if current_hash != last_hash:
                continue  # Code changed

            # 3. Check dependency changes
            if any(dep not in unchanged for dep in stack.dependencies):
                continue  # Dependency changed

            # 4. Check template changes
            current_template = self._load_template(stack)
            last_template = self._load_last_template(stack, env)
            if current_template != last_template:
                continue  # Template changed

            # No changes detected
            unchanged.add(stack)

        return unchanged
```

**Skip Benefits:**
- 70-90% time savings for incremental deployments
- Reduced AWS API calls
- Lower costs
- Faster iteration

### Parallel Execution

**Layer-Based Parallelization:**
```python
class ExecutionEngine:
    async def execute(self, plan: ExecutionPlan) -> ExecutionResult:
        """Execute plan with parallel execution within layers."""
        results = []

        for layer in plan.layers:
            # Execute all tasks in layer in parallel
            layer_tasks = []
            for task in layer.tasks:
                if isinstance(task, SkipTask):
                    layer_tasks.append(self._skip_stack(task.stack))
                elif isinstance(task, DeployTask):
                    layer_tasks.append(self._deploy_stack(task.stack))

            # Wait for all tasks in layer to complete
            layer_results = await asyncio.gather(*layer_tasks)
            results.extend(layer_results)

            # Stop if any task failed
            if any(r.failed for r in layer_results):
                break

        return ExecutionResult(results)
```

### Real-Time Progress Monitoring

**WebSocket Event Stream:**
```python
class ProgressMonitor:
    def __init__(self, websocket: WebSocket):
        self.ws = websocket

    async def on_deployment_started(self, deployment_id: str):
        await self.ws.send_json({
            'event': 'deployment_started',
            'deployment_id': deployment_id,
            'timestamp': datetime.utcnow().isoformat()
        })

    async def on_layer_started(self, layer: int, total: int):
        await self.ws.send_json({
            'event': 'layer_started',
            'layer': layer,
            'total_layers': total
        })

    async def on_stack_started(self, stack: str):
        await self.ws.send_json({
            'event': 'stack_started',
            'stack': stack
        })

    async def on_resource_created(self, stack: str, resource: str):
        await self.ws.send_json({
            'event': 'resource_created',
            'stack': stack,
            'resource': resource
        })

    async def on_stack_completed(self, stack: str, duration: float):
        await self.ws.send_json({
            'event': 'stack_completed',
            'stack': stack,
            'duration_seconds': duration
        })
```

---

## State Management

### Pulumi Cloud State Architecture

**State Organization:**
```
Pulumi Cloud
├── Organization: CompanyA
│   ├── Project: ecommerce               # Business project
│   │   ├── Stack: D1BRV40-network-dev   # Full context in name
│   │   │   ├── State Version: 1
│   │   │   ├── State Version: 2
│   │   │   └── State Version: 3 (current)
│   │   ├── Stack: D1BRV40-network-stage
│   │   ├── Stack: D1BRV40-network-prod
│   │   ├── Stack: D1BRV40-security-dev
│   │   └── ... (all deployment stacks)
│   └── Project: analytics
│       └── Stack: D1BRV50-network-dev
└── Organization: CompanyB
    └── Project: mobile
        └── Stack: D1BRV45-network-dev
```

**State Management Benefits:**
- Logical grouping by business project
- Clear deployment identification
- Version history preserved
- Point-in-time recovery
- Automatic locking
- Encrypted at rest

### State Operations

**State Initialization:**
```python
# Performed by PulumiWrapper
class PulumiWrapper:
    def init_stack(self, stack_name: str, project: str):
        """Initialize Pulumi stack."""
        subprocess.run([
            'pulumi', 'stack', 'init', stack_name,
            '--org', 'CompanyA',
            '--project', project
        ])
```

**State Query:**
```python
def get_stack_output(self, stack: str, output: str) -> str:
    """Get output value from Pulumi state."""
    result = subprocess.run([
        'pulumi', 'stack', 'output', output,
        '--stack', stack
    ], capture_output=True, text=True)
    return result.stdout.strip()
```

**State Export:**
```python
def export_state(self, stack: str, output_file: str):
    """Export stack state for backup."""
    result = subprocess.run([
        'pulumi', 'stack', 'export',
        '--stack', stack
    ], capture_output=True, text=True)

    with open(output_file, 'w') as f:
        f.write(result.stdout)
```

### State Locking

**Automatic Locking:**
- Pulumi Cloud automatically locks state during operations
- Prevents concurrent modifications
- Lock released on completion or timeout (10 minutes)
- Prevents race conditions and state corruption

**Lock Behavior:**
```
User A: python -m cloud_cli.main deploy D1BRV40 --environment dev
  └─▶ Acquires lock on D1BRV40-network-dev

User B: python -m cloud_cli.main deploy D1BRV40 --environment dev
  └─▶ Error: State locked by User A
      Waiting for lock release... (timeout: 10 minutes)
```

### State Backup and Recovery

**Automatic Backups:**
- Pulumi Cloud maintains complete version history
- Every deployment creates new state version
- Previous versions retained indefinitely
- Point-in-time recovery supported

**Manual Backup:**
```bash
# Export all stack states
python -m cloud_cli.main export-state D1BRV40 --all-environments \
  --output backups/D1BRV40-backup-20251029.tar.gz

# Export single stack
python -m cloud_cli.main export-state D1BRV40 --stack network --environment dev \
  --output backups/network-dev-backup.json
```

**State Recovery:**
```bash
# Restore from backup
python -m cloud_cli.main import-state D1BRV40 --stack network --environment dev \
  --input backups/network-dev-backup.json
```

---

## CLI Tool Specification

### CLI Architecture

**Implementation:**
- **Language**: Python 3.11+
- **Framework**: Typer 0.9+
- **Structure**: Commands in `cloud_cli.commands/`
- **Core Integration**: Direct `cloud_core` imports
- **Entry Point**: `python -m cloud_cli.main`

### Command Categories

**1. Deployment Lifecycle**
- `init` - Initialize new deployment from template
- `deploy` - Deploy all enabled stacks to environment
- `deploy-stack` - Deploy single stack
- `destroy` - Destroy all stacks in environment
- `destroy-stack` - Destroy single stack
- `rollback` - Rollback to previous state version
- `status` - Show deployment status
- `list` - List all deployments

**2. Environment Management**
- `enable-environment` - Enable environment for deployment
- `disable-environment` - Disable environment
- `list-environments` - List environments and their status

**3. Stack Management**
- `register-stack` - Register new stack (with `--auto-extract`)
- `update-stack` - Update stack template
- `unregister-stack` - Remove stack from registry
- `list-stacks` - List all registered stacks
- `discover` - Discover stacks in stacks/ directory

**4. Validation**
- `validate` - Validate deployment manifest
- `validate-stack` - Validate stack code against template
- `validate-template` - Validate template syntax
- `validate-dependencies` - Validate dependency graph
- `validate-aws` - Validate AWS credentials and permissions
- `validate-pulumi` - Validate Pulumi setup

**5. Template Management**
- `list-templates` - List available manifest templates
- `show-template` - Display template contents
- `create-template` - Create custom template
- `update-template` - Update existing template

**6. Logging and Monitoring**
- `logs` - View deployment logs
- `follow` - Follow deployment progress in real-time
- `export-state` - Export Pulumi state for backup

### Command Examples

**Initialize Deployment:**
```bash
python -m cloud_cli.main init \
  --org "Company-A" \
  --project "ecommerce" \
  --template default \
  --region us-east-1
```

**Deploy to Environment:**
```bash
python -m cloud_cli.main deploy D1BRV40 --environment dev
```

**Validate Stack Code:**
```bash
python -m cloud_cli.main validate-stack network --strict
```

**Register Stack with Auto-Extraction:**
```bash
python -m cloud_cli.main register-stack api-gateway --auto-extract
```

**View Status:**
```bash
python -m cloud_cli.main status D1BRV40 --all-environments
```

For complete command reference, see CLI_Commands_Reference.3.1.md.

---

## REST API Specification

### API Architecture

**Technology Stack:**
- **Framework**: FastAPI (Python) for alignment with core library
- **Authentication**: AWS Cognito + JWT tokens
- **Authorization**: Role-Based Access Control (RBAC)
- **Real-Time**: WebSocket for deployment progress
- **Documentation**: Auto-generated OpenAPI 3.0
- **Deployment**: AWS Lambda + API Gateway

**API Endpoints:**
```
/api/v1/
├── /auth
│   ├── POST /login
│   ├── POST /logout
│   └── POST /refresh-token
├── /deployments
│   ├── GET    /deployments
│   ├── POST   /deployments
│   ├── GET    /deployments/{id}
│   ├── PUT    /deployments/{id}
│   ├── DELETE /deployments/{id}
│   ├── POST   /deployments/{id}/deploy
│   └── GET    /deployments/{id}/status
├── /stacks
│   ├── GET    /stacks
│   ├── POST   /stacks/register
│   ├── GET    /stacks/{name}
│   └── POST   /stacks/{name}/validate
├── /templates
│   ├── GET    /templates
│   └── GET    /templates/{name}
└── /websocket
    └── WS     /progress/{deployment_id}
```

For complete API specification, see REST_API_Documentation.3.1.md.

---

## Verification and Validation

### Validation System

The platform includes comprehensive validation at every stage:

**1. Enhanced Template Validation**
- YAML syntax validation
- Parameter structure validation (`inputs` and `outputs`)
- Type specification validation
- Required field validation
- Dependency declaration validation

**2. Stack Code Validation (Template-First)**
- Input usage validation (StackCodeValidator)
- Output export validation
- Config method type matching
- Strict mode for zero-tolerance consistency

**3. Manifest Validation**
- Schema compliance
- Stack existence verification
- Dependency graph validation
- Circular dependency detection
- Configuration completeness

**4. Pre-Deployment Validation**
- AWS credentials verification
- Pulumi authentication check
- Stack code availability
- Dependency deployment verification
- Permission validation

**5. Runtime Validation**
- Placeholder syntax validation
- Cross-stack output existence
- AWS resource availability
- Dynamic query execution

### Validation Commands

```bash
# Validate everything
python -m cloud_cli.main validate D1BRV40 --full

# Validate stack code
python -m cloud_cli.main validate-stack network --strict

# Validate dependencies
python -m cloud_cli.main validate-dependencies D1BRV40

# Validate AWS setup
python -m cloud_cli.main validate-aws --region us-east-1
```

---

## Security and Access Control

### Authentication

**CLI Authentication:**
- AWS credentials from `~/.aws/credentials` or environment
- Pulumi tokens from `~/.pulumi/credentials.json`
- No additional authentication for local operations

**API Authentication:**
- AWS Cognito user pools
- JWT token-based authentication
- Token refresh mechanism
- MFA support

### Authorization (RBAC)

**Roles:**
- **Admin**: Full access to all operations
- **Developer**: Deploy to dev/stage, read prod
- **Operator**: Deploy to all environments, no delete
- **Viewer**: Read-only access

**Permission Matrix:**
```
Operation              | Admin | Developer | Operator | Viewer |
-----------------------|-------|-----------|----------|--------|
Init Deployment        |   ✓   |     ✓     |    ✓     |   ✗   |
Deploy to Dev          |   ✓   |     ✓     |    ✓     |   ✗   |
Deploy to Stage        |   ✓   |     ✓     |    ✓     |   ✗   |
Deploy to Prod         |   ✓   |     ✗     |    ✓     |   ✗   |
Destroy Dev/Stage      |   ✓   |     ✓     |    ✗     |   ✗   |
Destroy Prod           |   ✓   |     ✗     |    ✗     |   ✗   |
View Status            |   ✓   |     ✓     |    ✓     |   ✓   |
Register Stack         |   ✓   |     ✗     |    ✗     |   ✗   |
```

### Secrets Management

**Sensitive Data Storage:**
- AWS credentials: `~/.aws/credentials`
- Pulumi tokens: `~/.pulumi/credentials.json`
- Database passwords: AWS Secrets Manager
- API keys: AWS Secrets Manager
- SSH keys: AWS Secrets Manager

**Best Practices:**
- Never commit secrets to version control
- Use AWS Secrets Manager for runtime secrets
- Rotate credentials regularly
- Use IAM roles instead of static credentials
- Encrypt sensitive data at rest and in transit

---

## Monitoring and Logging

### Logging Architecture

**Log Types:**

**1. Initialization Logs**
```
deploy/D1BRV40/logs/init.log
- Template loading
- Manifest generation
- Config file generation
- Validation results
```

**2. Deployment Logs**
```
deploy/D1BRV40/logs/deploy-dev-20251029-143000.log
- Execution plan
- Stack-by-stack progress
- Resource creation details
- Errors and warnings
- Final summary
```

**3. Stack-Specific Logs**
```
deploy/D1BRV40/logs/network-dev-20251029-143500.log
- Pulumi output
- Resource-level details
- Timing information
```

### Monitoring

**Metrics:**
- Deployment success/failure rate
- Average deployment time per stack
- Skip rate (efficiency metric)
- Resource creation success rate
- Error frequency by type

**Tools:**
- CloudWatch for AWS resource metrics
- CloudWatch Logs for application logs
- CloudWatch Dashboards for visualization
- SNS for alerting

---

## Known Issues and Future Work

### Known Issues

**1. Auto-Extraction Limitations**
- Cannot extract meaningful parameter descriptions
- Limited to standard Pulumi Config patterns
- **Workaround**: Manual template refinement

**2. Public Subnet Configuration**
- Public subnet configuration may need refinement
- **Workaround**: Manual configuration adjustment

**3. Database Credentials Management**
- Database credentials need better secrets integration
- **Workaround**: Manual secrets rotation

### Future Enhancements (v5.0+)

**1. REST API with FastAPI**
- Direct core library integration
- No subprocess overhead
- Enhanced performance
- Estimated effort: 8-10 weeks

**2. Enhanced Auto-Extraction**
- Extract JSDoc comments for descriptions
- Detect validation rules from patterns
- Infer parameter relationships
- Estimated effort: 4-6 weeks

**3. AI-Assisted Template Generation**
- Use LLM for meaningful descriptions
- Suggest validation rules
- Recommend dependencies
- Estimated effort: 6-8 weeks

**4. Multi-Region Support**
- Deploy across multiple regions
- Global load balancing
- Cross-region replication
- Estimated effort: 6-8 weeks

**5. Cost Optimization Engine**
- Automatic rightsizing recommendations
- Unused resource detection
- Cost forecasting
- Estimated effort: 4-6 weeks

---

## Implementation Phases

### Phase 1: Foundation (Weeks 1-2)
- Enhanced template system with structured parameters
- Python core library structure
- Pulumi native config generation
- Deployment initialization

### Phase 2: Auto-Extraction and Validation (Weeks 3-4)
- ParameterExtractor implementation
- TypeScriptParser implementation
- StackCodeValidator implementation
- CLI validation commands

### Phase 3: Runtime Resolution (Weeks 5-6)
- PlaceholderResolver with ${...} syntax
- Cross-stack output queries
- AWS API integration
- Calculation engine

### Phase 4: Smart Orchestration (Weeks 7-8)
- DependencyResolver
- LayerCalculator
- ExecutionEngine
- Smart skip logic

### Phase 5: Multi-Environment & WebSocket (Weeks 9-10)
- Multi-environment manifest
- Environment management commands
- WebSocket server
- Real-time event publishing

### Phase 6: Python CLI (Weeks 11-12)
- Typer-based CLI
- Core library integration
- All 25+ commands
- Interactive modes

### Phase 7: REST API (Weeks 13-14)
- FastAPI implementation
- Direct core library integration
- Authentication/authorization
- WebSocket integration

### Phase 8: Verification & Testing (Weeks 15-16)
- Comprehensive testing
- Documentation finalization
- Bug fixes
- Production readiness

**Total: 16 weeks**

---

## Migration from Architecture 3.1

### Migration Overview

Migrate from TypeScript CLI to Python v4.1 with enhanced templates, auto-extraction, template-first validation, and Pulumi native config.

### Migration Steps

**Step 1: Backup**
```bash
# Backup deployments and state
cp -r ./cloud/deploy/* ./backups/deploy/
python -m cloud_cli.main export-all-state --output backups/state.tar.gz
```

**Step 2: Install v4.1**
```bash
# Install core library
cd ./cloud/tools/core
python3 -m venv venv
source venv/bin/activate
pip install -e .

# Install CLI
cd ../cli
pip install -e .
```

**Step 3: Migrate Templates**
```bash
# Auto-extract enhanced templates
python -m cloud_cli.main migrate-templates --from-v3.1 --auto-extract
```

**Step 4: Update Config Format**
```bash
# Convert to Pulumi native format and move to config/
python -m cloud_cli.main migrate-config-format --deployment D1BRV40
```

**Step 5: Validate**
```bash
# Run all validations
python -m cloud_cli.main validate D1BRV40
python -m cloud_cli.main validate-stack --all
```

**Step 6: Test**
```bash
# Test deployment in preview mode
python -m cloud_cli.main deploy D1BRV40 --environment dev --preview
```

### Migration Checklist

- [ ] Backup deployments and state
- [ ] Install Python core library
- [ ] Install Python CLI
- [ ] Migrate templates to enhanced format
- [ ] Run auto-extraction for all stacks
- [ ] Update config to Pulumi native format
- [ ] Move configs to config/ subdirectory
- [ ] Update placeholder syntax
- [ ] Run template-first validation
- [ ] Test deployment in preview mode
- [ ] Update documentation
- [ ] Train team on new features

---

## Conclusion

The Cloud Infrastructure Orchestration Platform v4.1 provides enterprise-grade infrastructure management with Python-based architecture, enhanced templates, auto-extraction, template-first validation, and comprehensive deployment orchestration.

### Key Achievements

**Architectural Excellence:**
- Core/CLI separation for maintainability
- Python implementation with 393+ core tests, 38+ CLI tests
- Modular design with clear responsibilities

**Enhanced Templates:**
- Structured parameters with types and defaults
- Foundation for auto-extraction and validation
- Better documentation and discoverability

**Auto-Extraction:**
- 80-90% reduction in template creation time
- Automatic code-template synchronization
- Reduced manual errors

**Template-First Validation:**
- Prevents template-code drift
- Early error detection
- Enforces architectural standards

**Operational Excellence:**
- Smart skip logic (70-90% time savings)
- Layer-based parallel execution
- Real-time progress monitoring
- Comprehensive validation at every stage

### Implementation Timeline

16 weeks for complete v4.1 implementation covering foundation, auto-extraction, validation, orchestration, CLI, API, and testing.

### Next Steps

1. Review and approve architecture
2. Begin Phase 1 implementation
3. Iterative development with testing
4. Staged rollout to production
5. Team training on new features

---

**Document Version:** 4.1
**Platform Version:** cloud-0.7
**Last Updated:** 2025-10-29
**Status:** Complete Implementation Blueprint
**Test Coverage:** 393+ core tests, 38+ CLI tests
**Implementation Status:** ✅ Architecture Complete

**End of Multi-Stack-Architecture-4.1 Document**
