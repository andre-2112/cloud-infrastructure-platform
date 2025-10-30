# Installation and Build Guide

**Platform:** cloud-0.7
**Architecture:** 4.6
**Last Updated:** 2025-01-30

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Building a Single Pulumi Stack](#building-a-single-pulumi-stack)
3. [Building All Pulumi Stacks](#building-all-pulumi-stacks)
4. [Building the Core Library](#building-the-core-library)
5. [Building the CLI](#building-the-cli)
6. [Testing and Running the CLI](#testing-and-running-the-cli)
7. [Enhanced Template System](#enhanced-template-system)
8. [Auto-Extraction and Validation](#auto-extraction-and-validation)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

**Node.js and npm:**
- Node.js >= 18.0.0
- npm >= 9.0.0

```bash
# Check versions
node --version
npm --version
```

**Python:**
- Python >= 3.11
- pip >= 21.0

```bash
# Check versions
python --version  # or python3 --version
pip --version     # or pip3 --version
```

**Pulumi CLI:**
- Pulumi >= 3.0.0

```bash
# Check version
pulumi version

# Install if needed
curl -fsSL https://get.pulumi.com | sh
```

**AWS CLI:**
- AWS CLI >= 2.0.0

```bash
# Check version
aws --version

# Configure AWS credentials
aws configure
```

### Optional Software

- **Git** (for version control)
- **Docker** (for containerized testing)

---

## Building a Single Pulumi Stack

### Step-by-Step Guide

Each Pulumi stack is an independent TypeScript project located in `cloud/stacks/<stack-name>/`.

**1. Navigate to the stack directory:**

```bash
cd cloud/stacks/<stack-name>

# Example: Build the network stack
cd cloud/stacks/network
```

**2. Install dependencies:**

```bash
npm install
```

This installs:
- `@pulumi/pulumi` - Pulumi SDK
- `@pulumi/aws` - AWS provider
- TypeScript and type definitions

**3. Build the stack (TypeScript compilation):**

```bash
# Option 1: Using npx tsc directly
npx tsc

# Option 2: Using npm script (if configured)
npm run build

# Option 3: Type-check without emitting files
npx tsc --noEmit
```

**4. Verify the build:**

```bash
# Check that index.ts compiles without errors
# Output directory (if configured) should contain .js files
ls -la bin/  # or dist/ depending on tsconfig.json outDir
```

### Stack Structure

```
cloud/stacks/<stack-name>/
├── index.ts              # Main entry point (AT ROOT!)
├── src/                  # Optional component files
│   ├── vpc.ts
│   ├── subnets.ts
│   └── outputs.ts
├── docs/                 # Stack documentation
├── Pulumi.yaml           # Stack metadata
├── package.json          # NPM dependencies
└── tsconfig.json         # TypeScript configuration
```

### Example: Building the Network Stack

```bash
# Navigate to stack
cd C:/Users/Admin/Documents/Workspace/cloud/stacks/network

# Install dependencies
npm install

# Compile TypeScript
npx tsc --noEmit

# Expected output: No errors
```

### Common Build Errors

**Error: Cannot find module '@pulumi/pulumi'**
```bash
# Solution: Install dependencies
npm install
```

**Error: TS2307: Cannot find module './src/vpc'**
```bash
# Solution: Check that component files exist in src/
ls -la src/
```

**Error: TS2304: Cannot find name 'pulumi'**
```bash
# Solution: Check Pulumi.yaml and package.json are present
ls -la Pulumi.yaml package.json
```

---

## Building All Pulumi Stacks

### Automated Build Scripts

Two automated scripts are provided for building all 16 stacks:

#### Option 1: Python Script (Cross-Platform)

**Location:** `cloud/tools/install/build_all_stacks.py`

```bash
# Navigate to workspace root
cd C:/Users/Admin/Documents/Workspace

# Run build script
python cloud/tools/install/build_all_stacks.py
```

**Features:**
- Builds all 16 stacks sequentially
- Validates stack structure (index.ts at root)
- Runs npm install and TypeScript compilation
- Reports success/failure for each stack
- Provides summary at the end

**Environment Variable:**
```bash
# Optional: Set custom workspace root
export WORKSPACE_ROOT="/path/to/workspace"
python cloud/tools/install/build_all_stacks.py
```

#### Option 2: Bash Script (Linux/macOS/Git Bash)

**Location:** `cloud/tools/install/build_stacks.sh`

```bash
# Navigate to workspace root
cd C:/Users/Admin/Documents/Workspace

# Make script executable (if needed)
chmod +x cloud/tools/install/build_stacks.sh

# Run build script
./cloud/tools/install/build_stacks.sh
```

**Features:**
- Fast parallel execution
- Validates index.ts location
- Suppresses verbose output
- Color-coded status indicators
- Final success/failure count

### Manual Build (All Stacks)

```bash
# Navigate to stacks directory
cd cloud/stacks

# Build all stacks
for stack in network security dns secrets authentication storage database-rds \
             containers-images containers-apps services-ecr services-ecs services-eks \
             services-api compute-ec2 compute-lambda monitoring; do
    echo "Building $stack..."
    cd $stack
    npm install > /dev/null 2>&1
    npx tsc --noEmit
    cd ..
done
```

### Expected Output

```
======================================================================
Building All Pulumi Stacks - Architecture 3.1
======================================================================

Building stack: network
  Running npm install...
  [OK] npm install
  Running TypeScript compilation...
  [OK] TypeScript compilation

Building stack: security
  Running npm install...
  [OK] npm install
  Running TypeScript compilation...
  [OK] TypeScript compilation

... (14 more stacks)

======================================================================
Build Summary
======================================================================
Successful: 16/16
Failed: 0/16

[SUCCESS] All stacks built successfully!
```

---

## Building the Core Library

The core library (`cloud_core`) provides business logic for the platform and must be installed before the CLI.

### Step-by-Step Installation

**1. Navigate to core directory:**

```bash
cd cloud/tools/core
```

**2. Create a Python virtual environment (recommended):**

```bash
# Create venv
python3 -m venv venv

# Activate venv
# On Linux/macOS:
source venv/bin/activate

# On Windows (Git Bash):
source venv/Scripts/activate
```

**3. Install the core library in development mode:**

```bash
# Install with pip
pip install -e .

# This installs:
# - pydantic - Data validation
# - pyyaml - YAML parsing
# - boto3 - AWS SDK
# - All other dependencies
```

**4. Verify installation:**

```bash
# Test import
python -c "from cloud_core.deployment import ConfigGenerator; print('✓ Core library installed')"

# Expected output:
# ✓ Core library installed
```

### Core Library Structure

```
cloud/tools/core/
├── cloud_core/
│   ├── deployment/         # Deployment management
│   ├── orchestrator/       # Dependency resolution, execution
│   ├── runtime/            # Placeholder resolution
│   ├── templates/          # Enhanced template system
│   ├── validation/         # Template-first validation
│   ├── pulumi/             # Pulumi integration
│   └── utils/              # Utilities
├── tests/                  # 393+ tests
├── setup.py
└── requirements.txt
```

---

## Building the CLI

The CLI (`cloud_cli`) is a Python application using Typer framework that wraps the core library.

### Step-by-Step Installation

**1. Navigate to CLI directory:**

```bash
cd cloud/tools/cli
```

**2. Create a Python virtual environment:**

```bash
# Create venv
python3 -m venv venv

# Activate venv
# On Linux/macOS:
source venv/bin/activate

# On Windows (Git Bash):
source venv/Scripts/activate

# On Windows (CMD):
venv\Scripts\activate.bat

# On Windows (PowerShell):
venv\Scripts\Activate.ps1
```

**3. Install core library first (if not already):**

```bash
# From CLI directory
pip install -e ../core

# Or if in separate environments, install core first
cd ../core
pip install -e .
cd ../cli
```

**4. Install the CLI in development mode:**

```bash
# Install with pip
pip install -e .

# This installs:
# - typer[all] - CLI framework
# - cloud_core - Core library (from ../core)
# - rich - Terminal formatting
# - All other dependencies
```

**5. Verify installation:**

```bash
# Check version
python -m cloud_cli.main --version

# Expected output:
# Cloud Infrastructure Orchestration Platform CLI
# Version: 0.7.0
# Architecture: 4.6
# Python: 3.13.x
```

**6. Setup PATH for direct `cloud` command usage (Recommended):**

The `cloud` command is installed in Python's Scripts directory. To use `cloud` directly instead of `python -m cloud_cli.main`, add the Scripts directory to your PATH.

**For Windows (Git Bash / MINGW64):**

```bash
# Find where cloud.exe is installed
find /c/Users/$USER/AppData/Roaming/Python -name "cloud.exe" 2>/dev/null

# Add to .bashrc for permanent access
echo 'export PATH="/c/Users/'$USER'/AppData/Roaming/Python/Python313/Scripts:$PATH"' >> ~/.bashrc

# Reload .bashrc
source ~/.bashrc

# Verify cloud command works
cloud --help
```

**For Linux/macOS:**

```bash
# Find where cloud is installed
which cloud || find ~/.local -name "cloud" 2>/dev/null

# Add to .bashrc or .zshrc
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc  # or ~/.zshrc

# Reload shell configuration
source ~/.bashrc  # or source ~/.zshrc

# Verify cloud command works
cloud --help
```

**For Windows (PowerShell - Permanent):**

```powershell
# Get Python Scripts path
$scriptsPath = python -c "import site; print(site.USER_SITE.replace('site-packages', 'Scripts'))"

# Add to PATH permanently (requires admin)
[Environment]::SetEnvironmentVariable("Path", $env:Path + ";$scriptsPath", "User")

# Reload environment
$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "User")

# Verify
cloud --help
```

**Testing PATH Setup:**

```bash
# Test the cloud command
cloud --help

# If successful, you can now use:
cloud init --help
cloud deploy --help
cloud status --help

# Instead of:
python -m cloud_cli.main init --help
python -m cloud_cli.main deploy --help
python -m cloud_cli.main status --help
```

**Note:** If `cloud --help` fails with "command not found", the PATH setup is incomplete. Use the full Python module invocation as a fallback: `python -m cloud_cli.main`

### Alternative: Global Installation

```bash
# Install globally (not recommended for development)
cd cloud/tools/cli
pip install .

# Or install as editable with link
pip install -e .
```

### CLI Structure

```
cloud/tools/cli/
├── src/
│   └── cloud_cli/
│       ├── main.py              # CLI entry point
│       ├── commands/            # Command implementations
│       ├── orchestrator/        # Deployment orchestration
│       ├── templates/           # Template management
│       ├── deployment/          # Deployment management
│       ├── runtime/             # Runtime resolution
│       ├── pulumi/              # Pulumi integration
│       ├── validation/          # Validation tools
│       └── utils/               # Utilities
├── tests/                       # Test suite
├── requirements.txt             # Dependencies
├── pyproject.toml               # Project configuration
└── setup.py                     # Setup script
```

### Development Dependencies

```bash
# Install with development dependencies
pip install -e ".[dev]"

# This additionally installs:
# - pytest - Testing framework
# - pytest-cov - Coverage reporting
# - mypy - Type checking
# - black - Code formatting
# - ruff - Linting
```

---

## Testing and Running the CLI

### Basic CLI Usage

**1. Activate the virtual environment:**

```bash
cd cloud/tools/cli
source venv/Scripts/activate  # On Windows Git Bash
```

**2. Run CLI commands:**

```bash
# Show help
python -m cloud_cli.main --help

# Show version
python -m cloud_cli.main version

# List deployments (placeholder)
python -m cloud_cli.main list

# Validate a deployment (placeholder)
python -m cloud_cli.main validate D1BRV40
```

### Available Commands

| Command | Description | Status |
|---------|-------------|--------|
| `version` | Show version information | ✅ Implemented |
| `init` | Initialize new deployment | 🚧 Placeholder |
| `deploy` | Deploy all stacks | 🚧 Placeholder |
| `status` | Show deployment status | 🚧 Placeholder |
| `list` | List all deployments | 🚧 Placeholder |
| `validate` | Validate deployment | 🚧 Placeholder |

**Note:** Most commands are placeholders pending full Session 3 implementation.

### Running Tests

**1. Run all tests:**

```bash
cd cloud/tools/cli
source venv/Scripts/activate
python -m pytest tests/ -v
```

**Expected output:**
```
============================= test session starts =============================
platform win32 -- Python 3.13.7, pytest-8.4.2, pluggy-1.6.0
collecting ... collected 10 items

tests/test_utils/test_deployment_id.py::TestDeploymentIdGeneration::test_generate_deployment_id_format PASSED [ 10%]
tests/test_utils/test_deployment_id.py::TestDeploymentIdGeneration::test_generate_deployment_id_uniqueness PASSED [ 20%]
... (8 more tests)

============================= 10 passed in 0.36s ==============================
```

**2. Run specific test module:**

```bash
# Test deployment ID generation
python -m pytest tests/test_utils/test_deployment_id.py -v

# Test manifest validation
python -m pytest tests/test_validation/test_manifest_validator.py -v
```

**3. Run with coverage:**

```bash
# Install pytest-cov first
pip install pytest-cov

# Run with coverage report
python -m pytest tests/ --cov=cloud_cli --cov-report=html --cov-report=term
```

**4. Type checking:**

```bash
# Install mypy first
pip install mypy

# Run type checker
mypy src/cloud_cli/
```

**5. Code formatting:**

```bash
# Install black first
pip install black

# Format code
black src/ tests/

# Check formatting without changes
black --check src/ tests/
```

### Integration Testing

**Test deployment ID generation:**

```bash
python -c "
from cloud_cli.utils.deployment_id import generate_deployment_id, validate_deployment_id
import sys

# Generate 10 IDs
for _ in range(10):
    dep_id = generate_deployment_id()
    is_valid = validate_deployment_id(dep_id)
    print(f'{dep_id}: {\"✓\" if is_valid else \"✗\"}')
    if not is_valid:
        sys.exit(1)

print('All IDs valid!')
"
```

**Test manifest validation:**

```bash
python -c "
from cloud_cli.validation.manifest_validator import DeploymentManifest

manifest = {
    'version': '3.1',
    'deployment_id': 'D1BRV40',
    'organization': 'TestOrg',
    'project': 'test-project',
    'domain': 'test.example.com',
    'template': 'default',
    'environments': {
        'dev': {
            'enabled': True,
            'region': 'us-east-1',
            'account_id': '111111111111'
        }
    },
    'stacks': {}
}

result = DeploymentManifest(**manifest)
print(f'Manifest valid: {result.deployment_id}')
"
```

### Manual Testing Procedures

**1. Test CLI installation:**
```bash
python -m cloud_cli.main --version
```

**2. Test command help:**
```bash
python -m cloud_cli.main --help
python -m cloud_cli.main init --help
python -m cloud_cli.main deploy --help
```

**3. Test utilities:**
```bash
# Test deployment ID generation
python -c "from cloud_cli.utils.deployment_id import generate_deployment_id; print(generate_deployment_id())"

# Test logger
python -c "from cloud_cli.utils.logger import get_logger; logger = get_logger(); logger.info('Test message')"
```

---

## Troubleshooting

### Common Issues

#### Issue: "Module not found" errors

```bash
# Symptom: ImportError: No module named 'cloud_cli'

# Solution 1: Ensure virtual environment is activated
source venv/Scripts/activate

# Solution 2: Reinstall in development mode
pip install -e .

# Solution 3: Check Python path
python -c "import sys; print('\\n'.join(sys.path))"
```

#### Issue: npm install fails for Pulumi stacks

```bash
# Symptom: npm ERR! network errors

# Solution 1: Clear npm cache
npm cache clean --force

# Solution 2: Delete node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Solution 3: Use different registry
npm install --registry=https://registry.npmjs.org/
```

#### Issue: TypeScript compilation errors

```bash
# Symptom: TS2307: Cannot find module

# Solution 1: Check tsconfig.json paths
cat tsconfig.json

# Solution 2: Ensure all dependencies installed
npm install

# Solution 3: Check import statements match file structure
# index.ts should import from "./src/..." if components in src/
```

#### Issue: Permission errors on scripts

```bash
# Symptom: Permission denied when running .sh scripts

# Solution: Make scripts executable
chmod +x cloud/tools/install/build_stacks.sh
```

#### Issue: Python version mismatch

```bash
# Symptom: Python 3.11+ required

# Solution: Use python3 explicitly
python3 --version
python3 -m venv venv
```

### Getting Help

**Check logs:**
```bash
# CLI logs
ls -la ~/.cloud-cli/logs/

# Stack build logs
cat cloud/stacks/<stack-name>/build.log
```

**Verify installation:**
```bash
# Check all prerequisites
node --version
npm --version
python3 --version
pip3 --version
pulumi version
aws --version
```

**Clean and rebuild:**
```bash
# Clean CLI
cd cloud/tools/cli
rm -rf venv
python3 -m venv venv
source venv/Scripts/activate
pip install -e .

# Clean stack
cd cloud/stacks/<stack-name>
rm -rf node_modules package-lock.json bin/
npm install
npx tsc
```

---

## Quick Reference

### Build Single Stack
```bash
cd cloud/stacks/<stack-name>
npm install && npx tsc --noEmit
```

### Build All Stacks
```bash
cd C:/Users/Admin/Documents/Workspace
python cloud/tools/install/build_all_stacks.py
```

### Install CLI
```bash
cd cloud/tools/cli
python3 -m venv venv
source venv/Scripts/activate
pip install -e .
```

### Test CLI
```bash
cd cloud/tools/cli
source venv/Scripts/activate
python -m pytest tests/ -v
```

### Run CLI
```bash
cd cloud/tools/cli
source venv/Scripts/activate
python -m cloud_cli.main --help
```

---

---

## Enhanced Template System

### Understanding Enhanced Templates

Stack templates in v4.0+ include structured parameter declarations with types, defaults, and validation. Templates are located in `cloud/tools/templates/config/`.

See [INSTALL_v4.1_additions.md](INSTALL_v4.1_additions.md) for complete enhanced template documentation.

---

## Auto-Extraction and Validation

### Auto-Extraction System

The auto-extraction system automatically generates stack templates from TypeScript code:

```bash
# Auto-extract and register a stack
python -m cloud_cli.main register-stack <stack-name> --auto-extract
```

### Template-First Validation

Validate that stack code matches its template:

```bash
# Validate a stack
python -m cloud_cli.main validate-stack <stack-name>

# Strict validation
python -m cloud_cli.main validate-stack <stack-name> --strict
```

See [INSTALL_v4.1_additions.md](INSTALL_v4.1_additions.md) for complete auto-extraction and validation documentation.

---

**For additional documentation, see:**
- [Multi_Stack_Architecture.4.6.md](Multi_Stack_Architecture.4.6.md) - Complete architecture
- [Complete_Stack_Management_Guide_v4.6.md](Complete_Stack_Management_Guide_v4.6.md) - Complete workflow guide
- [Stack_Parameters_and_Registration_Guide_v4.6.md](Stack_Parameters_and_Registration_Guide_v4.6.md) - Template system
- [CLI_Commands_Reference.3.1.md](CLI_Commands_Reference.3.1.md) - All CLI commands
- [Directory_Structure_Diagram.4.6.md](Directory_Structure_Diagram.4.6.md) - Directory layout
- [README.md](README.md) - Documentation index

---

**Document Version:** 4.6
**Last Updated:** 2025-01-30
**Platform:** cloud-0.7
**Architecture:** 4.6
