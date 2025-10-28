# Cloud Infrastructure Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-393%20passing-brightgreen)](tools/core/tests/)
[![Architecture](https://img.shields.io/badge/architecture-v4.0-brightgreen)](tools/docs/)

A comprehensive multi-stack deployment orchestration system built on Pulumi, designed for managing complex cloud infrastructure with automated dependency resolution, parallel execution, and template-based configuration.

## 🎯 Overview

The Cloud Infrastructure Platform provides an enterprise-grade framework for managing multi-stack cloud deployments. It introduces a structured approach to infrastructure-as-code that emphasizes:

- **Template-First Development**: Stack templates define inputs and outputs before implementation
- **Dependency Management**: Automatic resolution of cross-stack dependencies
- **Parallel Execution**: Layer-based parallel deployment of independent stacks
- **Type Safety**: Comprehensive validation and type checking
- **Runtime Resolution**: Dynamic placeholder resolution for AWS resources and stack outputs

## 🏗️ Architecture

```
cloud/
├── stacks/              # Individual infrastructure stacks
│   ├── network/         # VPC, subnets, routing
│   ├── security/        # Security groups, NACLs
│   ├── database-rds/    # RDS databases
│   ├── services-ecs/    # ECS clusters and services
│   └── ...              # 16 total stacks
├── tools/
│   ├── core/            # Business logic library (cloud_core)
│   │   ├── deployment/  # Deployment and config management
│   │   ├── orchestrator/ # Dependency resolution and execution
│   │   ├── runtime/     # Placeholder and output resolution
│   │   ├── templates/   # Template management
│   │   └── validation/  # Code and manifest validation
│   ├── cli/             # Command-line interface (cloud_cli)
│   │   └── commands/    # CLI commands
│   └── docs/            # Comprehensive documentation
├── templates/           # Stack and deployment templates
└── deploy/             # Deployment instances
```

## ✨ Key Features

### Multi-Stack Orchestration
- **Dependency Graph**: Automatically builds and validates dependency relationships
- **Layer Calculation**: Groups stacks into execution layers for parallel deployment
- **Cycle Detection**: Prevents circular dependencies
- **Execution Engine**: Parallel execution within layers, sequential across layers

### Template System
- **Stack Templates**: Define parameters, inputs, outputs, and dependencies
- **Deployment Templates**: Multi-stack deployment configurations
- **Auto-Extraction**: Extract parameters from TypeScript stack code
- **Template Validation**: Ensure code matches template specifications

### Cross-Stack Dependencies
- **Output References**: Reference outputs from other stacks using `${stack.output}`
- **Runtime Resolution**: Automatic resolution during deployment
- **Type Safety**: Validate output types and required dependencies

### Configuration Management
- **Pulumi Integration**: Native Pulumi configuration format
- **Environment Support**: Multi-environment deployments (dev, staging, prod)
- **Config Generation**: Automatic generation from deployment manifests
- **Placeholder Resolution**: Support for both `{{...}}` and `${...}` syntaxes

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Node.js 14+
- Pulumi CLI
- AWS credentials configured

### Installation

```bash
# Clone the repository
git clone https://github.com/andre-2112/cloud-infrastructure-platform.git
cd cloud-infrastructure-platform

# Install core library
cd tools/core
pip install -e .

# Install CLI tool
cd ../cli
pip install -e .

# Verify installation
cloud-cli --version
```

### Basic Usage

```bash
# Initialize a new deployment
cloud-cli init --deployment-id D1PROD --organization MyOrg

# Register a stack (auto-extract parameters)
cloud-cli register-stack network --auto-extract

# Validate stack code against template
cloud-cli validate-stack network --strict

# Deploy all stacks
cloud-cli deploy D1PROD --environment prod

# Deploy specific stack
cloud-cli deploy-stack D1PROD network --environment prod

# Check deployment status
cloud-cli status D1PROD

# Destroy deployment
cloud-cli destroy D1PROD --environment prod
```

## 📚 Documentation

Comprehensive documentation is available in `tools/docs/`:

### Core Guides
- **[Complete Stack Management Guide v4](tools/docs/Complete_Stack_Management_Guide_v4.md)** - Complete platform overview
- **[Stack Parameters & Registration Guide v4](tools/docs/Stack_Parameters_and_Registration_Guide_v4.md)** - Parameter system and registration
- **[Templates, Stacks & Config Guide v4](tools/docs/Complete_Guide_Templates_Stacks_Config_and_Registration_v4.md)** - Template system deep dive

### Reference Documentation
- **[CLI Commands Reference](tools/docs/CLI_Commands_Reference.3.1.md)** - All CLI commands
- **[Deployment Manifest Specification](tools/docs/Deployment_Manifest_Specification.3.1.md)** - Manifest format
- **[Multi-Stack Architecture](tools/docs/Multi_Stack_Architecture.3.1.md)** - Architecture overview

### Additional Resources
- **[Implementation Compliance Report v4](tools/docs/Implementation_Compliance_Report_v4.md)** - Architecture compliance verification
- **[Installation Guide](tools/docs/INSTALL.md)** - Detailed installation instructions

## 🧪 Testing

The platform includes comprehensive test coverage:

```bash
# Run core tests
cd tools/core
pytest tests/ -v

# Run CLI tests
cd tools/cli
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=cloud_core --cov-report=html
```

**Test Results:**
- Core: 393 passing tests
- CLI: 38 passing tests
- Coverage: High coverage across all modules

## 🏛️ Stack Library

The platform includes 16 production-ready stacks:

| Stack | Purpose | Dependencies |
|-------|---------|--------------|
| `network` | VPC, subnets, routing | - |
| `security` | Security groups, NACLs | network |
| `secrets` | AWS Secrets Manager | - |
| `database-rds` | RDS databases | network, security |
| `compute-ec2` | EC2 instances | network, security |
| `compute-lambda` | Lambda functions | network, security |
| `services-ecr` | ECR repositories | - |
| `services-ecs` | ECS clusters | network, security, services-ecr |
| `services-eks` | EKS clusters | network, security |
| `containers-images` | Container images | services-ecr |
| `containers-apps` | Container apps | services-ecs, containers-images |
| `services-api` | API Gateway | network |
| `storage` | S3 buckets | - |
| `dns` | Route53 zones | - |
| `authentication` | Cognito pools | - |
| `monitoring` | CloudWatch, alarms | - |

## 🔧 Configuration Example

### Deployment Manifest (`deploy/D1PROD/deployment-manifest.yaml`)

```yaml
deployment_id: D1PROD
organization: MyOrg
project: production
domain: example.com

environments:
  prod:
    region: us-east-1
    account_id: "123456789012"

stacks:
  network:
    enabled: true
    layer: 1
    config:
      vpcCidr: "10.0.0.0/16"
      availabilityZones: 3

  database-rds:
    enabled: true
    layer: 2
    dependencies:
      - network
    config:
      instanceClass: "db.t3.medium"
      engine: "postgres"
      subnets: "${network.privateSubnetIds}"  # Cross-stack reference
```

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines before submitting pull requests.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built with [Pulumi](https://www.pulumi.com/)
- Orchestration inspired by enterprise IaC best practices
- Test framework powered by [pytest](https://pytest.org/)

## 📞 Support

For questions, issues, or feature requests, please open an issue on GitHub.

---

**Status**: ✅ Production Ready | 100% Architecture Compliant (v4.0)

🤖 *Platform architecture designed and implemented with Claude Code*
