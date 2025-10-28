# Enhanced Stack Registration - Usage Guide

**Status:** Fully Implemented
**Version:** 2.0
**Coverage:** 87%

---

## Overview

The enhanced stack registration system provides automatic parameter extraction from TypeScript code, template-first validation, and strict enforcement of input/output declarations.

### Key Features

1. **Automated Parameter Extraction** - AST-based parsing extracts inputs and outputs from TypeScript code
2. **Enhanced Template Format** - Templates declare both inputs AND outputs
3. **Template-First Validation** - Code must match template declarations
4. **Strict Export Enforcement** - Outputs must be declared in templates
5. **Pre-Deployment Validation** - Validates code before deployment

---

## Quick Start

### 1. Register a Stack with Auto-Extraction

```bash
# Auto-extract parameters from stack code
cloud register-stack network \
  --description "Core VPC and networking" \
  --dependencies "" \
  --priority 100

# Output:
# Extracting parameters from network...
#   Found 3 input(s) and 2 output(s)
# ✓ Stack 'network' registered successfully
#   Template: cloud/tools/templates/config/network.yaml
#   Parameters: 3 inputs, 2 outputs
```

### 2. Register with Validation

```bash
# Register and validate immediately
cloud register-stack security \
  --description "Security groups and IAM" \
  --dependencies "network" \
  --priority 200 \
  --validate

# Output:
# ✓ Stack 'security' registered successfully
#
# Validating stack code...
# ✓ Validation passed
```

### 3. Validate Existing Stack

```bash
# Validate code against template
cloud validate-stack network

# Output:
# ============================================================
# Validating network against template...
# ✓ Stack 'network' is valid
#   Code matches template declarations
# ============================================================
```

### 4. Deploy with Validation

```bash
# Deploy with automatic code validation
cloud deploy D1BRV40 --environment dev --validate-code

# Output:
# Validating deployment...
# ✓ Manifest and dependencies valid
#
# Validating stack code against templates...
#   Validated: 5 stack(s)
#   Valid: 5/5
# ✓ Code validation passed
```

---

## Enhanced Template Format

### Template Structure

Templates now include both `inputs` and `outputs` sections:

```yaml
name: network
description: Core VPC and networking infrastructure
dependencies: []
priority: 100
parameters:
  inputs:
    vpcCidr:
      type: string
      required: true
      description: VPC CIDR block
    region:
      type: string
      required: false
      default: us-east-1
      description: AWS region
    enableNatGateway:
      type: boolean
      required: false
      default: true
      description: Enable NAT Gateway
  outputs:
    vpcId:
      type: string
      description: VPC ID
    vpcArn:
      type: string
      description: VPC ARN
    subnetIds:
      type: array
      description: List of subnet IDs
```

### Supported Types

**Inputs:**
- `string` - Text values
- `number` - Numeric values
- `boolean` - True/false values
- `object` - Complex objects
- `array` - Lists

**Outputs:**
- All input types plus:
- Pulumi `Output<T>` types (auto-detected)

---

## Parameter Extraction

### How It Works

The parameter extractor scans your TypeScript code and automatically detects:

**Inputs** - From config access calls:
```typescript
const config = new pulumi.Config();
const vpcCidr = config.require("vpcCidr");           // Required string
const region = config.get("region", "us-east-1");     // Optional with default
const port = config.requireNumber("port");            // Required number
const enabled = config.getBoolean("enabled", true);   // Optional boolean
const dbPassword = config.requireSecret("dbPassword"); // Required secret
const settings = config.getObject("settings");        // Object
```

**Outputs** - From export statements:
```typescript
export const vpcId = vpc.id;
export const vpcArn = vpc.arn;
export const subnetIds = subnets.map(s => s.id);
```

### Extraction Details

The extractor analyzes:
- Parameter names
- Types (inferred from method)
- Required vs optional
- Secret flag
- Default values (when provided inline)
- Descriptions (from inline comments)

---

## Validation

### Types of Validation

#### 1. File Structure Validation

```bash
cloud validate-stack network --check-files
```

Checks for:
- `index.ts` exists
- `Pulumi.yaml` exists
- `package.json` exists

#### 2. Template Validation

```bash
cloud validate-stack network
```

Validates:
- **Undeclared inputs** - Used in code but not in template (ERROR)
- **Unused inputs** - Declared in template but not used (WARNING in normal mode, ERROR in strict)
- **Missing outputs** - Declared in template but not exported (ERROR)
- **Undeclared outputs** - Exported but not declared (WARNING in normal mode, ERROR in strict)
- **Type mismatches** - Code type vs template type (WARNING)

#### 3. Strict Validation

```bash
cloud validate-stack network --strict
```

In strict mode:
- Unused inputs become ERRORS
- Undeclared outputs become ERRORS
- All parameters must be documented

### Validation Workflow

```
User runs: cloud deploy D1TEST1 -e dev --validate-code

┌─────────────────────────┐
│  Load Deployment        │
│  Manifest               │
└──────────┬──────────────┘
           │
           v
┌─────────────────────────┐
│  Validate Manifest      │
│  & Dependencies         │
└──────────┬──────────────┘
           │
           v
┌─────────────────────────┐
│  For Each Enabled       │
│  Stack:                 │
│  1. Load template       │
│  2. Extract params      │
│  3. Compare & validate  │
└──────────┬──────────────┘
           │
           v
┌─────────────────────────┐
│  Report Results:        │
│  - Errors               │
│  - Warnings             │
│  - Valid count          │
└──────────┬──────────────┘
           │
           v
    ┌──────┴──────┐
    │             │
    v             v
┌───────┐    ┌───────────┐
│ FAIL  │    │  PROCEED  │
│ EXIT  │    │  DEPLOY   │
└───────┘    └───────────┘
```

---

## Commands Reference

### register-stack

Register a new stack with the platform.

```bash
cloud register-stack <stack-name> [OPTIONS]
```

**Options:**
```
--description, -d TEXT          Stack description [required]
--dependencies TEXT             Comma-separated dependencies
--priority, -p INTEGER          Stack priority (default: 100)
--auto-extract                  Auto-extract parameters (default: true)
--no-auto-extract               Disable auto-extraction
--validate                      Validate code after registration
--strict                        Enable strict validation
--defaults-file TEXT            YAML file with additional config
```

**Examples:**

```bash
# Basic registration with auto-extraction
cloud register-stack network -d "Core networking"

# Register without auto-extraction
cloud register-stack legacy -d "Legacy stack" --no-auto-extract

# Register with validation
cloud register-stack security -d "Security" --validate --strict

# Register with dependencies
cloud register-stack database -d "RDS databases" \
  --dependencies "network,security" \
  --priority 300
```

### validate-stack

Validate a stack's code against template declarations.

```bash
cloud validate-stack <stack-name> [OPTIONS]
```

**Options:**
```
--strict                     Enable strict validation
--check-files                Check required files (default: true)
--no-check-files             Skip file checking
```

**Examples:**

```bash
# Normal validation
cloud validate-stack network

# Strict validation
cloud validate-stack security --strict

# Validation without file checks
cloud validate-stack app --no-check-files
```

**Output:**
```
Validating network against template...

============================================================
✓ Stack 'network' is valid
  Code matches template declarations
============================================================
```

Or with issues:
```
Validating security against template...

============================================================
✗ Stack 'security' validation failed

Errors (2):
  ✗ Input 'securityGroupRules' is used in code but not declared in template [input:securityGroupRules]
  ✗ Output 'securityGroupArn' is declared in template but not exported in code [output:securityGroupArn]

Warnings (1):
  ! Input 'deprecated' is declared in template but not used in code [input:deprecated]
============================================================
```

### list-stacks

List all registered stacks.

```bash
cloud list-stacks
```

**Output:**
```
┌──────────────┬────────────────────────┬──────────────┬──────────┐
│ Stack Name   │ Description            │ Dependencies │ Priority │
├──────────────┼────────────────────────┼──────────────┼──────────┤
│ network      │ Core networking        │ none         │ 100      │
│ security     │ Security groups        │ network      │ 200      │
│ database-rds │ RDS databases          │ network,...  │ 300      │
└──────────────┴────────────────────────┴──────────────┴──────────┘
```

### deploy

Deploy stacks with validation.

```bash
cloud deploy <deployment-id> [OPTIONS]
```

**Options:**
```
--environment, -e TEXT          Environment (default: dev)
--validate-code                 Validate stack code (default: true)
--no-validate-code              Skip code validation
--strict                        Enable strict validation
--parallel, -p INTEGER          Max parallel deployments (default: 3)
--preview                       Preview only, no changes
```

**Examples:**

```bash
# Deploy with validation
cloud deploy D1TEST1 -e dev

# Deploy without validation (not recommended)
cloud deploy D1TEST1 -e dev --no-validate-code

# Deploy with strict validation
cloud deploy D1TEST1 -e prod --strict
```

---

## Real-World Examples

### Example 1: Network Stack

**TypeScript Code** (`stacks/network/index.ts`):
```typescript
import * as pulumi from "@pulumi/pulumi";
import * as aws from "@pulumi/aws";

const config = new pulumi.Config();

// Inputs
const vpcCidr = config.require("vpcCidr");  // VPC CIDR block
const region = config.get("region", "us-east-1");  // AWS region
const enableNatGateway = config.getBoolean("enableNatGateway", true);

// Create VPC
const vpc = new aws.ec2.Vpc("main", {
    cidrBlock: vpcCidr,
    enableDnsHostnames: true,
    enableDnsSupport: true,
    tags: { Name: "main-vpc" }
});

// Outputs
export const vpcId = vpc.id;
export const vpcArn = vpc.arn;
export const vpcCidrBlock = vpc.cidrBlock;
```

**Register the Stack:**
```bash
cloud register-stack network \
  --description "Core VPC and networking" \
  --priority 100 \
  --validate
```

**Generated Template** (`tools/templates/config/network.yaml`):
```yaml
name: network
description: Core VPC and networking
dependencies: []
priority: 100
parameters:
  inputs:
    vpcCidr:
      type: string
      required: true
      secret: false
      description: VPC CIDR block
    region:
      type: string
      required: false
      secret: false
    enableNatGateway:
      type: boolean
      required: false
      secret: false
  outputs:
    vpcId:
      type: string
    vpcArn:
      type: string
    vpcCidrBlock:
      type: string
```

### Example 2: Database Stack

**TypeScript Code** (`stacks/database-rds/index.ts`):
```typescript
import * as pulumi from "@pulumi/pulumi";
import * as aws from "@pulumi/aws";

const config = new pulumi.Config();

// Inputs
const vpcId = config.require("vpcId");
const subnetIds = config.requireObject<string[]>("subnetIds");
const dbName = config.require("dbName");
const dbUsername = config.require("dbUsername");
const dbPassword = config.requireSecret("dbPassword");
const instanceClass = config.get("instanceClass", "db.t3.micro");
const allocatedStorage = config.requireNumber("allocatedStorage");

// Create DB instance
const db = new aws.rds.Instance("main", {
    identifier: dbName,
    engine: "postgres",
    instanceClass: instanceClass,
    allocatedStorage: allocatedStorage,
    username: dbUsername,
    password: dbPassword,
    skipFinalSnapshot: true
});

// Outputs
export const dbEndpoint = db.endpoint;
export const dbArn = db.arn;
export const dbPort = db.port;
```

**Register:**
```bash
cloud register-stack database-rds \
  --description "PostgreSQL RDS database" \
  --dependencies "network,security" \
  --priority 300 \
  --validate --strict
```

### Example 3: Validation Errors

**Scenario:** Code uses undeclared parameter

```typescript
// Code uses parameter not in template
const undeclaredParam = config.require("notInTemplate");
```

**Validation Result:**
```bash
$ cloud validate-stack mystack

============================================================
✗ Stack 'mystack' validation failed

Errors (1):
  ✗ Input 'notInTemplate' is used in code but not declared in template [input:notInTemplate]

Tip: Update your template or remove the unused parameter from code
============================================================
```

**Fix:** Add to template or remove from code

---

## Troubleshooting

### Issue: "Failed to extract parameters from code"

**Cause:** TypeScript file not found or has syntax errors

**Solution:**
- Ensure `index.ts` or `<stack-name>.ts` exists
- Check for TypeScript syntax errors
- Use `--no-auto-extract` to register manually

### Issue: "Input X is used in code but not declared in template"

**Cause:** Code uses a parameter not in the template

**Solution:**
- Add the parameter to the template:
  ```yaml
  parameters:
    inputs:
      X:
        type: string
        required: true
  ```
- Or remove the parameter usage from code

### Issue: "Output Y is declared in template but not exported in code"

**Cause:** Template declares an output that code doesn't export

**Solution:**
- Add export to code:
  ```typescript
  export const Y = value;
  ```
- Or remove from template if not needed

### Issue: Deploy fails validation

**Cause:** One or more stacks have validation errors

**Solution:**
1. Run `cloud validate-stack <name>` for each failing stack
2. Fix reported issues
3. Re-validate: `cloud validate-stack <name>`
4. Retry deployment

---

## Best Practices

### 1. Always Use Auto-Extraction

Let the system extract parameters automatically:
```bash
cloud register-stack mystack -d "Description"
# NOT: --no-auto-extract
```

### 2. Validate Before Deploying

Always run validation before deployment:
```bash
cloud validate-stack mystack
cloud deploy D1TEST1 -e dev
```

### 3. Use Strict Mode for Production

Use strict validation for production stacks:
```bash
cloud register-stack prod-stack -d "Production" --validate --strict
cloud deploy D1PROD1 -e prod --strict
```

### 4. Document Your Parameters

Add descriptions in comments:
```typescript
const vpcCidr = config.require("vpcCidr");  // VPC CIDR block (e.g., 10.0.0.0/16)
```

### 5. Keep Templates in Sync

After changing stack code:
```bash
# Re-register to update template
cloud register-stack mystack -d "Description"

# Validate
cloud validate-stack mystack
```

### 6. Review Warnings

Don't ignore warnings:
```bash
# Review and fix warnings
cloud validate-stack mystack

# Warnings indicate potential issues
```

---

## Migration Guide

### Migrating Existing Stacks

**Step 1:** Register all existing stacks
```bash
# Register without validation first
cloud register-stack network -d "Core networking" --no-validate
cloud register-stack security -d "Security groups" --no-validate
# ... etc
```

**Step 2:** Validate each stack
```bash
cloud validate-stack network
# Fix any issues found
```

**Step 3:** Re-register with validation
```bash
cloud register-stack network -d "Core networking" --validate
```

**Step 4:** Test deployment
```bash
cloud deploy D1TEST1 -e dev --validate-code
```

---

## End of Usage Guide
