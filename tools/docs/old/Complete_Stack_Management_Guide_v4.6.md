# Complete Stack Management Guide v4

**Platform:** cloud-0.7 Enhanced
**Architecture:** 4.5 with Auto-Extraction, Validation, and Dynamic Pulumi.yaml
**Version:** 4.5 (Unified Guide with Cross-Stack Dependencies and Dynamic Pulumi.yaml)
**Date:** 2025-10-30
**Status:** ✅ Fully Implemented (87% Coverage, 422 Tests Passing)

---

## What This Guide Covers

This is the **comprehensive unified guide** for the cloud infrastructure orchestration platform, combining:

- ✅ Templates (Stack and Deployment)
- ✅ Stack Parameters (Inputs and Outputs)
- ✅ Configuration Flow (3-Tier Resolution)
- ✅ Deployment Configs (Runtime Configuration)
- ✅ Enhanced Registration (Auto-Extraction)
- ✅ Template-First Validation
- ✅ Cross-Stack Dependency Outputs (NEW in v4)
- ✅ Full Lifecycle from Registration to Deployment

**New in v4:** Adds comprehensive cross-stack dependency output section with network → database example.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Core Concepts](#core-concepts)
3. [Templates Deep Dive](#templates-deep-dive)
4. [Stack Parameters](#stack-parameters)
5. [Configuration Flow](#configuration-flow)
6. [Enhanced Registration](#enhanced-registration)
7. [Template-First Validation](#template-first-validation)
8. [Deployment Process](#deployment-process)
9. [Cross-Stack References](#cross-stack-references)
10. [Cross-Stack Dependency Outputs (NEW v4)](#cross-stack-dependency-outputs)
11. [Complete Workflow Examples](#complete-workflow-examples)
12. [Command Reference](#command-reference)
13. [Implementation Details](#implementation-details)
14. [Best Practices](#best-practices)
15. [Troubleshooting](#troubleshooting)

---

## Architecture Overview

### The Complete System

```
┌─────────────────────────────────────────────────────────────────┐
│           COMPLETE ARCHITECTURE (v3 UNIFIED)                     │
└─────────────────────────────────────────────────────────────────┘

╔═══════════════════════════════════════════════════════════════╗
║                    LAYER 1: Templates                          ║
╠═══════════════════════════════════════════════════════════════╣
║                                                                ║
║  ┌──────────────────────┐        ┌──────────────────────┐    ║
║  │ Stack Templates      │        │ Deployment Templates │    ║
║  │ (Per-Stack Config)   │        │ (Orchestration)      │    ║
║  │                      │        │                      │    ║
║  │ • Input defaults     │        │ • Stack selection    │    ║
║  │ • Output declarations│        │ • Dependencies       │    ║
║  │ • Type metadata      │        │ • Overrides          │    ║
║  │                      │        │                      │    ║
║  │ tools/templates/     │        │ tools/templates/     │    ║
║  │   config/*.yaml      │        │   default/*.yaml     │    ║
║  └──────────────────────┘        └──────────────────────┘    ║
║                                                                ║
╚═══════════════════════════════════════════════════════════════╝
                              │
                              ▼
╔═══════════════════════════════════════════════════════════════╗
║              LAYER 2: Stack Implementations                    ║
╠═══════════════════════════════════════════════════════════════╣
║                                                                ║
║  ┌──────────────────────────────────────────────────┐         ║
║  │ Stack Code (TypeScript + Pulumi)                 │         ║
║  │                                                   │         ║
║  │  // INPUTS - Read configuration                  │         ║
║  │  const vpcCidr = config.require("vpcCidr");     │         ║
║  │  const region = config.get("region");            │         ║
║  │                                                   │         ║
║  │  // Create resources                             │         ║
║  │  const vpc = new aws.ec2.Vpc(...);              │         ║
║  │                                                   │         ║
║  │  // OUTPUTS - Export values                      │         ║
║  │  export const vpcId = vpc.id;                    │         ║
║  │  export const vpcArn = vpc.arn;                  │         ║
║  │                                                   │         ║
║  │  Location: stacks/*/index.ts                     │         ║
║  └──────────────────────────────────────────────────┘         ║
║                              │                                 ║
║                              ▼                                 ║
║  ┌──────────────────────────────────────────────────┐         ║
║  │ Parameter Extraction & Validation (NEW)          │         ║
║  │                                                   │         ║
║  │  • TypeScriptParser: Extract inputs/outputs     │         ║
║  │  • ParameterExtractor: Generate templates        │         ║
║  │  • StackCodeValidator: Enforce consistency       │         ║
║  └──────────────────────────────────────────────────┘         ║
║                                                                ║
╚═══════════════════════════════════════════════════════════════╝
                              │
                              ▼
╔═══════════════════════════════════════════════════════════════╗
║      LAYER 3: DEPLOYMENT CONFIGS (Runtime Configuration)       ║
╠═══════════════════════════════════════════════════════════════╣
║                                                                ║
║  ┌──────────────────────────────────────────────────┐         ║
║  │ Deployment Manifest (User-Customizable)          │         ║
║  │                                                   │         ║
║  │ • Generated from deployment template             │         ║
║  │ • User overrides for stack configs               │         ║
║  │ • Environment-specific overrides                 │         ║
║  │ • Cross-stack references                         │         ║
║  │                                                   │         ║
║  │ Location: deploy/<id>/deployment-manifest.yaml   │         ║
║  │ Created by: cloud init                           │         ║
║  └──────────────────────────────────────────────────┘         ║
║                              │                                 ║
║                              ▼ (ConfigGenerator)               ║
║  ┌──────────────────────────────────────────────────┐         ║
║  │ Per-Stack Config Files (Generated)               │         ║
║  │                                                   │         ║
║  │ ⭐ THESE ARE WHAT PULUMI ACTUALLY READS ⭐       │         ║
║  │                                                   │         ║
║  │ • One file per stack per environment             │         ║
║  │ • Pulumi config format (key:value)               │         ║
║  │ • Generated by ConfigGenerator from manifest     │         ║
║  │ • Includes all resolved parameters               │         ║
║  │                                                   │         ║
║  │ Example: deploy/<id>/config/network.dev.yaml:    │         ║
║  │   network:vpcCidr: "10.0.0.0/16"                │         ║
║  │   network:availabilityZones: "3"                │         ║
║  │   network:deploymentId: "D1TEST1"               │         ║
║  │   network:environment: "dev"                     │         ║
║  │                                                   │         ║
║  │ Location: deploy/<id>/config/*.yaml              │         ║
║  │ Created by: ConfigGenerator during init          │         ║
║  │ Authoritative: YES - runtime configuration       │         ║
║  └──────────────────────────────────────────────────┘         ║
║                                                                ║
╚═══════════════════════════════════════════════════════════════╝
                              │
                              ▼
╔═══════════════════════════════════════════════════════════════╗
║            LAYER 4: EXECUTION & STATE MANAGEMENT               ║
╠═══════════════════════════════════════════════════════════════╣
║                                                                ║
║  Orchestration:                                                ║
║  • DependencyResolver: Manages stack dependencies             ║
║  • PlaceholderResolver: Resolves cross-stack references       ║
║  • Parallel execution with max concurrency                    ║
║                                                                ║
║  Deployment:                                                   ║
║  • Pulumi up with --config-file <deploy>/<id>/config/*.yaml   ║
║  • Progress monitoring and logging                            ║
║  • Output capture and state updates                           ║
║                                                                ║
║  State Management:                                             ║
║  • Platform state: deploy/<id>/.state/state.yaml              ║
║  • Pulumi state: stacks/<stack>/.pulumi/stacks/*.json         ║
║                                                                ║
╚═══════════════════════════════════════════════════════════════╝
```

### Key Innovation: Template-First with Auto-Extraction

```
         TRADITIONAL APPROACH               v3 ENHANCED APPROACH
         (Manual Templates)                 (Auto-Generated)

┌─────────────────────┐            ┌─────────────────────┐
│ 1. Write Stack Code │            │ 1. Write Stack Code │
└──────────┬──────────┘            └──────────┬──────────┘
           │                                   │
           ▼                                   ▼
┌─────────────────────┐            ┌─────────────────────┐
│ 2. Manually Create  │            │ 2. AUTO-EXTRACT     │◀─ NEW
│    Template         │            │    TypeScriptParser │
│    • Prone to error │            │    • Accurate       │
│    • Gets out of    │            │    • Always in sync │
│      sync           │            └──────────┬──────────┘
└──────────┬──────────┘                       │
           │                                   ▼
           │                        ┌─────────────────────┐
           │                        │ 3. Generate Template│
           │                        │    • inputs: {}     │
           │                        │    • outputs: {}    │
           │                        └──────────┬──────────┘
           │                                   │
           ▼                                   ▼
┌─────────────────────┐            ┌─────────────────────┐
│ 3. Hope They Match  │            │ 4. VALIDATE         │◀─ NEW
│    ❌ No validation │            │    ✓ Enforced match │
└─────────────────────┘            └─────────────────────┘
```

---

## Core Concepts

### 1. Stack Templates vs Deployment Templates

**CRITICAL DISTINCTION:**

| Aspect | Stack Template | Deployment Template |
|--------|---------------|---------------------|
| **Purpose** | Define ONE stack's parameters | Define orchestration of MULTIPLE stacks |
| **Location** | `tools/templates/config/<stack>.yaml` | `tools/templates/default/<template>.yaml` |
| **Created by** | `cloud register-stack` (auto) | Platform developers (manual) |
| **Contains** | Input defaults + Output declarations | Stack selection + Dependencies |
| **Scope** | Single stack | Multiple stacks |
| **Count** | One per stack | Multiple (default, minimal, etc.) |

### 2. Deployment Manifest vs Deployment Configs

**ANOTHER CRITICAL DISTINCTION:**

| Aspect | Deployment Manifest | Deployment Configs |
|--------|--------------------|--------------------|
| **Purpose** | User-editable orchestration file | Runtime config files for Pulumi |
| **Location** | `deploy/<id>/deployment-manifest.yaml` | `deploy/<id>/config/*.yaml` |
| **Created by** | `cloud init` (from deployment template) | ConfigGenerator (from manifest) |
| **Format** | YAML with nested structure | Pulumi config format (key:value) |
| **Editable** | ✅ YES - users customize this | ❌ NO - auto-generated, don't edit |
| **Count** | One per deployment | One per stack per environment |
| **Authoritative** | For orchestration | For Pulumi runtime |

**Example:**

Deployment Manifest (user edits this):
```yaml
# deploy/D1TEST1/deployment-manifest.yaml
stacks:
  network:
    config:
      vpcCidr: "10.0.0.0/16"
      availabilityZones: 2
```

Deployment Config (auto-generated for Pulumi):
```yaml
# deploy/D1TEST1/config/network.dev.yaml
network:vpcCidr: "10.0.0.0/16"
network:availabilityZones: "2"
network:deploymentId: "D1TEST1"
network:environment: "dev"
```

### 3. Parameters: Inputs vs Outputs

**Inputs** - Configuration values passed INTO a stack:
```typescript
// Reading inputs
const vpcCidr = config.require("vpcCidr");
const region = config.get("region", "us-east-1");
```

**Outputs** - Values exported FROM a stack for use by others:
```typescript
// Exporting outputs
export const vpcId = vpc.id;
export const vpcArn = vpc.arn;
```

### 3. The 3-Tier Resolution System

```
Configuration Resolution Order:
===============================

TIER 1: Stack Template Defaults
├─ Source: tools/templates/config/network.yaml
├─ Example: region: us-east-1
└─ Lowest Priority

      ↓ (overridden by)

TIER 2: Deployment Manifest
├─ Source: deploy/D1TEST1/deployment-manifest.yaml
├─ Example: region: us-west-2
└─ Medium Priority

      ↓ (overridden by)

TIER 3: Environment-Specific
├─ Source: deployment-manifest.yaml (environments section)
├─ Example: dev uses us-east-1, prod uses us-west-2
└─ Highest Priority

FINAL VALUE: Environment > Manifest > Template
```

---

## Templates Deep Dive

### Stack Templates (Enhanced v3)

**Purpose:** Declare ALL parameters (inputs AND outputs) for a single stack

**Location:** `tools/templates/config/<stack-name>.yaml`

**Complete Example:**
```yaml
name: network
description: Core VPC and networking infrastructure
dependencies: []
priority: 100

# ENHANCED: Explicit parameter declarations
parameters:
  inputs:
    # Required string input
    vpcCidr:
      type: string
      required: true
      secret: false
      description: VPC CIDR block (e.g., 10.0.0.0/16)

    # Optional input with default
    region:
      type: string
      required: false
      secret: false
      default: us-east-1
      description: AWS region for deployment

    # Required number
    availabilityZones:
      type: number
      required: true
      secret: false
      description: Number of availability zones (2 or 3)

    # Optional boolean
    enableNatGateway:
      type: boolean
      required: false
      secret: false
      default: true
      description: Enable NAT Gateway for private subnets

    # Optional object
    tags:
      type: object
      required: false
      secret: false
      description: Resource tags to apply

  # NEW: Output declarations (must match code exports)
  outputs:
    vpcId:
      type: string
      description: VPC ID for cross-stack references

    vpcArn:
      type: string
      description: VPC ARN

    vpcCidrBlock:
      type: string
      description: Actual CIDR block used

    publicSubnetIds:
      type: array
      description: List of public subnet IDs

    privateSubnetIds:
      type: array
      description: List of private subnet IDs

    natGatewayIds:
      type: array
      description: List of NAT Gateway IDs
```

**Key Features:**
- ✅ AUTO-GENERATED from stack code
- ✅ Type-safe with validation
- ✅ Declares both inputs AND outputs
- ✅ Supports secrets
- ✅ Includes descriptions
- ✅ Serves as documentation

### Deployment Templates

**Purpose:** Define orchestration of multiple stacks

**Location:** `tools/templates/default/<template-name>.yaml`

**Example:**
```yaml
version: "3.1"
template_name: "default"
description: "Full platform deployment"

metadata:
  author: "Platform Team"
  created: "2025-01-15"

stacks:
  network:
    enabled: true
    dependencies: []
    config:
      vpcCidr: "10.0.0.0/16"
      availabilityZones: 3
      enableNatGateway: true

  security:
    enabled: true
    dependencies:
      - network  # Must deploy after network
    config:
      # Reference network outputs
      vpcId: "${network.vpcId}"
      vpcCidrBlock: "${network.vpcCidrBlock}"

  database-rds:
    enabled: false  # Disabled by default
    dependencies:
      - network
      - security
    config:
      vpcId: "${network.vpcId}"
      subnetIds: "${network.privateSubnetIds}"
      securityGroupId: "${security.dbSecurityGroupId}"

  compute-ecs:
    enabled: true
    dependencies:
      - network
      - security
    config:
      vpcId: "${network.vpcId}"
      subnetIds: "${network.publicSubnetIds}"
```

**Key Features:**
- ✅ References multiple stacks
- ✅ Defines dependencies
- ✅ Enables/disables stacks
- ✅ Overrides stack defaults
- ✅ Uses cross-stack references
- ✅ Multiple templates available

---

## Stack Parameters

### Input Parameters

#### Declaration in Stack Template

```yaml
parameters:
  inputs:
    parameterName:
      type: string | number | boolean | object | array
      required: true | false
      secret: true | false
      default: <value>  # Optional
      description: "..."  # Optional
```

#### Supported Types and Usage

**String:**
```yaml
vpcCidr:
  type: string
  required: true
```
```typescript
const vpcCidr = config.require("vpcCidr");
```

**Number:**
```yaml
port:
  type: number
  required: true
```
```typescript
const port = config.requireNumber("port");
```

**Boolean:**
```yaml
enabled:
  type: boolean
  required: false
  default: true
```
```typescript
const enabled = config.getBoolean("enabled") ?? true;
```

**Object:**
```yaml
tags:
  type: object
  required: false
```
```typescript
const tags = config.getObject<Record<string, string>>("tags") ?? {};
```

**Secret:**
```yaml
dbPassword:
  type: string
  required: true
  secret: true
```
```typescript
const dbPassword = config.requireSecret("dbPassword");
```

### Output Parameters (NEW in v3)

#### Declaration in Stack Template

```yaml
parameters:
  outputs:
    outputName:
      type: string | number | boolean | object | array
      description: "..."
```

#### Example

```yaml
parameters:
  outputs:
    vpcId:
      type: string
      description: VPC ID for cross-stack references

    subnetIds:
      type: array
      description: List of subnet IDs

    natGatewayCount:
      type: number
      description: Number of NAT Gateways created
```

**Corresponding Code:**
```typescript
export const vpcId = vpc.id;
export const subnetIds = subnets.map(s => s.id);
export const natGatewayCount = natGateways.length;
```

**Validation:** All exports must be declared, all declarations must be exported.

---

## Configuration Flow

### Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                 COMPLETE CONFIGURATION FLOW                  │
└─────────────────────────────────────────────────────────────┘

PHASE 1: Registration
══════════════════════════════════════════════════════════════

User: cloud register-stack network -d "..."

      ┌──────────────────┐
      │  Stack Code      │
      │  (index.ts)      │
      │  • config.require│
      │  • export const  │
      └────────┬─────────┘
               │
               ▼
      ┌──────────────────┐
      │TypeScriptParser  │
      │ Extract params   │
      └────────┬─────────┘
               │
               ▼
      ┌──────────────────┐
      │  Template        │
      │  parameters:     │
      │    inputs: {}    │
      │    outputs: {}   │
      └────────┬─────────┘
               │
               ▼
      ┌──────────────────┐
      │  Save to:        │
      │  tools/templates/│
      │  config/*.yaml   │
      └──────────────────┘


PHASE 2: Initialization
══════════════════════════════════════════════════════════════

User: cloud init --template default --deployment-id D1TEST1

      ┌──────────────────┐
      │ Load Templates   │
      │ • Deployment     │
      │ • Stack defaults │
      └────────┬─────────┘
               │
               ▼
      ┌──────────────────┐
      │  Merge & Generate│
      │  Manifest        │
      └────────┬─────────┘
               │
               ▼
      ┌──────────────────┐
      │  Save to:        │
      │  deploy/D1TEST1/ │
      │  manifest.yaml   │
      └──────────────────┘


PHASE 3: Deployment
══════════════════════════════════════════════════════════════

User: cloud deploy D1TEST1 -e dev

      ┌──────────────────┐
      │ Load Manifest    │
      └────────┬─────────┘
               │
               ▼
      ┌──────────────────┐
      │ VALIDATE CODE    │◀─ NEW
      │ vs Templates     │
      └────────┬─────────┘
               │ (if valid)
               ▼
      ┌──────────────────┐
      │ Resolve Config   │
      │ (3-Tier)         │
      │ Template→Manifest│
      │ →Environment     │
      └────────┬─────────┘
               │
               ▼
      ┌──────────────────┐
      │ Generate Pulumi  │
      │ Config Files     │
      └────────┬─────────┘
               │
               ▼
      ┌──────────────────┐
      │ Execute Stacks   │
      │ (Orchestrated)   │
      └────────┬─────────┘
               │
               ▼
      ┌──────────────────┐
      │ Capture Outputs  │
      │ Save to State    │
      └──────────────────┘
```

### 3-Tier Resolution in Detail

**Example Scenario:**

**TIER 1 - Stack Template:**
```yaml
# tools/templates/config/network.yaml
parameters:
  inputs:
    vpcCidr:
      default: "10.0.0.0/16"
    availabilityZones:
      default: 3
    enableNatGateway:
      default: true
```
**Result:** vpcCidr=10.0.0.0/16, availabilityZones=3, enableNatGateway=true

**TIER 2 - Deployment Manifest:**
```yaml
# deploy/D1TEST1/deployment-manifest.yaml
stacks:
  network:
    config:
      availabilityZones: 2  # Override template default
```
**Result:** vpcCidr=10.0.0.0/16 (unchanged), availabilityZones=2 (overridden), enableNatGateway=true (unchanged)

**TIER 3 - Environment Override:**
```yaml
stacks:
  network:
    environments:
      dev:
        config:
          enableNatGateway: false  # Dev override
      prod:
        config:
          enableNatGateway: true   # Prod override
```

**Final Resolution:**
- **For dev:** vpcCidr=10.0.0.0/16, availabilityZones=2, enableNatGateway=false
- **For prod:** vpcCidr=10.0.0.0/16, availabilityZones=2, enableNatGateway=true

**Generated Deployment Config Files:**

After `cloud init`, ConfigGenerator creates the actual config files that Pulumi reads:

```yaml
# deploy/D1TEST1/config/network.dev.yaml (what Pulumi reads for dev)
network:vpcCidr: "10.0.0.0/16"
network:availabilityZones: "2"
network:enableNatGateway: "false"
network:deploymentId: "D1TEST1"
network:environment: "dev"
```

```yaml
# deploy/D1TEST1/config/network.prod.yaml (what Pulumi reads for prod)
network:vpcCidr: "10.0.0.0/16"
network:availabilityZones: "2"
network:enableNatGateway: "true"
network:deploymentId: "D1TEST1"
network:environment: "prod"
```

**Pulumi Execution:**
```bash
cd stacks/network
pulumi up --stack dev --config-file ../../deploy/D1TEST1/config/network.dev.yaml
```

**Stack Code Reads:**
```typescript
const config = new pulumi.Config("network");
const vpcCidr = config.require("vpcCidr");  // Gets "10.0.0.0/16"
const azCount = config.requireNumber("availabilityZones");  // Gets 2
const enableNat = config.getBoolean("enableNatGateway");    // Gets false (dev) or true (prod)
```

---

## Enhanced Registration

### Auto-Extraction System

```
┌─────────────────────────────────────────────────────────────┐
│            AUTO-EXTRACTION ARCHITECTURE                      │
└─────────────────────────────────────────────────────────────┘

Stack Code (TypeScript)
         │
         │ Read
         ▼
┌─────────────────────┐
│ TypeScriptParser    │
│                     │
│ Regex Patterns:     │
│ • config.require()  │
│ • config.get()      │
│ • config.*Number()  │
│ • config.*Boolean() │
│ • config.*Secret()  │
│ • export const      │
│                     │
│ esprima (AST):      │
│ • Type analysis     │
│ • Structure         │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ ParseResult         │
│                     │
│ inputs: [           │
│   {name, type,      │
│    required,        │
│    secret,          │
│    default, ...}    │
│ ]                   │
│                     │
│ outputs: [          │
│   {name, type,      │
│    description}     │
│ ]                   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ParameterExtractor   │
│                     │
│ • Find main file    │
│ • Convert to format │
│ • Add metadata      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Template Format     │
│ parameters:         │
│   inputs: {}        │
│   outputs: {}       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│StackTemplateManager │
│ • Validate          │
│ • Save to file      │
└─────────────────────┘
```

### Registration Commands

**Basic Registration:**
```bash
cloud register-stack network --description "Core networking"
```

**Output:**
```
Extracting parameters from network...
  Found 5 input(s) and 4 output(s)
✓ Stack 'network' registered successfully
  Template: tools/templates/config/network.yaml
  Dependencies: none
  Priority: 100
  Parameters: 5 inputs, 4 outputs
```

**With Validation:**
```bash
cloud register-stack security \
  --description "Security groups" \
  --dependencies "network" \
  --validate
```

**With Strict Validation:**
```bash
cloud register-stack prod-stack \
  --description "Production stack" \
  --dependencies "network,security" \
  --priority 300 \
  --validate \
  --strict
```

**All Options:**
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

---

## Template-First Validation

### Validation System

```
┌─────────────────────────────────────────────────────────────┐
│                VALIDATION ARCHITECTURE                       │
└─────────────────────────────────────────────────────────────┘

Stack Code              Stack Template
     │                        │
     │ Extract                │ Load
     │                        │
     ▼                        ▼
┌──────────┐            ┌──────────┐
│Code Params│            │Template  │
│inputs: {}│            │Params    │
│outputs:{}│            │inputs: {}│
└─────┬────┘            │outputs:{}│
      │                 └─────┬────┘
      │                       │
      └───────────┬───────────┘
                  │
                  ▼
         ┌──────────────────┐
         │StackCodeValidator│
         │                  │
         │ Compare:         │
         │ • Input names    │
         │ • Output names   │
         │ • Types          │
         │ • Required flags │
         │                  │
         │ Apply Rules:     │
         │ • Normal mode    │
         │ • Strict mode    │
         └────────┬─────────┘
                  │
                  ▼
         ┌──────────────────┐
         │ValidationResult  │
         │                  │
         │ valid: bool      │
         │ errors: []       │
         │ warnings: []     │
         └──────────────────┘
```

### Validation Rules

| Rule | Condition | Normal Mode | Strict Mode |
|------|-----------|-------------|-------------|
| **R1** | Input used in code but not declared in template | ✗ ERROR | ✗ ERROR |
| **R2** | Input declared in template but not used in code | ⚠ WARNING | ✗ ERROR |
| **R3** | Output declared in template but not exported in code | ✗ ERROR | ✗ ERROR |
| **R4** | Output exported in code but not declared in template | ⚠ WARNING | ✗ ERROR |
| **R5** | Type mismatch between code and template | ⚠ WARNING | ⚠ WARNING |
| **R6** | Required flag mismatch | ⚠ WARNING | ⚠ WARNING |

### Validation Commands

**Validate Single Stack:**
```bash
cloud validate-stack network
```

**Output (Success):**
```
Validating network against template...

============================================================
✓ Stack 'network' is valid
  Code matches template declarations
============================================================
```

**Output (With Issues):**
```
Validating security against template...

============================================================
✗ Stack 'security' validation failed

Errors (2):
  ✗ Input 'unknownParam' is used in code but not declared in template [input:unknownParam]
  ✗ Output 'sgArn' is declared in template but not exported in code [output:sgArn]

Warnings (1):
  ! Input 'deprecatedFlag' is declared in template but not used in code [input:deprecatedFlag]
============================================================
```

**Strict Mode:**
```bash
cloud validate-stack security --strict
```
(Warnings become errors in strict mode)

---

## Deployment Process

### Complete Deployment Flow

```
┌─────────────────────────────────────────────────────────────┐
│              COMPLETE DEPLOYMENT FLOW                        │
└─────────────────────────────────────────────────────────────┘

USER ACTION: cloud deploy D1TEST1 -e dev

┌─────────────────────┐
│ 1. Load Manifest    │
│    • Validate YAML  │
│    • Check structure│
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 2. Validate Manifest│
│    • Dependencies   │
│    • Stack config   │
│    • Environments   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 3. VALIDATE CODE    │◀─── NEW in v3
│    • Load templates │
│    • Extract params │
│    • Compare        │
│    • Report issues  │
└──────────┬──────────┘
           │ (if valid)
           ▼
┌─────────────────────┐
│ 4. Build Dep Graph  │
│    • Resolve order  │
│    • Check cycles   │
│    • Plan layers    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 5. Generate Configs │
│    • 3-tier resolve │
│    • Placeholders   │
│    • Cross-refs     │
│    • Pulumi config  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 6. Execute Stacks   │
│    • Parallel exec  │
│    • Respect deps   │
│    • Capture output │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 7. Update State     │
│    • Save outputs   │
│    • Update status  │
│    • Record timing  │
└─────────────────────┘
```

### Deployment Commands

**Basic Deployment:**
```bash
cloud deploy D1TEST1 -e dev
```

**Without Code Validation (Not Recommended):**
```bash
cloud deploy D1TEST1 -e dev --no-validate-code
```

**With Strict Validation:**
```bash
cloud deploy D1PROD1 -e prod --strict
```

**Preview Mode:**
```bash
cloud deploy D1TEST1 -e dev --preview
```

**All Options:**
```
--environment, -e TEXT          Environment (default: dev)
--validate-code                 Validate stack code (default: true)
--no-validate-code              Skip code validation
--strict                        Enable strict validation
--parallel, -p INTEGER          Max parallel deployments (default: 3)
--preview                       Preview only, no changes
```

---

## Cross-Stack References

### How Outputs Flow Between Stacks

```
STEP 1: Deploy Network Stack
═════════════════════════════════════════════════════════════

┌──────────────────┐
│  network stack   │
│                  │
│  Deploys:        │
│  • VPC           │
│  • Subnets       │
│  • NAT Gateways  │
│                  │
│  Exports:        │
│  vpcId: vpc-123  │
│  subnetIds: [...] │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Pulumi State    │
│  Saves outputs   │
└────────┬─────────┘
         │
         │
STEP 2: Deploy Security Stack
         │
         ▼
┌──────────────────┐
│DependencyResolver│
│ Read network     │
│ outputs from     │
│ Pulumi state     │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  security stack  │
│                  │
│  Receives:       │
│  vpcId: vpc-123  │
│  subnetIds: [...] │
│                  │
│  Creates:        │
│  • Security      │
│    groups        │
└──────────────────┘
```

### Referencing Outputs in Manifest

```yaml
stacks:
  network:
    enabled: true
    dependencies: []
    config:
      vpcCidr: "10.0.0.0/16"
      availabilityZones: 3

  security:
    enabled: true
    dependencies:
      - network  # Must deploy after network
    config:
      # Reference network outputs using ${stack.output} syntax
      vpcId: "${network.vpcId}"
      subnetIds: "${network.subnetIds}"

  database-rds:
    enabled: true
    dependencies:
      - network
      - security
    config:
      # Reference outputs from multiple stacks
      vpcId: "${network.vpcId}"
      privateSubnetIds: "${network.privateSubnetIds}"
      securityGroupId: "${security.dbSecurityGroupId}"
```

### Using Referenced Values in Code

```typescript
// database-rds/index.ts
const config = new pulumi.Config();

// These values are resolved from referenced stack outputs
const vpcId = config.require("vpcId");  // From network.vpcId
const subnetIds = config.requireObject<string[]>("privateSubnetIds");  // From network
const securityGroupId = config.require("securityGroupId");  // From security

// Create DB subnet group
const subnetGroup = new aws.rds.SubnetGroup("db", {
    subnetIds: subnetIds  // Uses resolved subnet IDs
});

// Create DB instance
const db = new aws.rds.Instance("main", {
    vpcSecurityGroupIds: [securityGroupId],  // Uses resolved security group
    dbSubnetGroupName: subnetGroup.name
});
```

---

## Cross-Stack Dependency Outputs

### Overview

This section provides a comprehensive guide on how to declare, reference, and use dependency outputs between stacks. We'll use a real-world example: a **database stack** that depends on **networking stack outputs** (specifically, subnet IDs).

### The Problem

When deploying infrastructure, stacks often depend on resources created by other stacks:

- **Database** needs subnet IDs from **Network**
- **Application** needs load balancer ARN from **Compute**
- **Security** needs VPC ID from **Network**

The platform provides a complete solution for this through:
1. Output declarations in stack templates
2. Dependency declarations
3. Runtime resolution via DependencyResolver
4. Type-safe references in deployment manifests

### Complete Example: Network → Database

#### Step 1: Network Stack Template (Declares Outputs)

The network stack declares what outputs it provides:

```yaml
# tools/templates/config/network.yaml
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

    availabilityZones:
      type: number
      required: true
      description: Number of availability zones

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

    publicSubnetIds:
      type: array
      description: List of public subnet IDs

    privateSubnetIds:
      type: array
      description: List of private subnet IDs (for databases)

    availabilityZoneNames:
      type: array
      description: List of AZ names used
```

#### Step 2: Network Stack Code (Exports Outputs)

The network stack implementation exports these values:

```typescript
// stacks/network/index.ts
import * as pulumi from "@pulumi/pulumi";
import * as aws from "@pulumi/aws";

const config = new pulumi.Config();

// INPUTS
const vpcCidr = config.require("vpcCidr");
const azCount = config.requireNumber("availabilityZones");
const enableNatGateway = config.getBoolean("enableNatGateway") ?? false;

// Get available AZs
const availableAzs = aws.getAvailabilityZones({
    state: "available"
});

// Create VPC
const vpc = new aws.ec2.Vpc("main", {
    cidrBlock: vpcCidr,
    enableDnsHostnames: true,
    enableDnsSupport: true,
    tags: { Name: "main-vpc" }
});

// Create public subnets
const publicSubnets: aws.ec2.Subnet[] = [];
for (let i = 0; i < azCount; i++) {
    const subnet = new aws.ec2.Subnet(`public-${i}`, {
        vpcId: vpc.id,
        cidrBlock: `10.0.${i}.0/24`,
        availabilityZone: availableAzs.then(azs => azs.names[i]),
        mapPublicIpOnLaunch: true,
        tags: { Name: `public-subnet-${i}`, Type: "public" }
    });
    publicSubnets.push(subnet);
}

// Create private subnets (for databases)
const privateSubnets: aws.ec2.Subnet[] = [];
for (let i = 0; i < azCount; i++) {
    const subnet = new aws.ec2.Subnet(`private-${i}`, {
        vpcId: vpc.id,
        cidrBlock: `10.0.${100 + i}.0/24`,
        availabilityZone: availableAzs.then(azs => azs.names[i]),
        tags: { Name: `private-subnet-${i}`, Type: "private" }
    });
    privateSubnets.push(subnet);
}

// OUTPUTS - Export values for dependent stacks
export const vpcId = vpc.id;
export const vpcArn = vpc.arn;
export const publicSubnetIds = pulumi.output(publicSubnets.map(s => s.id));
export const privateSubnetIds = pulumi.output(privateSubnets.map(s => s.id));
export const availabilityZoneNames = availableAzs.then(azs => azs.names.slice(0, azCount));
```

#### Step 3: Database Stack Template (Declares Dependencies)

The database stack declares its dependency on network and what inputs it needs:

```yaml
# tools/templates/config/database-rds.yaml
name: database-rds
description: RDS PostgreSQL database
dependencies:
  - network  # ⭐ Declares dependency on network stack
priority: 300

parameters:
  inputs:
    # Database-specific inputs
    dbName:
      type: string
      required: true
      description: Database name

    dbUsername:
      type: string
      required: true
      description: Master username

    dbPassword:
      type: string
      required: true
      secret: true
      description: Master password

    instanceClass:
      type: string
      required: false
      default: "db.t3.micro"
      description: RDS instance class

    allocatedStorage:
      type: number
      required: false
      default: 20
      description: Storage in GB

    # ⭐ Inputs that will come from network stack outputs
    vpcId:
      type: string
      required: true
      description: VPC ID (from network stack)

    privateSubnetIds:
      type: array
      required: true
      description: Private subnet IDs for DB subnet group (from network stack)

  outputs:
    dbEndpoint:
      type: string
      description: Database endpoint

    dbArn:
      type: string
      description: Database ARN

    dbPort:
      type: number
      description: Database port
```

#### Step 4: Database Stack Code (Uses Dependency Outputs)

The database stack reads the subnet IDs that will be resolved from the network stack:

```typescript
// stacks/database-rds/index.ts
import * as pulumi from "@pulumi/pulumi";
import * as aws from "@pulumi/aws";

const config = new pulumi.Config();

// Database-specific inputs
const dbName = config.require("dbName");
const dbUsername = config.require("dbUsername");
const dbPassword = config.requireSecret("dbPassword");
const instanceClass = config.get("instanceClass") || "db.t3.micro";
const allocatedStorage = config.requireNumber("allocatedStorage");

// ⭐ Inputs from network stack (resolved by DependencyResolver)
const vpcId = config.require("vpcId");
const privateSubnetIds = config.requireObject<string[]>("privateSubnetIds");

// Create DB subnet group using subnets from network stack
const dbSubnetGroup = new aws.rds.SubnetGroup("main", {
    name: `${dbName}-subnet-group`,
    subnetIds: privateSubnetIds,  // ⭐ Uses network stack's private subnets
    tags: {
        Name: `${dbName}-subnet-group`,
        ManagedBy: "Pulumi"
    }
});

// Create security group in the VPC from network stack
const dbSecurityGroup = new aws.ec2.SecurityGroup("db", {
    name: `${dbName}-sg`,
    vpcId: vpcId,  // ⭐ Uses network stack's VPC ID
    description: "Security group for RDS database",
    ingress: [{
        protocol: "tcp",
        fromPort: 5432,
        toPort: 5432,
        cidrBlocks: ["10.0.0.0/16"]  // Allow from VPC
    }],
    tags: { Name: `${dbName}-sg` }
});

// Create RDS instance
const db = new aws.rds.Instance("main", {
    identifier: dbName,
    engine: "postgres",
    engineVersion: "14.7",
    instanceClass: instanceClass,
    allocatedStorage: allocatedStorage,
    dbName: dbName,
    username: dbUsername,
    password: dbPassword,
    dbSubnetGroupName: dbSubnetGroup.name,  // Uses subnet group with network subnets
    vpcSecurityGroupIds: [dbSecurityGroup.id],
    skipFinalSnapshot: true,
    tags: {
        Name: dbName,
        ManagedBy: "Pulumi"
    }
});

// OUTPUTS
export const dbEndpoint = db.endpoint;
export const dbArn = db.arn;
export const dbPort = db.port;
```

#### Step 5: Deployment Manifest (References Outputs)

The deployment manifest uses `${stack.output}` syntax to reference outputs:

```yaml
# deploy/D1PROD1/deployment-manifest.yaml
deployment:
  id: D1PROD1
  org: MyCompany
  project: MyApp
  region: us-east-1

stacks:
  network:
    enabled: true
    dependencies: []
    priority: 100
    config:
      vpcCidr: "10.0.0.0/16"
      availabilityZones: 3
      enableNatGateway: true

  database-rds:
    enabled: true
    dependencies:
      - network  # ⭐ Deploy after network
    priority: 300
    config:
      # Database-specific config
      dbName: "myappdb"
      dbUsername: "admin"
      dbPassword: "${env.DB_PASSWORD}"  # From environment variable
      instanceClass: "db.t3.small"
      allocatedStorage: 100

      # ⭐ Reference network stack outputs
      vpcId: "${network.vpcId}"
      privateSubnetIds: "${network.privateSubnetIds}"
```

#### Step 6: Config Generation (Runtime Resolution)

When you run `cloud deploy`, the ConfigGenerator resolves the references:

**Before Resolution (Deployment Manifest):**
```yaml
vpcId: "${network.vpcId}"
privateSubnetIds: "${network.privateSubnetIds}"
```

**After Resolution (Deployment Config for Pulumi):**
```yaml
# deploy/D1PROD1/config/database-rds.dev.yaml
database-rds:dbName: "myappdb"
database-rds:dbUsername: "admin"
database-rds:dbPassword: "secret123"
database-rds:instanceClass: "db.t3.small"
database-rds:allocatedStorage: "100"
database-rds:vpcId: "vpc-0a1b2c3d4e5f6g7h8"  # ⭐ Resolved from network stack
database-rds:privateSubnetIds: ["subnet-111", "subnet-222", "subnet-333"]  # ⭐ Resolved
database-rds:deploymentId: "D1PROD1"
database-rds:environment: "dev"
```

#### Step 7: Deployment Flow

```
┌────────────────────────────────────────────────────────────────┐
│                    DEPLOYMENT EXECUTION                         │
└────────────────────────────────────────────────────────────────┘

STEP 1: Deploy Network Stack
═══════════════════════════════════════════════════════════════
$ cloud deploy D1PROD1 -e dev

• Load deployment manifest
• Resolve dependencies: network has no dependencies
• Deploy network stack:
    cd stacks/network
    pulumi up --stack dev \
      --config-file ../../deploy/D1PROD1/config/network.dev.yaml

✓ Network deployed
  Outputs captured:
    vpcId: vpc-0a1b2c3d4e5f6g7h8
    privateSubnetIds: ["subnet-111", "subnet-222", "subnet-333"]

STEP 2: Resolve Database Dependencies
═══════════════════════════════════════════════════════════════
• DependencyResolver reads network outputs from Pulumi state
• PlaceholderResolver replaces ${network.vpcId} → "vpc-0a1b2c..."
• PlaceholderResolver replaces ${network.privateSubnetIds} → [...]
• ConfigGenerator creates database-rds.dev.yaml with resolved values

STEP 3: Deploy Database Stack
═══════════════════════════════════════════════════════════════
• Deploy database-rds stack:
    cd stacks/database-rds
    pulumi up --stack dev \
      --config-file ../../deploy/D1PROD1/config/database-rds.dev.yaml

✓ Database deployed
  Used network outputs:
    vpcId: vpc-0a1b2c3d4e5f6g7h8 (from network)
    privateSubnetIds: 3 subnets (from network)

  Outputs captured:
    dbEndpoint: myappdb.abc123.us-east-1.rds.amazonaws.com:5432
    dbArn: arn:aws:rds:us-east-1:123456789012:db:myappdb
```

### Key Points

1. **Template Declarations:**
   - Network stack template declares `privateSubnetIds` as an output
   - Database stack template declares `privateSubnetIds` as an input
   - Database stack template lists `network` in dependencies

2. **Code Implementation:**
   - Network code exports `privateSubnetIds` via `export const`
   - Database code reads `privateSubnetIds` via `config.requireObject()`
   - No direct coupling between stack code files

3. **Deployment Manifest:**
   - Uses `${network.privateSubnetIds}` syntax for references
   - Dependency order ensures network deploys first
   - Human-readable and easy to understand

4. **Runtime Resolution:**
   - DependencyResolver reads outputs from deployed network stack
   - PlaceholderResolver replaces `${...}` with actual values
   - ConfigGenerator creates Pulumi config files with resolved values

5. **Type Safety:**
   - Templates declare types (string, array, etc.)
   - Validation ensures types match
   - Runtime checks prevent type mismatches

### Common Patterns

#### Pattern 1: Single Value Reference

```yaml
# Deployment manifest
stacks:
  security:
    config:
      vpcId: "${network.vpcId}"  # Single string value
```

#### Pattern 2: Array Reference

```yaml
# Deployment manifest
stacks:
  database-rds:
    config:
      subnetIds: "${network.privateSubnetIds}"  # Array of strings
```

#### Pattern 3: Multiple Dependencies

```yaml
# Deployment manifest
stacks:
  application:
    dependencies:
      - network
      - security
      - database-rds
    config:
      vpcId: "${network.vpcId}"
      securityGroupId: "${security.appSecurityGroupId}"
      dbEndpoint: "${database-rds.dbEndpoint}"
```

#### Pattern 4: Conditional Output Usage

```typescript
// In dependent stack
const loadBalancerArn = config.get("loadBalancerArn");
if (loadBalancerArn) {
    // Use load balancer if provided
    // Reference came from ${compute.loadBalancerArn}
}
```

### Troubleshooting

**Problem:** `Output '${network.privateSubnetIds}' not found`

**Cause:** Network stack hasn't been deployed yet or output name is incorrect

**Solution:**
1. Check network stack is deployed: `pulumi stack output --stack dev`
2. Verify output name matches template: `privateSubnetIds` vs `private_subnet_ids`
3. Check dependency order in manifest

**Problem:** `Type mismatch: expected array, got string`

**Cause:** Output type doesn't match input type declaration

**Solution:**
1. Check network template: `outputs.privateSubnetIds.type: array`
2. Check database template: `inputs.privateSubnetIds.type: array`
3. Ensure stack code exports correct type: `pulumi.output(subnets.map(...))`

**Problem:** `Cannot read property 'privateSubnetIds' of undefined`

**Cause:** DependencyResolver failed to read network stack state

**Solution:**
1. Verify network stack exists: `cd stacks/network && pulumi stack ls`
2. Check Pulumi state accessibility
3. Verify stack name matches: `network` vs `networking`

---

## Complete Workflow Examples

### Example 1: Full Three-Stack Deployment

**Scenario:** Deploy network → security → database

#### Step 1: Register Stacks

```bash
# Register network stack
$ cloud register-stack network \
    --description "Core VPC and networking" \
    --priority 100

Extracting parameters from network...
  Found 5 input(s) and 4 output(s)
✓ Stack 'network' registered successfully


# Register security stack
$ cloud register-stack security \
    --description "Security groups and IAM roles" \
    --dependencies "network" \
    --priority 200 \
    --validate

Extracting parameters from security...
  Found 3 input(s) and 2 output(s)
✓ Stack 'security' registered successfully

Validating stack code...
✓ Validation passed


# Register database stack
$ cloud register-stack database-rds \
    --description "PostgreSQL RDS database" \
    --dependencies "network,security" \
    --priority 300 \
    --validate --strict

Extracting parameters from database-rds...
  Found 6 input(s) and 3 output(s)
✓ Stack 'database-rds' registered successfully

Validating stack code (strict mode)...
✓ Validation passed
```

#### Step 2: Review Generated Templates

```bash
$ cat tools/templates/config/network.yaml
```

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
    region:
      type: string
      required: false
      secret: false
      default: us-east-1
    availabilityZones:
      type: number
      required: true
      secret: false
    enableNatGateway:
      type: boolean
      required: false
      secret: false
      default: true
    tags:
      type: object
      required: false
      secret: false
  outputs:
    vpcId:
      type: string
      description: VPC ID
    vpcArn:
      type: string
      description: VPC ARN
    publicSubnetIds:
      type: array
      description: Public subnet IDs
    privateSubnetIds:
      type: array
      description: Private subnet IDs
```

#### Step 3: Initialize Deployment

```bash
$ cloud init \
    --template default \
    --deployment-id D1TEST1 \
    --org CompanyA \
    --project ecommerce

✓ Deployment 'D1TEST1' created
  Directory: deploy/D1TEST1-CompanyA-ecommerce/
  Manifest: deployment-manifest.yaml
  Enabled stacks: network, security, database-rds
```

#### Step 4: Customize Deployment Manifest

Edit `deploy/D1TEST1-CompanyA-ecommerce/deployment-manifest.yaml`:

```yaml
deployment:
  id: D1TEST1
  org: CompanyA
  project: ecommerce

stacks:
  network:
    enabled: true
    dependencies: []
    priority: 100
    config:
      vpcCidr: "10.1.0.0/16"
      availabilityZones: 3
      enableNatGateway: true
      tags:
        Environment: dev
        Project: ecommerce
    environments:
      dev:
        enabled: true
        config:
          availabilityZones: 2
          enableNatGateway: false
      prod:
        enabled: true
        config:
          availabilityZones: 3
          enableNatGateway: true

  security:
    enabled: true
    dependencies:
      - network
    priority: 200
    config:
      vpcId: "${network.vpcId}"  # Reference network output
      vpcCidrBlock: "${network.vpcCidrBlock}"
    environments:
      dev:
        enabled: true
      prod:
        enabled: true

  database-rds:
    enabled: true
    dependencies:
      - network
      - security
    priority: 300
    config:
      dbName: "myapp"
      dbUsername: "admin"
      # dbPassword provided via environment variable
      instanceClass: "db.t3.micro"
      allocatedStorage: 20
      subnetIds: "${network.privateSubnetIds}"  # Reference
      securityGroupId: "${security.dbSecurityGroupId}"  # Reference
    environments:
      dev:
        enabled: true
        config:
          instanceClass: "db.t3.micro"
          allocatedStorage: 20
      prod:
        enabled: true
        config:
          instanceClass: "db.m5.large"
          allocatedStorage: 100
```

#### Step 5: Validate Deployment

```bash
$ cloud deploy D1TEST1 -e dev --preview

Validating deployment...
✓ Manifest and dependencies valid

Validating stack code against templates...
  Validated: 3 stack(s)
  Valid: 3/3
✓ Code validation passed

Creating orchestration plan...
Layer 1: network
Layer 2: security
Layer 3: database-rds

[Preview mode - no changes will be made]
```

#### Step 6: Deploy

```bash
$ cloud deploy D1TEST1 -e dev

Deploying D1TEST1 to dev

Validating deployment...
✓ All validations passed

Creating orchestration plan...

Proceed with deployment? [y/N]: y

Deploying network...
  Creating VPC (vpcCidr=10.1.0.0/16)...
  Creating 2 availability zones...
  Creating subnets...
  Skipping NAT Gateway (disabled for dev)
  ✓ network deployed (45s)
  Outputs:
    vpcId: vpc-0abc123
    vpcArn: arn:aws:ec2:us-east-1:123456789012:vpc/vpc-0abc123
    publicSubnetIds: [subnet-1a, subnet-2a]
    privateSubnetIds: [subnet-1b, subnet-2b]

Deploying security...
  Using vpcId=vpc-0abc123
  Creating security groups...
  ✓ security deployed (12s)
  Outputs:
    dbSecurityGroupId: sg-0def456

Deploying database-rds...
  Using vpcId=vpc-0abc123
  Using securityGroupId=sg-0def456
  Using subnetIds=[subnet-1b, subnet-2b]
  Creating DB subnet group...
  Creating DB instance (class=db.t3.micro, storage=20GB)...
  ✓ database-rds deployed (180s)
  Outputs:
    dbEndpoint: myapp.xyz123.us-east-1.rds.amazonaws.com
    dbArn: arn:aws:rds:us-east-1:123456789012:db:myapp
    dbPort: 5432

✓ Deployment completed successfully
  Total time: 4m 17s
  Stacks deployed: 3
  Errors: 0
```

### Example 2: Validation Error Handling

**Scenario:** Developer adds new parameter without updating template

**Stack Code (Modified):**
```typescript
// Developer adds new feature
const newFeatureEnabled = config.getBoolean("newFeatureEnabled", false);

// But forgets to update template...
```

**Validation:**
```bash
$ cloud validate-stack mystack

Validating mystack against template...

============================================================
✗ Stack 'mystack' validation failed

Errors (1):
  ✗ Input 'newFeatureEnabled' is used in code but not declared in template [input:newFeatureEnabled]

Tip: Re-register the stack to update the template:
  cloud register-stack mystack -d "My Stack"
============================================================
```

**Fix:**
```bash
# Re-register to update template
$ cloud register-stack mystack -d "My Stack"

Extracting parameters from mystack...
  Found 5 input(s) and 3 output(s)  # ← Now includes newFeatureEnabled
✓ Stack 'mystack' registered successfully

# Validate again
$ cloud validate-stack mystack
✓ Stack 'mystack' is valid
```

**Prevent in Deployment:**
```bash
$ cloud deploy D1TEST1 -e dev

Validating deployment...
✓ Manifest and dependencies valid

Validating stack code against templates...
  Validated: 5 stack(s)
  Valid: 4/5
  ✗ Errors: 1

✗ Code validation failed:

  Stack: mystack
    ✗ Input 'newFeatureEnabled' is used in code but not declared in template

Tip: Run 'cloud validate-stack mystack' for detailed validation

Deployment blocked due to validation errors.
```

---

## Command Reference

### Complete CLI Commands

#### Stack Management

**register-stack** - Register a new stack
```bash
cloud register-stack <stack-name> [OPTIONS]

Options:
  --description, -d TEXT          Stack description [required]
  --dependencies TEXT             Comma-separated dependencies
  --priority, -p INTEGER          Stack priority (default: 100)
  --auto-extract                  Auto-extract parameters (default: true)
  --no-auto-extract               Disable auto-extraction
  --validate                      Validate code after registration
  --strict                        Enable strict validation
  --defaults-file TEXT            YAML file with additional config

Examples:
  cloud register-stack network -d "Core networking"
  cloud register-stack security -d "Security" --validate
  cloud register-stack db -d "Database" --dependencies "network,security"
```

**validate-stack** - Validate stack code against template
```bash
cloud validate-stack <stack-name> [OPTIONS]

Options:
  --strict                     Enable strict validation
  --check-files                Check required files (default: true)
  --no-check-files             Skip file checking

Examples:
  cloud validate-stack network
  cloud validate-stack security --strict
```

**list-stacks** - List registered stacks
```bash
cloud list-stacks

Shows all registered stacks with descriptions, dependencies, and priorities.
```

**update-stack** - Update stack registration
```bash
cloud update-stack <stack-name> [OPTIONS]

Options:
  --description, -d TEXT       New description
  --dependencies TEXT          New dependencies
  --priority, -p INTEGER       New priority

Example:
  cloud update-stack network --priority 50
```

**unregister-stack** - Remove stack registration
```bash
cloud unregister-stack <stack-name> [--force]

Example:
  cloud unregister-stack old-stack --force
```

#### Deployment Management

**init** - Initialize new deployment
```bash
cloud init [OPTIONS]

Options:
  --template TEXT              Template name (default: default)
  --deployment-id TEXT         Deployment ID (auto-generated if not provided)
  --org TEXT                   Organization name [required]
  --project TEXT               Project name [required]

Example:
  cloud init --template default --deployment-id D1TEST1 \
             --org CompanyA --project ecommerce
```

**deploy** - Deploy stacks (Enhanced)
```bash
cloud deploy <deployment-id> [OPTIONS]

Options:
  --environment, -e TEXT          Environment (default: dev)
  --validate-code                 Validate stack code (default: true)
  --no-validate-code              Skip code validation
  --strict                        Enable strict validation
  --parallel, -p INTEGER          Max parallel deployments (default: 3)
  --preview                       Preview only, no changes

Examples:
  cloud deploy D1TEST1 -e dev
  cloud deploy D1TEST1 -e dev --preview
  cloud deploy D1PROD1 -e prod --strict
  cloud deploy D1TEST1 -e dev --no-validate-code  # Not recommended
```

**destroy** - Destroy deployment
```bash
cloud destroy <deployment-id> -e <environment>

Example:
  cloud destroy D1TEST1 -e dev
```

---

## Implementation Details

### Module Structure

```
cloud/tools/
├── cli/src/cloud_cli/
│   ├── commands/
│   │   ├── stack_cmd.py          (Enhanced: 290 lines)
│   │   └── deploy_cmd.py         (Enhanced: 187 lines)
│   │
│   └── parser/                   ◀── NEW (657 lines total)
│       ├── __init__.py
│       ├── typescript_parser.py  (382 lines)
│       └── parameter_extractor.py (275 lines)
│
└── core/cloud_core/
    ├── templates/
    │   ├── template_manager.py    (308 lines)
    │   └── stack_template_manager.py  ◀── NEW (298 lines)
    │
    └── validation/
        ├── manifest_validator.py  (218 lines)
        └── stack_code_validator.py    ◀── NEW (376 lines)
```

### Key Classes

**TypeScriptParser:**
```python
class TypeScriptParser:
    """Parse TypeScript stack code to extract parameters"""

    def parse_source(self, source_code: str) -> ParseResult:
        """Extract inputs and outputs from TypeScript code"""
        # Returns: ParseResult(inputs, outputs, errors, warnings)
```

**ParameterExtractor:**
```python
class ParameterExtractor:
    """High-level API for parameter extraction"""

    def extract_from_stack(self, stack_dir: Path) -> Dict:
        """Extract parameters from stack directory"""
        # Returns: {success, parameters, warnings}
```

**StackCodeValidator:**
```python
class StackCodeValidator:
    """Validate stack code against template"""

    def validate(
        self,
        stack_dir: Path,
        template_data: Dict,
        strict: bool = False
    ) -> ValidationResult:
        """Validate code matches template"""
        # Returns: ValidationResult(valid, errors, warnings)
```

**StackTemplateManager:**
```python
class StackTemplateManager:
    """Manage stack templates with enhanced format"""

    def save_template(self, stack_name: str, data: Dict) -> Path:
        """Save stack template with validation"""

    def load_template(self, stack_name: str) -> Dict:
        """Load and validate stack template"""
```

### Test Coverage

**Overall:** 87% coverage with 422 passing tests

**By Module:**
- `stack_template_manager.py`: 94%
- `typescript_parser.py`: ~91%
- `parameter_extractor.py`: ~88%
- `deployment_manager.py`: 87%
- `orchestrator.py`: 86%

**Test Files:**
- 127 new tests for v3 features
- 295 existing tests (all passing)
- Total: 422 tests

---

## Best Practices

### 1. Always Use Auto-Extraction

✅ **DO:**
```bash
cloud register-stack mystack -d "Description"
# Let the system extract parameters automatically
```

❌ **DON'T:**
```bash
cloud register-stack mystack -d "Description" --no-auto-extract
# Manual templates are error-prone and get out of sync
```

### 2. Validate Before Deploying

✅ **DO:**
```bash
# Validate individual stack
cloud validate-stack mystack

# Deploy with validation (default)
cloud deploy D1TEST1 -e dev
```

❌ **DON'T:**
```bash
# Skip validation
cloud deploy D1TEST1 -e dev --no-validate-code
# You'll catch errors at deployment time instead of early
```

### 3. Use Strict Mode for Production

✅ **DO:**
```bash
cloud register-stack prod-stack -d "Production" --validate --strict
cloud deploy D1PROD1 -e prod --strict
```

❌ **DON'T:**
```bash
cloud deploy D1PROD1 -e prod
# Normal mode may miss issues
```

### 4. Document Your Parameters

✅ **DO:**
```typescript
// VPC CIDR block (e.g., 10.0.0.0/16)
const vpcCidr = config.require("vpcCidr");

// Number of availability zones (2 or 3)
const azCount = config.requireNumber("availabilityZones");
```

❌ **DON'T:**
```typescript
const vpcCidr = config.require("vpcCidr");  // No description
```

### 5. Keep Templates in Sync

✅ **DO:**
```bash
# After changing stack code
cloud register-stack mystack -d "Description"
cloud validate-stack mystack
```

❌ **DON'T:**
```bash
# Change code but forget to re-register
# Template gets out of sync with code
```

### 6. Use Descriptive Stack Names

✅ **DO:**
```
network
security-groups
database-rds
compute-ecs
monitoring-cloudwatch
```

❌ **DON'T:**
```
stack1
stack2
db
comp
```

### 7. Organize Dependencies Clearly

✅ **DO:**
```yaml
stacks:
  network:
    dependencies: []

  security:
    dependencies:
      - network

  database:
    dependencies:
      - network
      - security
```

❌ **DON'T:**
```yaml
stacks:
  database:
    dependencies:
      - security  # Missing transitive dependency on network
```

---

## Troubleshooting

### Common Issues and Solutions

#### Issue: "Failed to extract parameters from code"

**Cause:** TypeScript file not found or has syntax errors

**Solution:**
1. Ensure `index.ts` or `<stack-name>.ts` exists in stack directory
2. Check for TypeScript syntax errors
3. Verify file permissions
4. Use `--no-auto-extract` and create template manually if needed

#### Issue: "Input X is used in code but not declared in template"

**Cause:** Code uses a parameter not in the template

**Solution:**
```bash
# Option 1: Re-register to update template
cloud register-stack mystack -d "Description"

# Option 2: Manually add to template
# Edit tools/templates/config/mystack.yaml
parameters:
  inputs:
    X:
      type: string
      required: true
```

#### Issue: "Output Y is declared in template but not exported in code"

**Cause:** Template declares an output that code doesn't export

**Solution:**
```typescript
// Add export to code
export const Y = value;

// Or remove from template
# Edit tools/templates/config/mystack.yaml
# Remove Y from parameters.outputs
```

#### Issue: Deploy fails validation

**Cause:** One or more stacks have validation errors

**Solution:**
```bash
# 1. Identify failing stacks
cloud deploy D1TEST1 -e dev  # Shows which stacks failed

# 2. Validate each failing stack
cloud validate-stack network
cloud validate-stack security

# 3. Fix issues
# Either update code or re-register

# 4. Re-validate
cloud validate-stack network

# 5. Retry deployment
cloud deploy D1TEST1 -e dev
```

#### Issue: Cross-stack reference not resolving

**Cause:** Referenced stack hasn't been deployed yet or output doesn't exist

**Solution:**
1. Check deployment order (dependencies)
2. Verify output exists in referenced stack template
3. Ensure referenced stack deployed successfully
4. Check output name spelling

#### Issue: "Template not found" error

**Cause:** Stack hasn't been registered

**Solution:**
```bash
# Register the stack first
cloud register-stack mystack -d "Description"

# Then try operation again
```

#### Issue: Type mismatch warnings

**Cause:** Code uses different type than template declares

**Solution:**
```typescript
// Align code with template

// Template says: type: number
// Code should use:
const port = config.requireNumber("port");

// NOT:
const port = config.require("port");  // This is string
```

---

## File Structure Reference

### Complete Directory Layout

```
cloud/
├── tools/
│   ├── templates/
│   │   ├── config/                    ← Stack Templates (per-stack defaults)
│   │   │   ├── network.yaml
│   │   │   ├── security.yaml
│   │   │   └── database-rds.yaml
│   │   │
│   │   └── default/                   ← Deployment Templates (orchestration)
│   │       ├── default.yaml
│   │       ├── minimal.yaml
│   │       └── full-stack.yaml
│   │
│   └── cli/... and core/...           ← Implementation code
│
├── stacks/                            ← Stack Implementations (TypeScript + Pulumi)
│   ├── network/
│   │   ├── index.ts                   ← Stack code (what auto-extraction parses)
│   │   ├── Pulumi.yaml
│   │   └── package.json
│   │
│   ├── security/
│   │   └── ...
│   │
│   └── database-rds/
│       └── ...
│
└── deploy/                            ← Deployment Instances
    ├── D1TEST1-MyOrg-MyApp/
    │   ├── deployment-manifest.yaml   ⭐ User edits this (orchestration)
    │   │
    │   ├── config/                    ⭐ ConfigGenerator creates these (runtime)
    │   │   ├── network.dev.yaml       ← What Pulumi reads for dev
    │   │   ├── network.prod.yaml      ← What Pulumi reads for prod
    │   │   ├── security.dev.yaml
    │   │   ├── security.prod.yaml
    │   │   └── database-rds.dev.yaml
    │   │
    │   └── .state/
    │       └── state.yaml             ← Platform deployment state
    │
    └── D1PROD1-MyOrg-MyApp/
        └── ... (same structure)
```

### File Type Summary

| File | Location | Purpose | Created By | Editable | Pulumi Reads |
|------|----------|---------|------------|----------|--------------|
| Stack Template | `tools/templates/config/*.yaml` | Per-stack defaults | `register-stack` | Yes | No |
| Deployment Template | `tools/templates/default/*.yaml` | Orchestration | Manual | Yes | No |
| Deployment Manifest | `deploy/<id>/deployment-manifest.yaml` | User overrides | `cloud init` | ✅ YES | No |
| Deployment Configs | `deploy/<id>/config/*.yaml` | Runtime config | ConfigGenerator | ❌ NO | ✅ YES |
| Stack Code | `stacks/<stack>/index.ts` | Infrastructure code | Developers | Yes | No (compiled) |
| Platform State | `deploy/<id>/.state/state.yaml` | Deployment tracking | Orchestrator | No | No |

### The Flow

```
1. Developer writes stack code:
   stacks/network/index.ts

2. Register stack (auto-extracts parameters):
   cloud register-stack network -d "..."
   → Creates: tools/templates/config/network.yaml

3. Initialize deployment (creates manifest from template):
   cloud init --template default --deployment-id D1TEST1 ...
   → Creates: deploy/D1TEST1/deployment-manifest.yaml

4. User customizes manifest (optional):
   Edit: deploy/D1TEST1/deployment-manifest.yaml

5. Deploy (generates runtime configs):
   cloud deploy D1TEST1 -e dev
   → ConfigGenerator creates: deploy/D1TEST1/config/network.dev.yaml
   → Pulumi reads: deploy/D1TEST1/config/network.dev.yaml
   → Executes: cd stacks/network && pulumi up --config-file ../../deploy/...
```

---

## Summary

### Key Takeaways

1. **Two Types of Templates:**
   - Stack Templates: Per-stack config with inputs/outputs
   - Deployment Templates: Orchestration of multiple stacks

2. **Deployment Manifest vs Deployment Configs:**
   - Manifest: User-editable orchestration file (deployment-manifest.yaml)
   - Configs: Auto-generated runtime files that Pulumi reads (config/*.yaml)
   - Flow: Templates → Manifest → ConfigGenerator → Configs → Pulumi

3. **Enhanced Registration:**
   - Auto-extracts parameters from TypeScript code
   - Generates templates automatically
   - Includes both inputs AND outputs

4. **Template-First Validation:**
   - Enforces code-template consistency
   - Catches issues before deployment
   - Supports normal and strict modes

5. **3-Tier Configuration:**
   - Template defaults → Manifest overrides → Environment overrides
   - Clear precedence rules
   - Flexible per-environment customization
   - Results in deployment config files for Pulumi

6. **Cross-Stack References:**
   - Outputs flow between stacks
   - Resolved via DependencyResolver
   - Referenced using `${stack.output}` syntax

### Quick Command Reference

```bash
# Registration
cloud register-stack <name> -d "..." [--validate] [--strict]

# Validation
cloud validate-stack <name> [--strict]

# Initialization
cloud init --template <template> --deployment-id <id> --org <org> --project <project>

# Deployment
cloud deploy <id> -e <env> [--validate-code] [--strict]

# List stacks
cloud list-stacks
```

### File Locations

```
tools/templates/config/<stack>.yaml     - Stack templates
tools/templates/default/<name>.yaml     - Deployment templates
stacks/<stack>/index.ts                 - Stack code
deploy/<id>/deployment-manifest.yaml    - Deployment manifest
```

---

## End of Complete Stack Management Guide v4.5

**Version:** 4.5 (Unified)
**Status:** Fully Implemented
**Coverage:** 87%
**Tests:** 422 passing
**Features:** Auto-extraction, Output support, Validation, Complete workflows

This guide supersedes:
- Stack_Parameters_and_Registration_Guide_v2.md
- Complete_Guide_Templates_Stacks_Config_and_Registration_v2.md

For additional resources:
- Usage Guide: `Enhanced_Stack_Registration_Usage_Guide.md`
- Implementation Summary: `Implementation_Complete_Summary.md`
- Quick Guide: `Stack_Registration_Quick_Guide.md`
