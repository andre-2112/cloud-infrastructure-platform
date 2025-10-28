# Stack Parameters and Registration - Complete Guide

**Platform:** cloud-0.7
**Architecture:** 3.1
**Date:** 2025-10-24
**Purpose:** Comprehensive guide to stack parameters (inputs/outputs) and registration process

---

## Table of Contents

1. [Part 1: Where Stack Parameters Are Declared](#part-1-where-stack-parameters-are-declared)
   - [Input Parameters](#input-parameters)
   - [Output Parameters](#output-parameters)
   - [Parameter Declaration Summary](#parameter-declaration-summary)
2. [Part 2: Stack Registration Deep Dive](#part-2-stack-registration-deep-dive)
   - [Who Creates the Stack Template File?](#who-creates-the-stack-template-file)
   - [Registration Process Flow](#registration-process-flow)
   - [Stack Template File Structure](#stack-template-file-structure)
   - [Automation Possibilities](#automation-possibilities)
   - [Making Templates Authoritative](#making-templates-authoritative)
   - [Declaring Outputs in Templates](#declaring-outputs-in-templates)
   - [Validation and Enforcement](#validation-and-enforcement)

---

## Part 1: Where Stack Parameters Are Declared

### Input Parameters

Input parameters are configuration values that are **passed into** a stack during deployment. They control how the infrastructure is created.

#### 1. Stack Template File (Declaration of Defaults)

**Location:** `./cloud/tools/templates/config/<stack-name>.yaml`

**Created during:** `cloud register-stack` command

**Purpose:** Declare default input parameters for the stack

**Example: network.yaml**
```yaml
# ./cloud/tools/templates/config/network.yaml
name: network
description: Core networking infrastructure
dependencies: []
priority: 100

# Default input parameters
config:
  vpcCidr: "10.0.0.0/16"           # String parameter
  availabilityZones: 3              # Number parameter
  enableNatGateway: true            # Boolean parameter
  natGatewayType: "single"          # Enum-like parameter
  tags:                             # Object parameter
    Environment: "dev"
    ManagedBy: "cloud-0.7"
```

**When it's created:** Once, when you register the stack (one-time setup)

---

#### 2. Deployment Manifest (Override Defaults)

**Location:** `./cloud/deploy/<deployment-id>-<org>-<project>/Deployment_Manifest.yaml`

**Generated during:** `cloud init` command

**Purpose:** Override template defaults with deployment-specific values

**Example:**
```json
{
  "deployment": {
    "id": "D1BRV40",
    "org": "CompanyA",
    "project": "ecommerce"
  },
  "stacks": {
    "network": {
      "enabled": true,
      "dependencies": [],
      "priority": 100,
      "config": {
        "vpcCidr": "10.0.0.0/16",        // From template default
        "availabilityZones": 3,           // From template default
        "enableNatGateway": true          // From template default
      },
      "environments": {
        "dev": {
          "enabled": true,
          "config": {
            "availabilityZones": 2,       // Environment-specific override
            "enableNatGateway": false     // Environment-specific override
          }
        },
        "prod": {
          "enabled": true,
          "config": {
            "availabilityZones": 3,
            "enableNatGateway": true
          }
        }
      }
    }
  }
}
```

**Configuration resolution order (3-tier):**
1. **Template defaults** (from `network.yaml`)
2. **Manifest overrides** (from stack-level `config`)
3. **Runtime resolution** (from environment-specific `config` or runtime placeholders)

---

#### 3. Stack Code (Usage/Consumption)

**Location:** `./cloud/stacks/<stack-name>/index.ts`

**Purpose:** Read input parameters using Pulumi Config API

**Example: network/index.ts**
```typescript
import * as pulumi from '@pulumi/pulumi';
import * as aws from '@pulumi/aws';
import { createVpc } from './src/vpc';
import { createSubnets } from './src/subnets';

// Read configuration values
const config = new pulumi.Config();

// Required parameters (will error if not provided)
const vpcCidr = config.require('vpcCidr');               // String

// Typed required parameters
const availabilityZones = config.requireNumber('availabilityZones');  // Number

// Optional parameters with defaults
const enableNatGateway = config.getBoolean('enableNatGateway') ?? false;  // Boolean
const natGatewayType = config.get('natGatewayType') ?? 'single';         // String with default

// Object parameters
const tags = config.getObject<Record<string, string>>('tags') ?? {};

// Use the parameters
const vpc = createVpc(vpcCidr, tags);
const subnets = createSubnets(vpc.id, vpcCidr, availabilityZones);

// ... rest of stack implementation
```

**How parameters reach the stack code:**

1. CLI generates Pulumi config files: `./cloud/deploy/D1BRV40/.pulumi/config/D1BRV40-network-dev.yaml`
2. Config file contains resolved values:
```yaml
config:
  cloud-network:vpcCidr: "10.0.0.0/16"
  cloud-network:availabilityZones: "2"
  cloud-network:enableNatGateway: "false"
```
3. Pulumi reads this file when executing the stack
4. `pulumi.Config()` provides access to these values

---

### Output Parameters

Output parameters are values that are **exported from** a stack after deployment. They expose resource IDs and other values for use by dependent stacks.

#### 1. Stack Code (Declaration & Export)

**Location:** `./cloud/stacks/<stack-name>/index.ts` or `./cloud/stacks/<stack-name>/src/outputs.ts`

**Purpose:** Declare and export output values

**Method 1: Direct export in index.ts**
```typescript
// ./cloud/stacks/network/index.ts
import * as pulumi from '@pulumi/pulumi';

// ... resource creation ...

// Export outputs (Pulumi automatically registers these)
export const vpcId = vpc.id;
export const vpcCidr = vpc.cidrBlock;
export const publicSubnetIds = pulumi.output(subnets.publicSubnets.map(s => s.id));
export const privateSubnetIds = pulumi.output(subnets.privateSubnets.map(s => s.id));
export const natGatewayIds = natGateways ? pulumi.output(natGateways.map(ng => ng.id)) : undefined;
```

**Method 2: Using helper function (recommended for organization)**
```typescript
// ./cloud/stacks/network/src/outputs.ts
import * as pulumi from '@pulumi/pulumi';

export function exportOutputs(outputs: Record<string, pulumi.Output<any> | any>) {
  for (const [key, value] of Object.entries(outputs)) {
    pulumi.export(key, value);
  }
}

// ./cloud/stacks/network/index.ts
import { exportOutputs } from './src/outputs';

exportOutputs({
  vpcId: vpc.id,
  vpcCidr: vpc.cidrBlock,
  publicSubnetIds: subnets.publicSubnets.map(s => s.id),
  privateSubnetIds: subnets.privateSubnets.map(s => s.id),
});
```

**Where outputs are stored:**
- Pulumi state file: `./cloud/deploy/D1BRV40/.pulumi/stacks/D1BRV40-network-dev.json`
- Accessible via: `pulumi stack output vpcId --stack D1BRV40-network-dev`

---

#### 2. Referenced by Other Stacks (Usage/Consumption)

**Location:** Other stacks' `index.ts`

**Purpose:** Read outputs from dependency stacks

**Method 1: Using DependencyResolver (Recommended)**
```typescript
// ./cloud/stacks/security/index.ts
import * as pulumi from '@pulumi/pulumi';
import * as aws from '@pulumi/aws';
import { DependencyResolver } from '../../../tools/utils/dependency-resolver';

const config = new pulumi.Config();
const deploymentId = config.require('deploymentId');
const environment = config.require('environment');

// Initialize dependency resolver
const resolver = new DependencyResolver(deploymentId, environment);

// Get output from network stack
const vpcId = resolver.get('network', 'vpcId');  // Returns pulumi.Output<string>
const privateSubnetIds = resolver.get('network', 'privateSubnetIds');  // Returns pulumi.Output<string[]>

// Use in resource creation
const securityGroup = new aws.ec2.SecurityGroup('web-sg', {
  vpcId: vpcId,  // Pulumi handles the Output<T> automatically
  description: 'Security group for web servers',
  ingress: [
    { protocol: 'tcp', fromPort: 80, toPort: 80, cidrBlocks: ['0.0.0.0/0'] },
  ],
});
```

**Method 2: Using Pulumi StackReference directly**
```typescript
import * as pulumi from '@pulumi/pulumi';

// Full stack name format: orgName/projectName/deploymentId-stackName-environment
const networkStack = new pulumi.StackReference('MyOrg/my-project/D1BRV40-network-dev');

const vpcId = networkStack.getOutput('vpcId');
const privateSubnetIds = networkStack.getOutput('privateSubnetIds');
```

**Method 3: Using runtime placeholders (resolved by CLI before deployment)**
```yaml
# In manifest
stacks:
  security:
    config:
      vpcId: "{{RUNTIME:network:vpcId}}"  # Resolved by CLI to actual value
```

---

### Parameter Declaration Summary

| Component | Input Parameters | Output Parameters | When Created |
|-----------|------------------|-------------------|--------------|
| **Stack Template** (`network.yaml`) | ✅ Declare defaults | ❌ Not here | During `register-stack` |
| **Deployment Manifest** | ✅ Override defaults | ❌ Not here | During `cloud init` |
| **Stack Code** (`index.ts`) | ✅ Read via `config.require()` | ✅ **Declare via `export`** | When you write the stack |
| **Pulumi State** | ❌ Not stored | ✅ **Stored after deploy** | After `pulumi up` |
| **Other Stack Code** | ❌ Not accessed | ✅ Read via `DependencyResolver.get()` | When you write dependent stacks |

**Workflow Summary:**

1. **Write stack code** → Declare outputs via `export`
2. **Register stack** → Create template with input parameter defaults
3. **Initialize deployment** → Generate manifest from template
4. **Deploy stack** → Pulumi stores outputs in state
5. **Reference in other stacks** → Use `DependencyResolver.get()` to access outputs

---

## Part 2: Stack Registration Deep Dive

### Who Creates the Stack Template File?

**Short answer:** The `cloud register-stack` CLI command creates the stack template file automatically.

**Detailed process:**

1. **Developer writes stack code first**
   - Create `./cloud/stacks/my-new-stack/` directory
   - Write `index.ts` with Pulumi resources
   - Write `Pulumi.yaml` with stack metadata
   - Write `package.json` with dependencies

2. **Developer runs registration command**
   ```bash
   cloud register-stack my-new-stack \
     --description "My custom stack" \
     --dependencies network,security \
     --defaults-file ./my-defaults.yaml  # Optional
   ```

3. **CLI tool generates the template file**
   - Reads `Pulumi.yaml` to get stack name and description
   - Optionally parses `--defaults-file` for default configuration
   - Alternatively prompts user interactively for defaults
   - Creates `./cloud/tools/templates/config/my-new-stack.yaml`
   - Adds stack to platform's stack registry

---

### Registration Process Flow

```
┌─────────────────────────────────────────────────────────────────┐
│  Developer Action: cloud register-stack my-new-stack            │
│                    --defaults-file defaults.yaml                │
└─────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 1: Validate Stack Exists                                  │
│  - Check ./cloud/stacks/my-new-stack/ directory exists          │
│  - Check Pulumi.yaml exists                                     │
│  - Check index.ts exists                                        │
│  - Validate directory structure                                 │
└─────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 2: Extract Stack Metadata                                 │
│  - Parse Pulumi.yaml                                            │
│  - Extract: name, runtime, description                          │
│  - Validate metadata completeness                               │
└─────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 3: Collect Configuration Parameters                       │
│  Option A: From --defaults-file                                 │
│    - Parse YAML file                                            │
│    - Extract all config keys, types, and default values         │
│  Option B: From code analysis (FUTURE ENHANCEMENT)              │
│    - Parse index.ts AST                                         │
│    - Find all config.require() and config.get() calls           │
│    - Infer parameter names and types                            │
│  Option C: Interactive prompts                                  │
│    - Prompt user for parameter name                             │
│    - Prompt for type (string/number/boolean/object)             │
│    - Prompt for default value                                   │
│    - Repeat until user is done                                  │
└─────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 4: Generate Stack Template File                           │
│  - Create YAML structure                                        │
│  - Include: name, description, dependencies, config             │
│  - Write to ./cloud/tools/templates/config/my-new-stack.yaml    │
└─────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 5: Register in Stack Registry                             │
│  - Add entry to ./cloud/tools/templates/registry.json           │
│  - Make stack discoverable by cloud list-stacks                 │
│  - Make stack available for deployment templates                │
└─────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  Output: Stack registered successfully                          │
│  - Template created at: ./cloud/tools/templates/config/...      │
│  - Stack is now available for use in deployments                │
└─────────────────────────────────────────────────────────────────┘
```

---

### Stack Template File Structure

#### Current Structure (Architecture 3.1)

```yaml
# ./cloud/tools/templates/config/network.yaml
name: network
description: Core networking infrastructure
dependencies: []
priority: 100

# Input parameters with defaults
config:
  vpcCidr: "10.0.0.0/16"
  availabilityZones: 3
  enableNatGateway: true
  natGatewayType: "single"
  enableFlowLogs: false
  tags:
    Environment: "dev"
    ManagedBy: "cloud-0.7"
```

#### Enhanced Structure (With Parameter Metadata - Recommended Future Enhancement)

```yaml
# ./cloud/tools/templates/config/network.yaml
name: network
description: Core networking infrastructure
dependencies: []
priority: 100

# Input parameters with full metadata
parameters:
  inputs:
    - name: vpcCidr
      type: string
      required: true
      default: "10.0.0.0/16"
      description: "CIDR block for the VPC"
      validation:
        pattern: "^\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}/\\d{1,2}$"

    - name: availabilityZones
      type: number
      required: true
      default: 3
      description: "Number of availability zones to use"
      validation:
        min: 1
        max: 6

    - name: enableNatGateway
      type: boolean
      required: false
      default: true
      description: "Enable NAT Gateway for private subnets"

    - name: natGatewayType
      type: enum
      required: false
      default: "single"
      description: "NAT Gateway deployment type"
      validation:
        enum: ["single", "per-az", "none"]

  # Output parameters (for validation and documentation)
  outputs:
    - name: vpcId
      type: string
      description: "ID of the created VPC"
      required: true  # Validation: must be exported

    - name: vpcCidr
      type: string
      description: "CIDR block of the VPC"
      required: true

    - name: publicSubnetIds
      type: array
      items: string
      description: "List of public subnet IDs"
      required: true

    - name: privateSubnetIds
      type: array
      items: string
      description: "List of private subnet IDs"
      required: true

    - name: natGatewayIds
      type: array
      items: string
      description: "List of NAT Gateway IDs"
      required: false  # Only if enableNatGateway is true

# Backward compatibility: simple config (deprecated)
config:
  vpcCidr: "10.0.0.0/16"
  availabilityZones: 3
  enableNatGateway: true
```

---

### The defaults-file Format

**Purpose:** Provide input parameter defaults when registering a stack

**Location:** Anywhere (passed as `--defaults-file ./path/to/file.yaml`)

**Format:**

```yaml
# ./stack-defaults.yaml
# Simple format - just values
vpcCidr: "10.0.0.0/16"
availabilityZones: 3
enableNatGateway: true
natGatewayType: "single"
tags:
  Environment: "dev"
  ManagedBy: "cloud-0.7"
```

**Alternative format with metadata:**

```yaml
# ./stack-defaults-enhanced.yaml
parameters:
  - name: vpcCidr
    type: string
    default: "10.0.0.0/16"
    description: "CIDR block for the VPC"

  - name: availabilityZones
    type: number
    default: 3
    description: "Number of availability zones"

  - name: enableNatGateway
    type: boolean
    default: true
    description: "Enable NAT Gateway"
```

**How it's used during registration:**

1. User runs: `cloud register-stack network --defaults-file ./network-defaults.yaml`
2. CLI reads the YAML file
3. CLI extracts parameter names, types, and defaults
4. CLI generates template file with these values
5. Template is saved to `./cloud/tools/templates/config/network.yaml`

---

### Automation Possibilities

#### Question: Can parameter extraction be automated from code?

**Answer: YES - This can be automated by parsing the TypeScript code**

**Method 1: Abstract Syntax Tree (AST) Parsing**

```typescript
// Automated parameter extraction tool
// ./cloud/tools/utils/parameter-extractor.ts

import * as ts from 'typescript';
import * as fs from 'fs';

interface Parameter {
  name: string;
  type: 'string' | 'number' | 'boolean' | 'object' | 'unknown';
  required: boolean;
  defaultValue?: any;
}

export function extractParametersFromStack(stackPath: string): Parameter[] {
  const indexPath = `${stackPath}/index.ts`;
  const sourceCode = fs.readFileSync(indexPath, 'utf-8');

  // Parse TypeScript to AST
  const sourceFile = ts.createSourceFile(
    indexPath,
    sourceCode,
    ts.ScriptTarget.Latest,
    true
  );

  const parameters: Parameter[] = [];

  // Visit each node in the AST
  function visit(node: ts.Node) {
    // Look for config.require() calls
    if (ts.isCallExpression(node)) {
      const expression = node.expression;

      // config.require('paramName')
      if (ts.isPropertyAccessExpression(expression) &&
          expression.expression.getText() === 'config' &&
          expression.name.getText() === 'require') {

        const paramName = node.arguments[0]?.getText().replace(/['"]/g, '');
        parameters.push({
          name: paramName,
          type: 'string',  // Default, could be inferred
          required: true,
        });
      }

      // config.requireNumber('paramName')
      if (ts.isPropertyAccessExpression(expression) &&
          expression.expression.getText() === 'config' &&
          expression.name.getText() === 'requireNumber') {

        const paramName = node.arguments[0]?.getText().replace(/['"]/g, '');
        parameters.push({
          name: paramName,
          type: 'number',
          required: true,
        });
      }

      // config.getBoolean('paramName') ?? defaultValue
      if (ts.isPropertyAccessExpression(expression) &&
          expression.expression.getText() === 'config' &&
          expression.name.getText() === 'getBoolean') {

        const paramName = node.arguments[0]?.getText().replace(/['"]/g, '');

        // Check if there's a default value (?? operator)
        let defaultValue: any;
        if (node.parent && ts.isBinaryExpression(node.parent) &&
            node.parent.operatorToken.kind === ts.SyntaxKind.QuestionQuestionToken) {
          defaultValue = node.parent.right.getText();
        }

        parameters.push({
          name: paramName,
          type: 'boolean',
          required: false,
          defaultValue: defaultValue === 'true',
        });
      }
    }

    ts.forEachChild(node, visit);
  }

  visit(sourceFile);
  return parameters;
}

// Usage in register-stack command
const parameters = extractParametersFromStack('./cloud/stacks/network');
console.log(parameters);
/*
Output:
[
  { name: 'vpcCidr', type: 'string', required: true },
  { name: 'availabilityZones', type: 'number', required: true },
  { name: 'enableNatGateway', type: 'boolean', required: false, defaultValue: false }
]
*/
```

**Method 2: Static Analysis with Comments**

Enhance the code to include JSDoc comments that can be parsed:

```typescript
// ./cloud/stacks/network/index.ts
import * as pulumi from '@pulumi/pulumi';

const config = new pulumi.Config();

/**
 * @param vpcCidr
 * @type string
 * @required true
 * @default "10.0.0.0/16"
 * @description CIDR block for the VPC
 */
const vpcCidr = config.require('vpcCidr');

/**
 * @param availabilityZones
 * @type number
 * @required true
 * @default 3
 * @description Number of availability zones to use
 */
const availabilityZones = config.requireNumber('availabilityZones');
```

**Benefits of automation:**
- ✅ No manual defaults file needed
- ✅ Parameters automatically stay in sync with code
- ✅ Reduces human error
- ✅ Faster registration process

**Implementation plan:**
1. Add AST parser utility to CLI tools
2. Update `register-stack` command to use parser
3. Generate template file from extracted parameters
4. Allow `--defaults-file` as optional override

---

### Making Templates Authoritative

#### Question: Can the template file become the authoritative source of truth?

**Answer: YES - This is recommended and can be implemented**

**Current State (Architecture 3.1):**
- Stack code defines what parameters are used
- Template file documents defaults
- **Code is authoritative** (if code changes, template may be out of sync)

**Proposed: Template-First Approach**

```
┌─────────────────────────────────────────────────────────────────┐
│                   Template File (network.yaml)                   │
│                 [AUTHORITATIVE SOURCE OF TRUTH]                  │
│                                                                  │
│  Defines:                                                        │
│  - Input parameters (name, type, required, default)             │
│  - Output parameters (name, type, description)                  │
│  - Dependencies                                                  │
│  - Validation rules                                             │
└─────────────────────────────────────────────────────────────────┘
                           │
                           │ Enforced by validation
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                Stack Code (index.ts)                             │
│                [IMPLEMENTATION]                                  │
│                                                                  │
│  Must:                                                           │
│  - Use only parameters declared in template                     │
│  - Export all outputs declared in template                      │
│  - Follow parameter types and validation rules                  │
└─────────────────────────────────────────────────────────────────┘
```

**Implementation:**

1. **Update template format** to include output declarations:
```yaml
# network.yaml
name: network
description: Core networking infrastructure
dependencies: []

parameters:
  inputs:
    - name: vpcCidr
      type: string
      required: true
      default: "10.0.0.0/16"

  outputs:  # NEW: Declare expected outputs
    - name: vpcId
      type: string
      description: "ID of the created VPC"
      required: true
    - name: publicSubnetIds
      type: array
      items: string
      required: true
```

2. **Add validation command:** `cloud validate-stack <stack-name>`

```typescript
// Validation logic
async function validateStackAgainstTemplate(stackName: string): Promise<ValidationResult> {
  // 1. Load template
  const template = loadTemplate(stackName);

  // 2. Parse stack code to extract actual parameters used
  const actualInputs = extractParametersFromStack(`./cloud/stacks/${stackName}`);
  const actualOutputs = extractExportsFromStack(`./cloud/stacks/${stackName}`);

  // 3. Validate inputs
  const inputErrors = [];
  for (const declaredInput of template.parameters.inputs) {
    const actualInput = actualInputs.find(i => i.name === declaredInput.name);

    if (declaredInput.required && !actualInput) {
      inputErrors.push(`Required input '${declaredInput.name}' not found in code`);
    }
  }

  for (const actualInput of actualInputs) {
    const declaredInput = template.parameters.inputs.find(i => i.name === actualInput.name);

    if (!declaredInput) {
      inputErrors.push(`Input '${actualInput.name}' used in code but not declared in template`);
    }
  }

  // 4. Validate outputs
  const outputErrors = [];
  for (const declaredOutput of template.parameters.outputs) {
    const actualOutput = actualOutputs.find(o => o.name === declaredOutput.name);

    if (declaredOutput.required && !actualOutput) {
      outputErrors.push(`Required output '${declaredOutput.name}' not exported in code`);
    }
  }

  for (const actualOutput of actualOutputs) {
    const declaredOutput = template.parameters.outputs.find(o => o.name === actualOutput.name);

    if (!declaredOutput) {
      outputErrors.push(`Output '${actualOutput.name}' exported in code but not declared in template`);
    }
  }

  return {
    valid: inputErrors.length === 0 && outputErrors.length === 0,
    inputErrors,
    outputErrors,
  };
}
```

3. **Enforce during registration and deployment:**

```bash
# During registration
cloud register-stack my-new-stack --validate-code

# Output:
# Validating stack code against template...
# ✓ All required inputs are used in code
# ✓ All required outputs are exported in code
# ✗ ERROR: Input 'extraParam' used in code but not declared in template
#
# Registration failed. Fix errors and try again.

# During deployment
cloud deploy D1BRV40 --environment dev

# Output:
# Pre-deployment validation...
# Validating network stack... ✓
# Validating security stack... ✓
# All stacks valid. Starting deployment...
```

**Benefits:**
- ✅ Template becomes documentation and contract
- ✅ Prevents code drift from template
- ✅ Easier to understand what a stack needs/provides
- ✅ Enables better tooling and IDE integration
- ✅ Allows catching errors before deployment

---

### Declaring Outputs in Templates

#### Question: Can output parameters be declared in the template file?

**Answer: YES - This is highly recommended and should be implemented**

**Enhanced Template Format:**

```yaml
# ./cloud/tools/templates/config/network.yaml
name: network
description: Core networking infrastructure
dependencies: []
priority: 100

parameters:
  # Input parameters
  inputs:
    - name: vpcCidr
      type: string
      required: true
      default: "10.0.0.0/16"
      description: "CIDR block for the VPC"
      validation:
        pattern: "^\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}/\\d{1,2}$"

    - name: availabilityZones
      type: number
      required: true
      default: 3
      description: "Number of availability zones"
      validation:
        min: 1
        max: 6

    - name: enableNatGateway
      type: boolean
      required: false
      default: true
      description: "Enable NAT Gateway for private subnets"

  # Output parameters (NEW!)
  outputs:
    - name: vpcId
      type: string
      description: "ID of the created VPC"
      required: true
      usedBy:  # Documentation: which stacks use this output
        - security
        - database-rds
        - compute-ec2

    - name: vpcCidr
      type: string
      description: "CIDR block of the VPC"
      required: true

    - name: publicSubnetIds
      type: array
      items: string
      description: "List of public subnet IDs"
      required: true
      usedBy:
        - compute-ec2
        - services-ecs

    - name: privateSubnetIds
      type: array
      items: string
      description: "List of private subnet IDs"
      required: true
      usedBy:
        - database-rds
        - services-ecs

    - name: natGatewayIds
      type: array
      items: string
      description: "List of NAT Gateway IDs (only if enableNatGateway is true)"
      required: false
      condition: "enableNatGateway == true"
```

**Benefits of declaring outputs in templates:**

1. **Documentation:**
   - Clear contract of what the stack provides
   - Helps dependent stacks know what's available
   - Easier onboarding for new developers

2. **Validation:**
   - Verify stack code actually exports declared outputs
   - Catch missing exports before deployment
   - Prevent breaking changes to outputs

3. **Dependency tracking:**
   - Know which stacks depend on which outputs
   - Safer refactoring (know impact of removing an output)
   - Better error messages when outputs are missing

4. **Tooling:**
   - IDE autocomplete for output names
   - Type checking in dependent stacks
   - Generate documentation automatically

---

### Validation and Enforcement

#### Question: Can registration code enforce that stack exports match declared outputs?

**Answer: YES - This is essential for template-first approach**

**Implementation:**

#### 1. Extract Exports from Stack Code

```typescript
// ./cloud/tools/utils/export-extractor.ts
import * as ts from 'typescript';
import * as fs from 'fs';

interface Export {
  name: string;
  type: string;
  optional: boolean;
}

export function extractExportsFromStack(stackPath: string): Export[] {
  const indexPath = `${stackPath}/index.ts`;
  const sourceCode = fs.readFileSync(indexPath, 'utf-8');

  const sourceFile = ts.createSourceFile(
    indexPath,
    sourceCode,
    ts.ScriptTarget.Latest,
    true
  );

  const exports: Export[] = [];

  function visit(node: ts.Node) {
    // Match: export const vpcId = ...
    if (ts.isVariableStatement(node) &&
        node.modifiers?.some(m => m.kind === ts.SyntaxKind.ExportKeyword)) {

      const declaration = node.declarationList.declarations[0];
      if (declaration.name && ts.isIdentifier(declaration.name)) {
        const name = declaration.name.text;
        const type = inferType(declaration);
        const optional = type.includes('undefined');

        exports.push({ name, type, optional });
      }
    }

    // Match: pulumi.export('vpcId', ...)
    if (ts.isCallExpression(node)) {
      const expression = node.expression;

      if (ts.isPropertyAccessExpression(expression) &&
          expression.expression.getText() === 'pulumi' &&
          expression.name.getText() === 'export') {

        const name = node.arguments[0]?.getText().replace(/['"]/g, '');
        exports.push({
          name,
          type: 'unknown',
          optional: false,
        });
      }
    }

    ts.forEachChild(node, visit);
  }

  visit(sourceFile);
  return exports;
}

function inferType(declaration: ts.VariableDeclaration): string {
  if (declaration.type) {
    return declaration.type.getText();
  }

  // Try to infer from initializer
  if (declaration.initializer) {
    const init = declaration.initializer;

    // pulumi.Output<T> pattern
    if (ts.isCallExpression(init)) {
      return 'pulumi.Output<any>';
    }
  }

  return 'unknown';
}
```

#### 2. Validate Exports Against Template

```typescript
// ./cloud/tools/commands/validate-stack.ts
import { loadStackTemplate } from '../utils/template-loader';
import { extractExportsFromStack } from '../utils/export-extractor';

export async function validateStackExports(stackName: string): Promise<ValidationResult> {
  // Load template
  const template = loadStackTemplate(stackName);

  // Extract actual exports from code
  const actualExports = extractExportsFromStack(`./cloud/stacks/${stackName}`);

  const errors: string[] = [];
  const warnings: string[] = [];

  // Check required outputs are exported
  for (const declaredOutput of template.parameters.outputs) {
    if (!declaredOutput.required) continue;

    const actualExport = actualExports.find(e => e.name === declaredOutput.name);

    if (!actualExport) {
      errors.push(
        `Required output '${declaredOutput.name}' declared in template but not exported in code`
      );
    }
  }

  // Check for undeclared exports (warning, not error)
  for (const actualExport of actualExports) {
    const declaredOutput = template.parameters.outputs.find(o => o.name === actualExport.name);

    if (!declaredOutput) {
      warnings.push(
        `Output '${actualExport.name}' exported in code but not declared in template. ` +
        `Consider adding to template for documentation.`
      );
    }
  }

  return {
    valid: errors.length === 0,
    errors,
    warnings,
  };
}
```

#### 3. Enforce During Registration

```typescript
// ./cloud/tools/commands/register-stack.ts
export async function registerStack(stackName: string, options: RegisterOptions) {
  console.log(`Registering stack: ${stackName}`);

  // 1. Validate stack directory exists
  validateStackDirectory(stackName);

  // 2. Generate or load template
  const template = await generateStackTemplate(stackName, options);

  // 3. VALIDATE: Check stack code matches template
  if (options.validate || options.enforceOutputs) {
    console.log('Validating stack code against template...');

    const validation = await validateStackExports(stackName);

    if (!validation.valid) {
      console.error('✗ Stack validation failed:');
      for (const error of validation.errors) {
        console.error(`  - ${error}`);
      }

      throw new Error('Stack validation failed. Fix errors and try again.');
    }

    if (validation.warnings.length > 0) {
      console.warn('⚠ Warnings:');
      for (const warning of validation.warnings) {
        console.warn(`  - ${warning}`);
      }
    }

    console.log('✓ Stack validation passed');
  }

  // 4. Save template
  saveStackTemplate(stackName, template);

  // 5. Register in stack registry
  addToStackRegistry(stackName);

  console.log(`✓ Stack '${stackName}' registered successfully`);
}
```

#### 4. Usage Examples

```bash
# Register with validation enabled (recommended)
cloud register-stack network \
  --defaults-file ./network-defaults.yaml \
  --validate

# Output:
# Registering stack: network
# Validating stack code against template...
# ✓ All required outputs are exported
# ✓ All required inputs are used
# ✓ Stack validation passed
# Template created: ./cloud/tools/templates/config/network.yaml
# ✓ Stack 'network' registered successfully

# Register with strict mode (fail on warnings)
cloud register-stack network \
  --defaults-file ./network-defaults.yaml \
  --validate \
  --strict

# Update existing stack registration
cloud update-stack network \
  --add-output "availabilityZones:number:Number of AZs used" \
  --validate
```

#### 5. Validate Before Deployment

```bash
# Validate all stacks in deployment
cloud validate D1BRV40 --check-exports

# Output:
# Validating deployment D1BRV40...
#
# Validating stack: network
# ✓ All required inputs present
# ✓ All required outputs exported
#
# Validating stack: security
# ✓ All required inputs present
# ✓ All required outputs exported
# ✓ All dependencies (network) have required outputs
#
# Validating stack: database-rds
# ✓ All required inputs present
# ✓ All required outputs exported
# ✓ All dependencies (network, security) have required outputs
#
# ✓ All stacks valid. Ready for deployment.
```

---

## Summary

### Current State (Architecture 3.1)

**Input parameters:**
1. Declared in stack template (`network.yaml`) - defaults only
2. Overridden in deployment manifest
3. Read in stack code via `pulumi.Config()`

**Output parameters:**
1. Declared and exported in stack code only
2. NOT declared in template
3. Referenced by dependent stacks via `DependencyResolver`

**Registration process:**
- User provides `--defaults-file` or interactive prompts
- CLI generates template file
- Code is authoritative (template is documentation)

### Recommended Enhancements

**1. Automated Parameter Extraction**
- Use AST parsing to extract parameters from code
- Eliminate need for manual defaults file
- Keep template in sync with code automatically

**2. Template-First Approach**
- Declare both inputs AND outputs in template
- Make template the authoritative source of truth
- Validate code against template during registration

**3. Strict Validation**
- Enforce that stack exports match declared outputs
- Catch missing or undeclared outputs before deployment
- Provide clear error messages

**4. Enhanced Template Format**
```yaml
parameters:
  inputs:
    - name, type, required, default, description, validation
  outputs:
    - name, type, required, description, usedBy, condition
```

**5. Validation Commands**
```bash
cloud validate-stack <stack-name>      # Validate code vs template
cloud validate D1BRV40 --check-exports # Validate before deployment
cloud register-stack <name> --validate # Validate during registration
```

### Benefits of Enhancements

- ✅ Template becomes comprehensive documentation
- ✅ Prevents code/template drift
- ✅ Catches errors early (before deployment)
- ✅ Better IDE support and tooling
- ✅ Clearer contracts between stacks
- ✅ Safer refactoring
- ✅ Faster onboarding for new developers

---

**End of Guide**

**Document Version:** 1.0
**Last Updated:** 2025-10-24
**Platform:** cloud-0.7
**Architecture:** 3.1
