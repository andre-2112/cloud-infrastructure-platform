# Directory Structure Diagram v3.1

## Directory Structure Diagram Reference, for Multi-Stack Archtecture version 3.1

<directory_structure>
```
./cloud/                                                # Cloud Platform Root
│   
├── .claude/                                            # Claude
│   ├── commands/  
│   ├── memory/                                            
│   └── skills/  

├── tools/                                              # Platform Tools
│   │
│   ├── docs/                                           # Architecture Documentation
│   │   ├── Multi_Stack_Architecture.3.0.md             # Main Architecture Document
│   │   ├── Directory_Structure_Diagram.3.0.md          # This document
│   │   ├── Deployment_Manifest_Specification.3.0.md
│   │   ├── CLI_Commands_Reference.3.0.md
│   │   ├── REST_API_Documentation.3.0.md
│   │   ├── Addendum_Platform_Code.3.0.md
│   │   └── ... (additional documents)
│   │
│   ├── templates/                                      # Deployment Templates
│   │   │
│   │   ├── docs/                                       # Stack Marokdown Templates   
│   │   │   ├── Stack_Prompt_Main.md
│   │   │   ├── Stack_Prompt.Extra.md
│   │   │   ├── Stack_Definitions.md
│   │   │   ├── Stack_Resources.md
│   │   │   ├── Stack_History_Errors.md
│   │   │   ├── Stack_History_Fixes.md
│   │   │   └── Stack_History.md
│   │   │
│   │   ├── stack/                                      # Stack Pulumi Templates
│   │   │   ├── index.ts                                # Main entry point (exports resources)
│   │   │   ├── src/
│   │   │   │   ├── stack-component-1.ts                # optional additional stack componentas
│   │   │   │   ├── stack-component-2.ts                # optional additional stack componentas
│   │   │   │   └── outputs.ts                          # Exported outputs
│   │   │   ├── Pulumi.yaml                             # Stack metadata
│   │   │   └── package.json
│   │   │ 
│   │   ├── config/                                     # Stack Definitions (with dependencies)
│   │   │   ├── network.yaml                            # Network stack template
│   │   │   ├── dns.yaml                                # DNS stack template
│   │   │   ├── security.yaml                           # Security stack template
│   │   │   └── ... (13 more stacks)
│   │   │
│   │   ├── default/                                    # Manifest Templates
│   │   │   ├── default.yaml                            # Full platform template - updated when stacks are added/changed
│   │   │   ├── minimal.yaml                            # Minimal infrastructure
│   │   │   ├── microservices.yaml                      # Container-focused
│   │   │   └── data-platform.yaml                      # Data processing focus
│   │   │ 
│   │   └── custom/                                     # Organization-specific Custom Stack Templates   
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
│   └── api/                                            # REST API Source Code
│       ├── src/
│       │   ├── index.ts                                # API entry point
│       │   ├── routes/                                 # API route handlers
│       │   ├── auth/                                   # Authentication logic
│       │   ├── cli-wrapper/                            # CLI integration
│       │   ├── websocket/                              # Real-time updates
│       │   └── utils/                                  # API utilities
│       ├── tests/
│       ├── package.json
│       └── openapi.yaml
│
├── stacks/                                             # Stack implementations
│   ├── network/
│   │   ├── index.ts                                    # Main entry point (exports resources)
│   │   ├── docs/
│   │   │   ├── Stack_Prompt_Main.md
│   │   │   ├── Stack_Prompt.Extra.md
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
│   ├── security/
│   │   ├── index.ts
│   │   ├── docs/
│   │   │   ├── Stack_Prompt_Main.md
│   │   │   ├── Stack_Prompt.Extra.md
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
│   ├── database-rds/
│   │   ├── index.ts
│   │   ├── docs/
│   │   │   ├── Stack_Prompt_Main.md
│   │   │   ├── Stack_Prompt.Extra.md
│   │   │   ├── Stack_Definitions.md
│   │   │   ├── Stack_Resources.md
│   │   │   ├── Stack_History_Errors.md
│   │   │   ├── Stack_History_Fixes.md
│   │   │   └── Stack_History.md
│   │   ├── src/
│   │   │   ├── rds-instance.ts
│   │   │   ├── subnet-group.ts
│   │   │   └── parameter-group.ts
│   │   ├── Pulumi.yaml
│   │   └── package.json
│   └── ... (13 more stacks)
│
└── deploy/                                             # Active Deployments
    ├── D1BRV40-CompanyA-ecommerce/                     # Deployment Example 1
    │   ├── Deployment_Manifest.yaml                    # Deployment config
    │   ├── config/
    │   │   ├── network.dev.yaml                        # Network dev config
    │   │   ├── network.stage.yaml                      # Network stage config
    │   │   ├── network.prod.yaml                       # Network prod config
    │   │   └── ... (all stacks × environments)
    │   └── logs/
    │       ├── init.log
    │       ├── D1BRV40-dev-20251009.log
    │       └── D1BRV40-stage-20251010.log
    │
    ├── D1BRV45-CompanyB-mobile/                        # Deployment Example 2
    │   ├── Deployment_Manifest.yaml                    # Deployment config
    │   ├── config/
    │   │   ├── network.dev.yaml                        # Network dev config
    │   │   ├── network.stage.yaml                      # Network stage config
    │   │   ├── network.prod.yaml                       # Network prod config
    │   │   └── ... (all stacks × environments)
    │   └── logs/
    │       ├── init.log
    │       ├── D1BRV45-dev-20251009.log
    │       └── D1BRV45-stage-20251010.log
    │   
    └── D1BRV50-CompanyA-analytics/                     # Deployment Example 3
        ├── Deployment_Manifest.yaml                    # Deployment config
        ├── config/
        │   ├── network.dev.yaml                        # Network dev config
        │   ├── network.stage.yaml                      # Network stage config
        │   ├── network.prod.yaml                       # Network prod config
        │   └── ... (all stacks × environments)
        └── logs/
            ├── init.log
            ├── D1BRV50-dev-20251009.log
            └── D1BRV50-stage-20251010.log
```
</directory_structure>
  