# Directory Structure Diagram v4.5

**Version:** 4.5
**Date:** 2025-10-30
**Status:** Production Ready
**Architecture**: Aligned with v4.0 authoritative documents, enhanced in v4.5

**Changes from v3.1 to v4.1:**
- Updated to align with v4.0 authoritative documents
- Clarified Python CLI implementation (cloud_cli)
- Added core/CLI architecture split documentation
- Emphasized config/ subdirectory for deployment configs
- Clarified index.ts at stack root (not in src/)
- Added enhanced template structure
- Updated to reflect Pulumi native config format
- Added cross-stack dependency examples
- Documented auto-extraction and validation systems

**Changes from v4.1 to v4.5:**
- Added Dynamic Pulumi.yaml Management system in core/pulumi
- All deployment templates default to disabled stacks
- Added Addendum_Dynamic_Pulumi_YAML_Implementation.4.1.md documentation
- Updated pulumi_wrapper.py with deployment_context() method
- Enhanced PulumiWrapper with backup/restore functionality

---

## Directory Structure Diagram Reference, for Multi-Stack Architecture version 4.5

<directory_structure>
```
./cloud/                                                # Cloud Platform Root
│
├── .claude/                                            # Claude Code Configuration
│   ├── commands/
│   ├── memory/
│   └── skills/
│
├── tools/                                              # Platform Tools
│   │
│   ├── docs/                                           # Architecture Documentation
│   │   ├── Multi_Stack_Architecture.4.5.md             # Main Architecture Document (v4.5)
│   │   ├── Directory_Structure_Diagram.4.5.md          # This document (v4.5)
│   │   ├── Deployment_Manifest_Specification.4.5.md    # Manifest spec (v4.5)
│   │   ├── Addendum_Dynamic_Pulumi_YAML_Implementation.4.1.md  # Dynamic Pulumi.yaml (NEW v4.5)
│   │   ├── README.md                                   # Documentation index (v4.1)
│   │   ├── INSTALL.md                                  # Installation guide (v4.1)
│   │   │
│   │   ├── Complete_Stack_Management_Guide_v4.md       # 🔖 Authoritative v4
│   │   ├── Stack_Parameters_and_Registration_Guide_v4.md  # 🔖 Authoritative v4
│   │   ├── Complete_Guide_Templates_Stacks_Config_and_Registration_v4.md  # 🔖 Authoritative v4
│   │   ├── Implementation_Compliance_Report_v4.md
│   │   │
│   │   ├── CLI_Commands_Reference.3.1.md
│   │   ├── CLI_Commands_Quick_Reference.3.1.md
│   │   ├── CLI_Testing_Guide.3.1.md
│   │   ├── REST_API_Documentation.3.1.md
│   │   ├── REST_API_Quick_Reference.3.1.md
│   │   ├── REST_API_Testing_Guide.3.1.md
│   │   ├── Addendum_Platform_Code.3.1.md
│   │   ├── Addendum_Changes_From_2.3.3.1.md
│   │   ├── Addendum_Questions_Answers.3.1.md
│   │   ├── Addendum_Stack_Cloning.3.1.md
│   │   ├── Addendum_Verification_Architecture.3.1.md
│   │   ├── Addendum_Progress_Monitoring.3.1.md
│   │   └── Addendum_Statistics.3.1.md
│   │
│   ├── templates/                                      # Deployment Templates
│   │   │
│   │   ├── docs/                                       # Stack Markdown Templates
│   │   │   ├── Stack_Prompt_Main.md.template
│   │   │   ├── Stack_Prompt_Extra.md.template
│   │   │   ├── Stack_Definitions.md.template
│   │   │   ├── Stack_Resources.md.template
│   │   │   ├── Stack_History_Errors.md.template
│   │   │   ├── Stack_History_Fixes.md.template
│   │   │   └── Stack_History.md.template
│   │   │
│   │   ├── stack/                                      # Stack Pulumi Templates
│   │   │   ├── index.ts.template                       # Main entry point template
│   │   │   ├── src/
│   │   │   │   ├── component-example.ts.template       # Optional additional stack components
│   │   │   │   └── outputs.ts.template                 # Exported outputs template
│   │   │   ├── Pulumi.yaml.template                    # Stack metadata template
│   │   │   ├── package.json.template                   # NPM package template
│   │   │   └── tsconfig.json.template                  # TypeScript config template
│   │   │
│   │   ├── config/                                     # Stack Templates (Enhanced v4 Format)
│   │   │   ├── network.yaml                            # Network stack template
│   │   │   │   # Enhanced format with parameters.inputs and parameters.outputs
│   │   │   ├── dns.yaml                                # DNS stack template
│   │   │   ├── security.yaml                           # Security stack template
│   │   │   ├── secrets.yaml                            # Secrets stack template
│   │   │   ├── authentication.yaml                     # Authentication stack template
│   │   │   ├── storage.yaml                            # Storage stack template
│   │   │   ├── database-rds.yaml                       # Database stack template
│   │   │   ├── containers-images.yaml                  # Container images stack template
│   │   │   ├── containers-apps.yaml                    # Container apps stack template
│   │   │   ├── services-ecr.yaml                       # ECR service stack template
│   │   │   ├── services-ecs.yaml                       # ECS service stack template
│   │   │   ├── services-eks.yaml                       # EKS service stack template
│   │   │   ├── services-api.yaml                       # API Gateway stack template
│   │   │   ├── compute-ec2.yaml                        # EC2 stack template
│   │   │   ├── compute-lambda.yaml                     # Lambda stack template
│   │   │   └── monitoring.yaml                         # Monitoring stack template
│   │   │
│   │   ├── default/                                    # Deployment Manifest Templates
│   │   │   ├── default.yaml                            # Full platform template
│   │   │   ├── minimal.yaml                            # Minimal infrastructure
│   │   │   ├── microservices.yaml                      # Container-focused
│   │   │   └── data-platform.yaml                      # Data processing focus
│   │   │
│   │   └── custom/                                     # Organization-specific Custom Templates
│   │
│   ├── core/                                           # Core Business Logic Library (NEW v4)
│   │   ├── cloud_core/                                 # Python package
│   │   │   ├── __init__.py
│   │   │   ├── deployment/                             # Deployment Management
│   │   │   │   ├── config_generator.py                 # Generates Pulumi config files
│   │   │   │   ├── deployment_manager.py               # Deployment lifecycle
│   │   │   │   └── state_manager.py                    # State management
│   │   │   ├── orchestrator/                           # Orchestration Engine
│   │   │   │   ├── dependency_resolver.py              # Builds dependency graph
│   │   │   │   ├── execution_engine.py                 # Executes deployments
│   │   │   │   ├── layer_calculator.py                 # Calculates execution layers
│   │   │   │   └── orchestrator.py                     # Main orchestrator
│   │   │   ├── runtime/                                # Runtime Resolution
│   │   │   │   ├── placeholder_resolver.py             # Resolves ${...} and {{...}}
│   │   │   │   ├── stack_reference_resolver.py         # Reads Pulumi stack outputs
│   │   │   │   └── aws_query_resolver.py               # AWS API queries
│   │   │   ├── templates/                              # Template Management
│   │   │   │   ├── stack_template_manager.py           # Enhanced template manager
│   │   │   │   ├── template_manager.py                 # Deployment template manager
│   │   │   │   ├── template_renderer.py                # Template rendering
│   │   │   │   └── manifest_generator.py               # Generates manifests
│   │   │   ├── validation/                             # Validation System
│   │   │   │   ├── stack_code_validator.py             # Template-first validation
│   │   │   │   ├── manifest_validator.py               # Manifest validation
│   │   │   │   ├── dependency_validator.py             # Dependency validation
│   │   │   │   ├── pulumi_validator.py                 # Pulumi validation
│   │   │   │   └── aws_validator.py                    # AWS prerequisites
│   │   │   ├── pulumi/                                 # Pulumi Integration
│   │   │   │   ├── pulumi_wrapper.py                   # Pulumi CLI wrapper (v4.5: deployment_context())
│   │   │   │   ├── stack_operations.py                 # Stack operations
│   │   │   │   └── state_queries.py                    # State queries
│   │   │   └── utils/                                  # Utilities
│   │   │       ├── logger.py                           # Logging
│   │   │       └── deployment_id.py                    # ID generation
│   │   ├── tests/                                      # Core tests (393+ tests)
│   │   ├── setup.py
│   │   └── requirements.txt
│   │
│   ├── cli/                                            # CLI Tool (Python - NEW v4)
│   │   ├── src/
│   │   │   └── cloud_cli/                              # Python package
│   │   │       ├── __init__.py
│   │   │       ├── main.py                             # CLI entry point
│   │   │       ├── commands/                           # Command implementations
│   │   │       │   ├── stack_cmd.py                    # Stack commands (register, validate)
│   │   │       │   ├── deploy_cmd.py                   # Deployment commands
│   │   │       │   ├── template_cmd.py                 # Template commands
│   │   │       │   └── ...                             # Other command modules
│   │   │       └── parser/                             # Auto-Extraction System (NEW v4)
│   │   │           ├── parameter_extractor.py          # Extracts parameters from code
│   │   │           └── typescript_parser.py            # Parses TypeScript code
│   │   ├── tests/                                      # CLI tests
│   │   ├── setup.py
│   │   ├── requirements.txt
│   │   └── pyproject.toml
│   │
│   └── dev/                                            # Development & Planning Documents
│       └── ... (implementation plans, analysis docs)
│
├── stacks/                                             # Stack Implementations
│   ├── network/
│   │   ├── index.ts                                    # Main entry point (AT ROOT!)
│   │   ├── docs/
│   │   │   ├── Stack_Prompt_Main.md
│   │   │   ├── Stack_Prompt_Extra.md
│   │   │   ├── Stack_Definitions.md
│   │   │   ├── Stack_Resources.md
│   │   │   ├── Stack_History_Errors.md
│   │   │   ├── Stack_History_Fixes.md
│   │   │   └── Stack_History.md
│   │   ├── src/                                        # Optional component files
│   │   │   ├── vpc.ts                                  # VPC resources
│   │   │   ├── subnets.ts                              # Subnet resources
│   │   │   ├── nat.ts                                  # NAT Gateway resources
│   │   │   └── outputs.ts                              # Exported outputs
│   │   ├── Pulumi.yaml                                 # Stack metadata (minimal)
│   │   ├── package.json
│   │   └── tsconfig.json
│   │
│   ├── security/
│   │   ├── index.ts
│   │   ├── docs/
│   │   ├── src/
│   │   │   ├── security-groups.ts
│   │   │   ├── iam-roles.ts
│   │   │   └── kms.ts
│   │   ├── Pulumi.yaml
│   │   ├── package.json
│   │   └── tsconfig.json
│   │
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
│       └── (same structure as network stack)
│
└── deploy/                                             # Active Deployments
    ├── D1BRV40-CompanyA-ecommerce/                     # Deployment Example 1
    │   ├── deployment-manifest.yaml                    # Deployment configuration (YAML!)
    │   ├── config/                                     # Config subdirectory (v4!)
    │   │   ├── network.dev.yaml                        # Network dev config (Pulumi format)
    │   │   ├── network.stage.yaml                      # Network stage config
    │   │   ├── network.prod.yaml                       # Network prod config
    │   │   ├── security.dev.yaml
    │   │   ├── security.stage.yaml
    │   │   ├── security.prod.yaml
    │   │   └── ... (all enabled stacks × environments)
    │   └── logs/
    │       ├── init.log
    │       ├── D1BRV40-network-dev-20251009-143000.log
    │       ├── D1BRV40-security-dev-20251009-143500.log
    │       └── ... (stack deployment logs)
    │
    ├── D1BRV45-CompanyB-mobile/                        # Deployment Example 2
    │   ├── deployment-manifest.yaml
    │   ├── config/
    │   │   ├── network.dev.yaml
    │   │   ├── network.stage.yaml
    │   │   ├── network.prod.yaml
    │   │   └── ... (all enabled stacks × environments)
    │   └── logs/
    │       ├── init.log
    │       ├── D1BRV45-network-dev-20251010-091500.log
    │       └── ... (stack deployment logs)
    │
    └── D1BRV50-CompanyA-analytics/                     # Deployment Example 3
        ├── deployment-manifest.yaml
        ├── config/
        │   ├── network.dev.yaml
        │   ├── network.stage.yaml
        │   ├── network.prod.yaml
        │   └── ... (all enabled stacks × environments)
        └── logs/
            ├── init.log
            ├── D1BRV50-network-dev-20251011-101500.log
            └── ... (stack deployment logs)
```
</directory_structure>

---

## Key Directory Concepts

### Deployment Directory Naming Convention

**Format:** `<deployment-id>-<organization>-<project>/`

**Examples:**
- `D1BRV40-CompanyA-ecommerce/`
- `D1BRV45-CompanyB-mobile/`
- `D1BRV50-CompanyA-analytics/`

**Purpose:** This naming convention allows:
- Unique identification of each deployment
- Clear association with organization and project
- Easy filtering and grouping in file systems
- Alignment with Pulumi state organization

### Deployment Manifest Location

**Path:** `./cloud/deploy/<deployment-id>-<org>-<project>/deployment-manifest.yaml`

**Format:** YAML (not JSON!)

**Key Points:**
- The manifest is located **at the deployment root** (not in a `src/` subdirectory)
- Filename is `deployment-manifest.yaml` (hyphenated, not camelCase or underscored)
- Contains all environment and stack configurations

### Stack Configuration Files (v4 Format)

**Path:** `./cloud/deploy/<deployment-id>-<org>-<project>/config/<stack>.<environment>.yaml`

**Format:** Pulumi native format

**Examples:**
- `config/network.dev.yaml`
- `config/network.stage.yaml`
- `config/network.prod.yaml`
- `config/security.dev.yaml`

**Pulumi Native Format Example:**
```yaml
# config/network.dev.yaml
network:deploymentId: "D1BRV40"
network:organization: "CompanyA"
network:project: "ecommerce"
network:vpcCidr: "10.0.0.0/16"
network:availabilityZones: "2"
aws:region: "us-east-1"
```

**Key Changes from v3.1:**
- Files in `config/` subdirectory (not flat in deployment root)
- Pulumi native format: `stackname:key: "value"`
- All values are strings (Pulumi requirement)
- Complex types (arrays, objects) serialized as JSON strings

### Log Files

**Path:** `./cloud/deploy/<deployment-id>-<org>-<project>/logs/<deployment-id>-<stack>-<environment>-<timestamp>.log`

**Examples:**
- `logs/init.log` (initialization log)
- `logs/D1BRV40-network-dev-20251009-143000.log`
- `logs/D1BRV40-security-dev-20251009-143500.log`

---

## Template Structure Details

### Stack Markdown Templates (`tools/templates/docs/`)

These are templates for creating documentation for new stacks:
- `Stack_Prompt_Main.md.template` - Main prompt for stack generation
- `Stack_Prompt_Extra.md.template` - Additional requirements
- `Stack_Definitions.md.template` - Stack specifications
- `Stack_Resources.md.template` - Resource documentation
- `Stack_History_Errors.md.template` - Error tracking
- `Stack_History_Fixes.md.template` - Fix documentation
- `Stack_History.md.template` - Complete history

### Stack Pulumi Templates (`tools/templates/stack/`)

These are templates for creating new Pulumi stack implementations:
- `index.ts.template` - Main entry point (at stack root!)
- `src/component-example.ts.template` - Component example
- `src/outputs.ts.template` - Output definitions
- `Pulumi.yaml.template` - Stack metadata (minimal)
- `package.json.template` - NPM dependencies
- `tsconfig.json.template` - TypeScript configuration

### Stack Templates - Enhanced v4 Format (`tools/templates/config/`)

**NEW in v4:** Enhanced template format with structured parameter system

YAML files defining each stack's:
- **parameters.inputs** - Input parameters with types, defaults, validation
- **parameters.outputs** - Output declarations for cross-stack references
- **dependencies** - Stack dependencies
- **layer** - Execution layer
- Default configurations

**Enhanced Template Example:**
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
      description: "Private subnet IDs for RDS/ECS"

    publicSubnetIds:
      type: array
      description: "Public subnet IDs for ALB"

dependencies: []
layer: 1
```

### Deployment Manifest Templates (`tools/templates/default/`)

Pre-built deployment templates:
- `default.yaml` - Full platform (all 16 stacks)
- `minimal.yaml` - Basic infrastructure only
- `microservices.yaml` - Container-focused deployment
- `data-platform.yaml` - Data processing focus

---

## Core/CLI Architecture Split (NEW in v4)

### Two-Tier Architecture

**tools/core/** - Business Logic Library (`cloud_core`)
- Deployment management
- Orchestration engine
- Template system
- Validation system
- Pulumi integration
- Runtime resolution

**tools/cli/** - User Interface (`cloud_cli`)
- Command-line interface
- Command handlers
- User interaction
- Auto-extraction system (ParameterExtractor, TypeScriptParser)

### Key Modules

**Deployment Management:**
- `config_generator.py` - Generates Pulumi config files in native format
- `deployment_manager.py` - Manages deployment lifecycle
- `state_manager.py` - Pulumi state management

**Orchestration:**
- `dependency_resolver.py` - Builds dependency graph, detects cycles
- `layer_calculator.py` - Calculates execution layers
- `execution_engine.py` - Executes stacks in layers

**Runtime Resolution:**
- `placeholder_resolver.py` - Resolves `${...}` and `{{...}}` placeholders
- `stack_reference_resolver.py` - Reads Pulumi stack outputs
- `aws_query_resolver.py` - Queries AWS resources

**Templates:**
- `stack_template_manager.py` - Manages enhanced stack templates
- `template_manager.py` - Manages deployment templates
- `manifest_generator.py` - Generates deployment manifests

**Validation:**
- `stack_code_validator.py` - Template-first validation
- `manifest_validator.py` - Manifest schema validation
- `dependency_validator.py` - Dependency validation

**Auto-Extraction (NEW in v4):**
- `parameter_extractor.py` - Extracts parameters from TypeScript code
- `typescript_parser.py` - Parses stack code for Config calls

---

## Stack Structure Details

### Correct Stack Layout (v4)

```
stacks/<stack-name>/
├── index.ts                    # Main entry point (AT ROOT, not in src/)
├── src/                        # Optional component files
│   ├── vpc.ts                  # VPC creation logic
│   ├── subnets.ts              # Subnet creation logic
│   ├── nat.ts                  # NAT gateway logic
│   └── outputs.ts              # Output exports
├── docs/                       # Stack documentation
│   ├── Stack_Prompt_Main.md
│   ├── Stack_Definitions.md
│   └── ... (other docs)
├── Pulumi.yaml                 # Minimal metadata (name, runtime, description only)
├── package.json                # NPM dependencies
└── tsconfig.json               # TypeScript configuration
```

**Key Points:**
- `index.ts` is **at the root** of the stack directory
- `src/` directory contains optional component files
- `index.ts` imports from `./src/*` for modular organization
- `Pulumi.yaml` contains minimal metadata only (no config!)
- All deployment-specific config in deployment directories

---

## Directory Structure Changes from v2.3

```
Old (Architecture 2.3)                    New (Architecture 4.1)
────────────────────────────────────────────────────────────────────
./aws/deploy/                         →   ./cloud/deploy/
./admin/v2/                           →   ./cloud/tools/
./aws/build/<stack>/v2/src/     →   ./cloud/stacks/<stack>/
./admin/v2/docs/                      →   ./cloud/tools/docs/
./admin/v2/templates/                 →   ./cloud/tools/templates/

Deployment directories:
./deploy/D1BRV40/                     →   ./deploy/D1BRV40-CompanyA-ecommerce/

Manifest location:
(varied)                              →   ./deploy/<id>-<org>-<project>/deployment-manifest.yaml

Config files:
./deploy/<id>/*.yaml                  →   ./deploy/<id>/config/*.yaml

CLI implementation:
TypeScript (./tools/cli/src/index.ts) →   Python (./tools/cli/src/cloud_cli/main.py)
```

---

## Notes

- All paths shown are relative to the platform root (`./cloud/`)
- The `.claude/` directory contains Claude Code configuration and memory
- The `tools/dev/` directory contains implementation planning documents
- Stack implementations follow a consistent structure across all 16 stacks
- Each deployment is fully isolated in its own directory
- Log files use deployment ID and stack name for clear identification
- Template system allows for easy creation of new stacks and deployments
- **Python CLI** implementation (not TypeScript)
- **Core/CLI split** for better modularity
- **Enhanced templates** with structured parameter system
- **Auto-extraction system** for automatic template generation
- **Template-first validation** for code-template consistency
- **Dynamic Pulumi.yaml management** (v4.5) for deployment-specific project naming

---

**Document Version:** 4.5
**Last Updated:** 2025-10-30
**Architecture Version:** 4.5
**Authoritative Documents:** Complete_Stack_Management_Guide_v4.md, Stack_Parameters_and_Registration_Guide_v4.md, Complete_Guide_Templates_Stacks_Config_and_Registration_v4.md, Addendum_Dynamic_Pulumi_YAML_Implementation.4.1.md
**Next Document:** Multi_Stack_Architecture.4.5.md
