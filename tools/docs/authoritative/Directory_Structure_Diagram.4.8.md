# Directory Structure Diagram v4.8

**Version:** 4.8
**Date:** 2025-10-31
**Status:** Production Ready
**Architecture**: Aligned with v4.0 authoritative documents, enhanced in v4.5, v4.6, v4.8

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

**Changes from v4.5 to v4.6:**
- **Composite Project Naming Scheme** - Complete deployment isolation in Pulumi Cloud
- Configuration file key prefixes now use composite project name format: `{DeploymentID}-{Organization}-{Project}`
- Updated config_generator.py to generate composite project prefixes
- Updated pulumi_wrapper.py _generate_pulumi_yaml() to use composite project names
- Enhanced deployment_context() to pass manifest for composite naming
- Stack names remain simple; deployment isolation via composite project naming

**Changes from v4.6 to v4.8:**
- **Configuration Approach Change** - Switched from `pulumi config set` to `--config-file` parameter
- Config files generated and stored in deployment directories
- Pulumi invoked with `--config-file` pointing to deployment-specific config files
- **Enhanced CLI Commands** - Rich interactive modes for list, config, and status commands
- **Deployment Lifecycle** - Improved state tracking (initialized, deployed, partial, failed, destroyed)
- **Destroyed Deployment History** - Full history preserved for audit trail
- `cloud list` filters destroyed deployments by default
- `cloud list --all` shows all deployments including destroyed
- `cloud list --rich` provides interactive mode with actions menu
- **Error Handling** - Comprehensive AWS error detection with user-friendly messages
- Error logs stored in deployment directory under logs/
- Specific remediation guidance for AWS service limits

---

## Directory Structure Diagram Reference, for Multi-Stack Architecture version 4.8

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
│   │   ├── Multi_Stack_Architecture.4.8.md             # Main Architecture Document (v4.8)
│   │   ├── Directory_Structure_Diagram.4.8.md          # This document (v4.6)
│   │   ├── Deployment_Manifest_Specification.4.8.md    # Manifest spec (v4.6)
│   │   ├── Architecture_v4.6_Composite_Naming_Summary.md  # Composite naming (NEW v4.6)
│   │   ├── Addendum_Dynamic_Pulumi_YAML_Implementation.4.1.md  # Dynamic Pulumi.yaml (v4.5)
│   │   ├── README.md                                   # Documentation index (v4.6)
│   │   ├── INSTALL.md                                  # Installation guide (v4.6)
│   │   │
│   │   ├── Complete_Stack_Management_Guide.4.8.md       # 🔖 Authoritative v4.6
│   │   ├── Stack_Parameters_and_Registration_Guide.4.8.md  # 🔖 Authoritative v4.6
│   │   ├── Complete_Guide_Templates_Stacks_Config_and_Registration_v4.6.md  # 🔖 Authoritative v4.6
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
│   ├── core/                                           # Core Business Logic Library (v4)
│   │   ├── cloud_core/                                 # Python package
│   │   │   ├── __init__.py
│   │   │   ├── deployment/                             # Deployment Management
│   │   │   │   ├── config_generator.py                 # Generates Pulumi config files (v4.6: composite naming)
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
│   │   │   │   ├── pulumi_wrapper.py                   # Pulumi CLI wrapper (v4.6: composite project naming)
│   │   │   │   ├── stack_operations.py                 # Stack operations
│   │   │   │   └── state_queries.py                    # State queries
│   │   │   └── utils/                                  # Utilities
│   │   │       ├── logger.py                           # Logging
│   │   │       └── deployment_id.py                    # ID generation
│   │   ├── tests/                                      # Core tests (393+ tests)
│   │   ├── setup.py
│   │   └── requirements.txt
│   │
│   ├── cli/                                            # CLI Tool (Python - v4)
│   │   ├── src/
│   │   │   └── cloud_cli/                              # Python package
│   │   │       ├── __init__.py
│   │   │       ├── main.py                             # CLI entry point
│   │   │       ├── commands/                           # Command implementations
│   │   │       │   ├── stack_cmd.py                    # Stack commands (register, validate)
│   │   │       │   ├── deploy_cmd.py                   # Deployment commands (v4.6: passes manifest)
│   │   │       │   ├── template_cmd.py                 # Template commands
│   │   │       │   └── ...                             # Other command modules
│   │   │       └── parser/                             # Auto-Extraction System (v4)
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
    │   │   ├── network.dev.yaml                        # Network dev config (Pulumi format, v4.6: composite prefix)
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

### Composite Project Naming (NEW in v4.6)

**Format:** `{DeploymentID}-{Organization}-{Project}`

**Example:** `DT28749-TestOrg-demo-test`

**Where Applied:**
1. **Pulumi Cloud Project Names**
   - Full stack path: `{pulumiOrg}/{composite-project}/{stack-name}-{environment}`
   - Example: `andre-2112/DT28749-TestOrg-demo-test/network-dev`

2. **Configuration File Key Prefixes**
   - Format: `{composite-project}:{key}: "{value}"`
   - Example: `DT28749-TestOrg-demo-test:vpc_cidr: "10.0.0.0/16"`

3. **Generated Pulumi.yaml Files**
   - The `name:` field uses the composite project name
   - Example: `name: DT28749-TestOrg-demo-test`

**Benefits:**
- **Complete Deployment Isolation** - Each deployment gets unique Pulumi Cloud namespace
- **No Stack Naming Conflicts** - Multiple teams/environments can coexist
- **Organization Clarity** - Separates business org from Pulumi org
- **Simplified Cleanup** - Easy to identify and remove deployment artifacts

**Technical Implementation:**
- `config_generator.py` - Lines 98-108: Builds composite name and uses as config prefix
- `pulumi_wrapper.py` - Lines 444-485: Generates Pulumi.yaml with composite project name
- `deploy_cmd.py` - Lines 96-97: Passes manifest to deployment_context

For complete details, see: `Architecture_v4.6_Composite_Naming_Summary.md`

### Deployment Manifest Location

**Path:** `./cloud/deploy/<deployment-id>-<org>-<project>/deployment-manifest.yaml`

**Format:** YAML (not JSON!)

**Key Points:**
- The manifest is located **at the deployment root** (not in a `src/` subdirectory)
- Filename is `deployment-manifest.yaml` (hyphenated, not camelCase or underscored)
- Contains all environment and stack configurations

### Stack Configuration Files (v4.6 Format)

**Path:** `./cloud/deploy/<deployment-id>-<org>-<project>/config/<stack>.<environment>.yaml`

**Format:** Pulumi native format with composite project prefix (v4.6)

**Examples:**
- `config/network.dev.yaml`
- `config/network.stage.yaml`
- `config/network.prod.yaml`
- `config/security.dev.yaml`

**Pulumi Native Format Example (v4.6 - Composite Prefix):**
```yaml
# config/network.dev.yaml
DT28749-TestOrg-demo-test:deploymentId: "DT28749"
DT28749-TestOrg-demo-test:organization: "TestOrg"
DT28749-TestOrg-demo-test:project: "demo-test"
DT28749-TestOrg-demo-test:vpcCidr: "10.0.0.0/16"
DT28749-TestOrg-demo-test:availabilityZones: "2"
aws:region: "us-east-1"
```

**Previous Format (v4.5 - Stack Name Prefix):**
```yaml
# config/network.dev.yaml
network:deploymentId: "DT28749"
network:organization: "TestOrg"
network:project: "demo-test"
network:vpcCidr: "10.0.0.0/16"
network:availabilityZones: "2"
aws:region: "us-east-1"
```

**Key Changes in v4.6:**
- Configuration keys now use **composite project name** as prefix (not stack name)
- Format: `{DeploymentID}-{Organization}-{Project}:{key}: "{value}"`
- Provides complete deployment isolation in Pulumi Cloud
- All values remain strings (Pulumi requirement)
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

**Enhanced in v4:** Structured parameter system with inputs/outputs

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

## Core/CLI Architecture Split (v4)

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
- `config_generator.py` - Generates Pulumi config files in native format (v4.6: composite prefix)
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

**Auto-Extraction (v4):**
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
- **v4.6:** Pulumi.yaml temporarily replaced with composite project name during deployment

---

## Directory Structure Changes from v2.3

```
Old (Architecture 2.3)                    New (Architecture 4.6)
────────────────────────────────────────────────────────────────────
./aws/deploy/                         →   ./cloud/deploy/
./admin/v2/                           →   ./cloud/tools/
./aws/build/<stack>/v2/src/           →   ./cloud/stacks/<stack>/
./admin/v2/docs/                      →   ./cloud/tools/docs/
./admin/v2/templates/                 →   ./cloud/tools/templates/

Deployment directories:
./deploy/D1BRV40/                     →   ./deploy/D1BRV40-CompanyA-ecommerce/

Manifest location:
(varied)                              →   ./deploy/<id>-<org>-<project>/deployment-manifest.yaml

Config files:
./deploy/<id>/*.yaml                  →   ./deploy/<id>/config/*.yaml

Config key format (v4.6):
<stack>:<key>: "value"                →   <deployment-id>-<org>-<project>:<key>: "value"

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
- **Composite project naming** (v4.6) for complete deployment isolation in Pulumi Cloud

---

**Document Version:** 4.8
**Last Updated:** 2025-10-31
**Architecture Version:** 4.8
**Authoritative Documents:** Complete_Stack_Management_Guide.4.8.md, Stack_Parameters_and_Registration_Guide.4.8.md, Complete_Guide_Templates_Stacks_Config_and_Registration_v4.6.md, Architecture_v4.6_Composite_Naming_Summary.md
**Previous Version:** Directory_Structure_Diagram.4.6.md
**Next Document:** Multi_Stack_Architecture.4.8.md
