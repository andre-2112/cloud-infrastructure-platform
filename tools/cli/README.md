# Cloud Infrastructure Orchestration Platform CLI

**Version:** 0.7.0
**Architecture:** 3.1
**Status:** Core Implementation Complete (Session 3)

## Overview

The `cloud` CLI is a comprehensive command-line tool for managing cloud infrastructure deployments using the Multi-Stack Architecture 3.1 platform.

## Features

- **Deployment Management**: Initialize, deploy, destroy, and rollback deployments
- **Stack Management**: Register, update, and manage infrastructure stacks
- **Environment Management**: Support for dev, stage, and production environments
- **Template System**: Pre-built and custom deployment templates
- **Validation**: Comprehensive validation of manifests, dependencies, and credentials
- **Monitoring**: Real-time deployment progress and status tracking

## Installation

```bash
# Install in development mode
cd cloud/tools/cli
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .

# Verify installation
cloud --version
# Output: 0.7.0
```

## Session 3 Implementation Status

**Completed in Session 3:**
- ✅ Complete orchestrator engine (dependency resolution, layer calculation, execution)
- ✅ Template management system (loading, generation, rendering)
- ✅ Deployment manager (CRUD operations, state management, config generation)
- ✅ Runtime resolver (placeholder resolution, stack references, AWS queries)
- ✅ Pulumi wrapper (CLI integration, stack operations, state queries)
- ✅ All validators (manifest, dependency, AWS, Pulumi)
- ✅ Core CLI commands: init, deploy, status, list
- ✅ Default template with 16 stacks

**Ready for Session 4:**
- Additional CLI commands (destroy, rollback, stack management, etc.)
- Comprehensive test suite (unit + integration tests)
- REST API implementation
- WebSocket monitoring
- Database integration

## Quick Start

```bash
# 1. Install dependencies
cd cloud/tools/cli
python3 -m venv venv
source venv/bin/activate
pip install -e .

# 2. Initialize a new deployment
cloud init --org MyOrg --project my-project --domain example.com \
  --template default --region us-east-1 --account-dev 123456789012

# 3. Check deployment created
cloud list

# 4. Deploy to development (requires Pulumi CLI and AWS credentials)
cloud deploy D1BRV40 --environment dev --preview  # Preview first
cloud deploy D1BRV40 --environment dev            # Deploy

# 5. Check status
cloud status D1BRV40 --environment dev
```

**Prerequisites:**
- Python 3.11+
- Pulumi CLI installed
- AWS credentials configured
- Pulumi access token set (PULUMI_ACCESS_TOKEN)

## Documentation

See `../../docs/CLI_Commands_Reference.3.1.md` for complete command documentation.

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Type checking
mypy src/

# Code formatting
black src/ tests/
ruff check src/ tests/
```

## Architecture

```
src/
├── main.py                # CLI entry point
├── commands/              # Command implementations
├── orchestrator/          # Deployment orchestration
├── templates/             # Template management
├── deployment/            # Deployment management
├── runtime/               # Runtime resolution
├── pulumi/                # Pulumi integration
├── validation/            # Validation tools
└── utils/                 # Utilities
```

## License

MIT License
