# Cloud Infrastructure Orchestration Platform - Documentation Index

**Platform:** cloud-0.7
**Architecture Version:** 4.8
**Last Updated:** 2025-10-31

---

## Welcome

This is the master documentation index for the Cloud Infrastructure Orchestration Platform (cloud-0.7). This platform provides comprehensive tools for managing complex, interdependent AWS infrastructure deployments using Pulumi with a Python-based CLI, core business logic library, and --config-file based configuration (NEW in v4.8).

---

## Getting Started

| Document | Description |
|----------|-------------|
| [INSTALL.md](INSTALL.md) | **Start here!** Complete installation and build guide for stacks and CLI |
| [Multi_Stack_Architecture.4.8.md](Multi_Stack_Architecture.4.8.md) | Main architecture document - comprehensive platform overview (v4.8) |
| [Directory_Structure_Diagram.4.8.md](Directory_Structure_Diagram.4.8.md) | Complete directory structure and organization (v4.8) |

---

## Authoritative Documentation (v4.0+)

### Primary Architecture Documents

These documents define the current, authoritative architecture:

| Document | Version | Description |
|----------|---------|-------------|
| [Complete_Stack_Management_Guide.4.8.md](Complete_Stack_Management_Guide.4.8.md) | 4.8 | 🔖 **Authoritative** - Complete platform workflow and management |
| [Stack_Parameters_and_Registration_Guide.4.8.md](Stack_Parameters_and_Registration_Guide.4.8.md) | 4.8 | 🔖 **Authoritative** - Enhanced templates, parameters, and registration |
| [Complete_Guide_Templates_Stacks_Config_and_Registration_v4.6.md](Complete_Guide_Templates_Stacks_Config_and_Registration_v4.6.md) | 4.0 | 🔖 **Authoritative** - Template system and configuration flow |
| [Implementation_Compliance_Report_v4.md](Implementation_Compliance_Report_v4.md) | 4.0 | Architecture compliance verification report |

### Core Architecture Documents (v4.8)

Updated to align with v4.0 authoritative documents, enhanced in v4.8:

| Document | Version | Description |
|----------|---------|-------------|
| [Multi_Stack_Architecture.4.8.md](Multi_Stack_Architecture.4.8.md) | 4.8 | Complete architecture specification with --config-file approach |
| [Directory_Structure_Diagram.4.8.md](Directory_Structure_Diagram.4.8.md) | 4.8 | Directory structure reference |
| [Deployment_Manifest_Specification.4.8.md](Deployment_Manifest_Specification.4.8.md) | 4.8 | Manifest file format with --config-file parameter |
| [Addendum_Dynamic_Pulumi_YAML_Implementation.4.1.md](Addendum_Dynamic_Pulumi_YAML_Implementation.4.1.md) | 4.1 | Dynamic Pulumi.yaml management system |

---

## Core Architecture Documentation (v3.1 - Legacy)

**Note:** v3.1 documents are now **legacy** and superseded by v4.1. They are kept for reference only.

### Legacy Primary Documents

| Document | Version | Status |
|----------|---------|--------|
| [Multi_Stack_Architecture.3.1.md](Multi_Stack_Architecture.3.1.md) | 3.1 | ⚠️ Legacy - See v4.1 |
| [Directory_Structure_Diagram.3.1.md](Directory_Structure_Diagram.3.1.md) | 3.1 | ⚠️ Legacy - See v4.1 |
| [Deployment_Manifest_Specification.3.1.md](Deployment_Manifest_Specification.3.1.md) | 3.1 | ⚠️ Legacy - See v4.1 |

---

## CLI Documentation

### Command Reference

| Document | Description |
|----------|-------------|
| [CLI_Commands_Reference.3.1.md](CLI_Commands_Reference.3.1.md) | Complete CLI command documentation (25+ commands) |
| [CLI_Commands_Quick_Reference.3.1.md](CLI_Commands_Quick_Reference.3.1.md) | Quick reference guide for CLI commands |
| [CLI_Testing_Guide.3.1.md](CLI_Testing_Guide.3.1.md) | Testing procedures for the CLI |

**Note:** CLI is implemented in **Python** using Typer framework, not TypeScript.

---

## REST API Documentation

### API Reference

| Document | Description |
|----------|-------------|
| [REST_API_Documentation.3.1.md](REST_API_Documentation.3.1.md) | Complete REST API documentation |
| [REST_API_Quick_Reference.3.1.md](REST_API_Quick_Reference.3.1.md) | Quick reference for API endpoints |
| [REST_API_Testing_Guide.3.1.md](REST_API_Testing_Guide.3.1.md) | Testing procedures for the REST API |

---

## Addendum Documents

### Supplementary Documentation

| Document | Description |
|----------|-------------|
| [Architecture_Inconsistency_Analysis_v3.1_to_v4.md](Architecture_Inconsistency_Analysis_v3.1_to_v4.md) | Analysis of changes from v3.1 to v4.0 |
| [Addendum_Platform_Code.3.1.md](Addendum_Platform_Code.3.1.md) | Code examples and implementation patterns |
| [Addendum_Changes_From_2.3.3.1.md](Addendum_Changes_From_2.3.3.1.md) | Complete changelog from Architecture 2.3 to 3.1 |
| [Addendum_Questions_Answers.3.1.md](Addendum_Questions_Answers.3.1.md) | Architecture questions and design decisions |
| [Addendum_Stack_Cloning.3.1.md](Addendum_Stack_Cloning.3.1.md) | Guide for creating multiple similar stacks |
| [Addendum_Verification_Architecture.3.1.md](Addendum_Verification_Architecture.3.1.md) | Validation and verification tools |
| [Addendum_Progress_Monitoring.3.1.md](Addendum_Progress_Monitoring.3.1.md) | Real-time progress monitoring via WebSocket |
| [Addendum_Statistics.3.1.md](Addendum_Statistics.3.1.md) | Platform statistics and metrics |

---

## Quick Navigation by Topic

### 🏗️ Architecture & Design
- [Multi_Stack_Architecture.4.6.md](Multi_Stack_Architecture.4.6.md) - **Current architecture (v4.6)**
- [Complete_Stack_Management_Guide_v4.6.md](Complete_Stack_Management_Guide_v4.6.md) - **Authoritative guide**
- [Directory_Structure_Diagram.4.6.md](Directory_Structure_Diagram.4.6.md) - **Directory layout (v4.6)**
- [Addendum_Dynamic_Pulumi_YAML_Implementation.4.1.md](Addendum_Dynamic_Pulumi_YAML_Implementation.4.1.md) - **Dynamic Pulumi.yaml (NEW v4.6)**
- [Architecture_Inconsistency_Analysis_v3.1_to_v4.md](Architecture_Inconsistency_Analysis_v3.1_to_v4.md) - **v3.1 to v4.0 changes**

### 📦 Templates & Configuration
- [Complete_Guide_Templates_Stacks_Config_and_Registration_v4.6.md](Complete_Guide_Templates_Stacks_Config_and_Registration_v4.6.md) - **Authoritative template guide**
- [Stack_Parameters_and_Registration_Guide_v4.6.md](Stack_Parameters_and_Registration_Guide_v4.6.md) - **Enhanced templates**
- [Deployment_Manifest_Specification.4.6.md](Deployment_Manifest_Specification.4.6.md) - **Manifest format (v4.6)**

### 💻 CLI Usage
- [INSTALL.md](INSTALL.md) - Installation guide
- [CLI_Commands_Reference.3.1.md](CLI_Commands_Reference.3.1.md) - Full command docs
- [CLI_Commands_Quick_Reference.3.1.md](CLI_Commands_Quick_Reference.3.1.md) - Quick reference

### 🌐 REST API
- [REST_API_Documentation.3.1.md](REST_API_Documentation.3.1.md) - Full API docs
- [REST_API_Quick_Reference.3.1.md](REST_API_Quick_Reference.3.1.md) - Quick reference

### 🧪 Testing & Validation
- [CLI_Testing_Guide.3.1.md](CLI_Testing_Guide.3.1.md) - CLI testing
- [REST_API_Testing_Guide.3.1.md](REST_API_Testing_Guide.3.1.md) - API testing
- [Addendum_Verification_Architecture.3.1.md](Addendum_Verification_Architecture.3.1.md) - Validation tools
- [Implementation_Compliance_Report_v4.md](Implementation_Compliance_Report_v4.md) - Compliance report

### 📊 Monitoring
- [Addendum_Progress_Monitoring.3.1.md](Addendum_Progress_Monitoring.3.1.md) - WebSocket monitoring
- [Addendum_Statistics.3.1.md](Addendum_Statistics.3.1.md) - Platform metrics

### 🔧 Development
- [Addendum_Platform_Code.3.1.md](Addendum_Platform_Code.3.1.md) - Code examples
- [Addendum_Stack_Cloning.3.1.md](Addendum_Stack_Cloning.3.1.md) - Stack templates

---

## Document Organization

### By Directory

```
cloud/
├── .claude/
│   ├── CLAUDE.md                           # Memory bank configuration
│   └── memory/                             # Session management documents
│
└── tools/
    ├── docs/                               # Platform documentation (YOU ARE HERE)
    │   ├── README.md                       # This file (v4.1)
    │   ├── INSTALL.md                      # Installation guide (v4.1)
    │   │
    │   ├── Multi_Stack_Architecture.4.1.md              # v4.1 Architecture
    │   ├── Directory_Structure_Diagram.4.1.md           # v4.1 Directory structure
    │   ├── Deployment_Manifest_Specification.4.1.md     # v4.1 Manifest spec
    │   │
    │   ├── Complete_Stack_Management_Guide_v4.6.md        # 🔖 Authoritative v4
    │   ├── Stack_Parameters_and_Registration_Guide_v4.6.md  # 🔖 Authoritative v4
    │   ├── Complete_Guide_Templates_Stacks_Config_and_Registration_v4.6.md  # 🔖 Authoritative v4
    │   ├── Implementation_Compliance_Report_v4.md
    │   ├── Architecture_Inconsistency_Analysis_v3.1_to_v4.md
    │   │
    │   ├── Multi_Stack_Architecture.3.1.md              # Legacy v3.1
    │   ├── Directory_Structure_Diagram.3.1.md           # Legacy v3.1
    │   ├── Deployment_Manifest_Specification.3.1.md     # Legacy v3.1
    │   │
    │   ├── CLI_Commands_Reference.3.1.md
    │   ├── CLI_Commands_Quick_Reference.3.1.md
    │   ├── CLI_Testing_Guide.3.1.md
    │   ├── REST_API_Documentation.3.1.md
    │   ├── REST_API_Quick_Reference.3.1.md
    │   ├── REST_API_Testing_Guide.3.1.md
    │   ├── Addendum_Platform_Code.3.1.md
    │   ├── Addendum_Changes_From_2.3.3.1.md
    │   ├── Addendum_Questions_Answers.3.1.md
    │   ├── Addendum_Stack_Cloning.3.1.md
    │   ├── Addendum_Verification_Architecture.3.1.md
    │   ├── Addendum_Progress_Monitoring.3.1.md
    │   └── Addendum_Statistics.3.1.md
    │
    ├── core/                               # Core business logic library (Python)
    │   └── cloud_core/
    │       ├── deployment/
    │       ├── orchestrator/
    │       ├── runtime/
    │       ├── templates/
    │       ├── validation/
    │       ├── pulumi/
    │       └── utils/
    │
    ├── cli/                                # CLI tool (Python)
    │   └── cloud_cli/
    │       ├── commands/
    │       ├── parser/                     # Auto-extraction system
    │       └── main.py
    │
    ├── dev/                                # Development documents
    └── install/                            # Installation scripts
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| **4.8** | **2025-10-31** | **--config-file approach, enhanced CLI with rich modes, deployment lifecycle improvements** |
| 4.6 | 2025-10-30 | Composite project naming for complete deployment isolation |
| 4.5 | 2025-10-30 | Dynamic Pulumi.yaml management, pulumiOrg/project fields, stacks disabled by default |
| 4.1 | 2025-10-29 | Aligned with v4.0 authoritative documents, Python CLI, enhanced templates |
| 4.0 | 2025-10-28 | Template-first validation, auto-extraction, cross-stack dependencies |
| 3.1 | 2025-10-21 | Updated Pulumi state management, stack naming, Python CLI |
| 3.0 | 2025-10-08 | Template-based dependencies, smart deployment, layer execution |
| 2.3 | 2025-10-01 | Multi-file TypeScript support, configuration tiers |

---

## Architecture Highlights (v4.8)

### Core/CLI Architecture

**Two-Tier Design:**
- `tools/core/cloud_core/` - Business logic library (Python)
- `tools/cli/cloud_cli/` - Command-line interface (Python)

**Key Modules:**
- Deployment management
- Orchestration engine (dependency resolver, layer calculator)
- Runtime resolution (placeholders, stack references)
- Enhanced template system
- Template-first validation
- Auto-extraction system

### Enhanced Template System (v4.0+)

**Stack Templates with Parameters:**
```yaml
parameters:
  inputs:
    vpcCidr:
      type: string
      required: true
      default: "10.0.0.0/16"

  outputs:
    vpcId:
      type: string
    privateSubnetIds:
      type: array
```

**Auto-Extraction:**
- Automatically extract parameters from TypeScript code
- Generate templates from stack implementations
- Validate code against templates

### Configuration System

**Pulumi Native Format:**
```yaml
network:vpcCidr: "10.0.0.0/16"
network:availabilityZones: "3"
aws:region: "us-east-1"
```

**Cross-Stack Dependencies:**
```yaml
database-rds:
  config:
    subnets: "${network.privateSubnetIds}"
```

---

## Platform Statistics

| Metric | Count |
|--------|-------|
| **Documentation Files (v4.1)** | 20+ |
| **Documentation Files (Legacy v3.1)** | 16 |
| **Architecture Stacks** | 16 |
| **CLI Commands** | 25+ |
| **REST API Endpoints** | 15+ |
| **Supported Environments** | 3 (dev, stage, prod) |
| **Core Test Suite** | 393+ tests passing |
| **CLI Test Suite** | 38+ tests passing |

---

## Getting Help

### Installation Issues
See [INSTALL.md](INSTALL.md) troubleshooting section

### Architecture Questions
- See [Complete_Stack_Management_Guide_v4.6.md](Complete_Stack_Management_Guide_v4.6.md) for complete workflow
- See [Architecture_Inconsistency_Analysis_v3.1_to_v4.md](Architecture_Inconsistency_Analysis_v3.1_to_v4.md) for v3.1 to v4.0 migration

### Command Usage
See [CLI_Commands_Reference.3.1.md](CLI_Commands_Reference.3.1.md)

### Template System
See [Stack_Parameters_and_Registration_Guide_v4.6.md](Stack_Parameters_and_Registration_Guide_v4.6.md)

### API Usage
See [REST_API_Documentation.3.1.md](REST_API_Documentation.3.1.md)

---

## Contributing

### Documentation Standards
- Use Markdown format
- Include table of contents for documents > 100 lines
- Maintain version numbers in headers
- Update this README when adding new documents
- Mark deprecated documents clearly

### Code Standards
- Python: Follow PEP 8, use type hints
- TypeScript: Follow TSConfig strict mode (for stacks)
- All code must pass tests before commit
- Use Black for Python formatting
- Use Prettier for TypeScript formatting

---

## License

See platform repository for license information.

---

## Contact

For questions or support, refer to the platform maintainers or open an issue on GitHub.

---

**Platform:** cloud-0.7
**Architecture:** 4.5
**Total Documentation:** 21+ files (v4.6) + 16 files (legacy v3.1)
**Last Updated:** 2025-01-30
**Implementation Status:** ✅ 100% Architecture Compliant (v4.6)

**End of Documentation Index**
