# Directory Structure Diagram v3.1

**Version:** 3.1
**Date:** 2025-10-21
**Status:** Production Ready

**Changes from v3.0:**
- Updated document version references to 3.1
- Confirmed all directory structures are correct and complete

---

## Directory Structure Diagram Reference, for Multi-Stack Architecture version 3.1

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
│   │   ├── Multi_Stack_Architecture.3.1.md             # Main Architecture Document
│   │   ├── Directory_Structure_Diagram.3.1.md          # This document
│   │   ├── Deployment_Manifest_Specification.3.1.md
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
│   │   ├── config/                                     # Stack Definitions (with dependencies)
│   │   │   ├── network.yaml                            # Network stack template
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
│   │   ├── default/                                    # Manifest Templates
│   │   │   ├── default.yaml                            # Full platform template
│   │   │   ├── minimal.yaml                            # Minimal infrastructure
│   │   │   ├── microservices.yaml                      # Container-focused
│   │   │   └── data-platform.yaml                      # Data processing focus
│   │   │
│   │   └── custom/                                     # Organization-specific Custom Templates
│   │
│   ├── cli/                                            # CLI Tool Source Code
│   │   ├── src/
│   │   │   ├── index.ts                                # CLI entry point
│   │   │   ├── commands/                               # Command implementations
│   │   │   ├── orchestrator/                           # Orchestration engine
│   │   │   ├── templates/                              # Template management
│   │   │   ├── deployment/                             # Deployment management
│   │   │   ├── runtime/                                # Runtime resolution
│   │   │   ├── pulumi/                                 # Pulumi integration
│   │   │   ├── validation/                             # Validation
│   │   │   └── utils/                                  # Utilities
│   │   ├── tests/
│   │   ├── package.json
│   │   └── tsconfig.json
│   │
│   ├── api/                                            # REST API Source Code
│   │   ├── src/
│   │   │   ├── index.ts                                # API entry point
│   │   │   ├── routes/                                 # API route handlers
│   │   │   ├── auth/                                   # Authentication logic
│   │   │   ├── cli-wrapper/                            # CLI integration
│   │   │   ├── websocket/                              # Real-time updates
│   │   │   └── utils/                                  # API utilities
│   │   ├── tests/
│   │   ├── package.json
│   │   └── openapi.yaml
│   │
│   └── dev/                                            # Development & Planning Documents
│       └── ... (implementation plans, analysis docs)
│
├── stacks/                                             # Stack Implementations
│   ├── network/
│   │   ├── index.ts                                    # Main entry point (exports resources)
│   │   ├── docs/
│   │   │   ├── Stack_Prompt_Main.md
│   │   │   ├── Stack_Prompt_Extra.md
│   │   │   ├── Stack_Definitions.md
│   │   │   ├── Stack_Resources.md
│   │   │   ├── Stack_History_Errors.md
│   │   │   ├── Stack_History_Fixes.md
│   │   │   └── Stack_History.md
│   │   ├── src/
│   │   │   ├── vpc.ts                                  # VPC resources
│   │   │   ├── subnets.ts                              # Subnet resources
│   │   │   ├── nat.ts                                  # NAT Gateway resources
│   │   │   └── outputs.ts                              # Exported outputs
│   │   ├── Pulumi.yaml                                 # Stack metadata
│   │   └── package.json
│   │
│   ├── security/
│   │   ├── index.ts
│   │   ├── docs/
│   │   │   ├── Stack_Prompt_Main.md
│   │   │   ├── Stack_Prompt_Extra.md
│   │   │   ├── Stack_Definitions.md
│   │   │   ├── Stack_Resources.md
│   │   │   ├── Stack_History_Errors.md
│   │   │   ├── Stack_History_Fixes.md
│   │   │   └── Stack_History.md
│   │   ├── src/
│   │   │   ├── security-groups.ts
│   │   │   ├── iam-roles.ts
│   │   │   └── kms.ts
│   │   ├── Pulumi.yaml
│   │   └── package.json
│   │
│   ├── dns/
│   │   ├── index.ts
│   │   ├── docs/
│   │   ├── src/
│   │   ├── Pulumi.yaml
│   │   └── package.json
│   │
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
    │   ├── Deployment_Manifest.yaml                    # Deployment configuration
    │   ├── config/
    │   │   ├── network.dev.yaml                        # Network dev config
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
    │   ├── Deployment_Manifest.yaml                    # Deployment configuration
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
        ├── Deployment_Manifest.yaml                    # Deployment configuration
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

**Path:** `./cloud/deploy/<deployment-id>-<org>-<project>/Deployment_Manifest.yaml`

The manifest is located **at the deployment root** (not in a `src/` subdirectory).

### Stack Configuration Files

**Path:** `./cloud/deploy/<deployment-id>-<org>-<project>/config/<stack>.<environment>.yaml`

**Examples:**
- `config/network.dev.yaml`
- `config/network.stage.yaml`
- `config/network.prod.yaml`
- `config/security.dev.yaml`

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
- `index.ts.template` - Main entry point
- `src/component-example.ts.template` - Component example
- `src/outputs.ts.template` - Output definitions
- `Pulumi.yaml.template` - Stack metadata
- `package.json.template` - NPM dependencies
- `tsconfig.json.template` - TypeScript configuration

### Stack Definition Templates (`tools/templates/config/`)

YAML files defining each stack's:
- Dependencies on other stacks
- Layer assignment
- Configuration parameters
- Output values
- Default settings

### Manifest Templates (`tools/templates/default/`)

Pre-built deployment templates:
- `default.yaml` - Full platform (all 16 stacks)
- `minimal.yaml` - Basic infrastructure only
- `microservices.yaml` - Container-focused deployment
- `data-platform.yaml` - Data processing focus

---

## Directory Structure Changes from v2.3

```
Old (Architecture 2.3)                    New (Architecture 3.1)
────────────────────────────────────────────────────────────────────
./aws/deploy/                         →   ./cloud/deploy/
./admin/v2/                           →   ./cloud/tools/
./aws/build/<stack>/v2/src/     →   ./cloud/stacks/<stack>/src/
./admin/v2/docs/                      →   ./cloud/tools/docs/
./admin/v2/templates/                 →   ./cloud/tools/templates/

Deployment directories:
./deploy/D1BRV40/                     →   ./deploy/D1BRV40-CompanyA-ecommerce/

Manifest location:
(varied)                              →   ./deploy/<id>-<org>-<project>/Deployment_Manifest.yaml
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

---

**Document Version:** 3.1
**Last Updated:** 2025-10-21
**Next Document:** Multi_Stack_Architecture.3.1.md
