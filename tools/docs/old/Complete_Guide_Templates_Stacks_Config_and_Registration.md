# Complete Guide: Templates, Stacks, Configuration, and Registration

**Platform:** cloud-0.7
**Architecture:** 3.1
**Date:** 2025-10-28
**Purpose:** Comprehensive unified guide covering all aspects of templates, stacks, configuration flow, and registration

---

## Table of Contents

1. [Overview and Key Concepts](#overview-and-key-concepts)
2. [Critical Distinction: Stack Templates vs Deployment Templates](#critical-distinction-stack-templates-vs-deployment-templates)
3. [The Four Layers of the Architecture](#the-four-layers-of-the-architecture)
4. [Stack Implementations (Layer 2)](#stack-implementations-layer-2)
5. [Complete Configuration Flow (6 Steps)](#complete-configuration-flow-6-steps)
6. [3-Tier Parameter Resolution](#3-tier-parameter-resolution)
7. [Stack Registration Process](#stack-registration-process)
8. [Input Parameters: Declaration and Usage](#input-parameters-declaration-and-usage)
9. [Output Parameters: Declaration and Usage](#output-parameters-declaration-and-usage)
10. [DependencyResolver: Cross-Stack References](#dependencyresolver-cross-stack-references)
11. [Directory Structure Complete Map](#directory-structure-complete-map)
12. [Example: Full Lifecycle Walkthrough](#example-full-lifecycle-walkthrough)
13. [Advanced Topics](#advanced-topics)
14. [Why This Architecture?](#why-this-architecture)
15. [Summary and Quick Reference](#summary-and-quick-reference)

---

## Overview and Key Concepts

### The Complete Picture

The Cloud Infrastructure Orchestration Platform uses a sophisticated multi-layer architecture that separates concerns and enables flexible, repeatable infrastructure deployments.

```
┌─────────────────────────────────────────────────────────────────┐
│                    COMPLETE ARCHITECTURE                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Stack Templates          → Per-stack config defaults           │
│    (tools/templates/config/<stack>.yaml)                        │
│                                                                  │
│  Deployment Templates     → Orchestration recipes               │
│    (tools/templates/default/default.yaml)                       │
│                                                                  │
│  Stack Code               → Infrastructure as Code              │
│    (stacks/*/index.ts)                                          │
│                                                                  │
│  Deployment Manifests     → Deployment-specific config          │
│    (deploy/.../Deployment_Manifest.yaml)                        │
│                                                                  │
│  Per-Stack Config Files   → Runtime configuration               │
│    (deploy/.../config/*.yaml)                                   │
│                                                                  │
│  DependencyResolver       → Cross-stack references              │
│    (Utility for reading stack outputs)                          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Critical Distinction: Stack Templates vs Deployment Templates

**This is the most important concept to understand!**

### Stack Template Files (Per-Stack Config Defaults)

**Purpose:** Define default input parameters for a **single stack**

**Location:** `./cloud/tools/templates/config/<stack-name>.yaml`

**Created by:** `cloud register-stack` command (one-time per stack)

**Example: network.yaml**
```yaml
# ./cloud/tools/templates/config/network.yaml
name: network
description: Core networking infrastructure
dependencies: []
priority: 100

# Default input parameters for THIS STACK ONLY
config:
  vpcCidr: "10.0.0.0/16"
  availabilityZones: 3
  enableNatGateway: true
  natGatewayType: "single"
```

**Key Points:**
- ✅ One file per stack
- ✅ Contains only input parameter defaults
- ✅ Created during stack registration
- ✅ Used as base defaults for all deployments
- ❌ Does NOT define orchestration
- ❌ Does NOT contain outputs

---

### Deployment Templates (Orchestration Recipes)

**Purpose:** Define **which stacks** to deploy together and their relationships

**Location:** `./cloud/tools/templates/default/default.yaml`

**Created by:** Platform developers (multiple pre-built templates)

**Example: default.yaml**
```yaml
# ./cloud/tools/templates/default/default.yaml
version: "3.1"
template_name: "default"
description: "Full platform deployment with all stacks"

stacks:
  network:
    enabled: true
    layer: 1
    dependencies: []
    config:
      vpc_cidr: "10.0.0.0/16"  # Can override stack template defaults

  security:
    enabled: true
    layer: 2
    dependencies:
      - network  # Defines orchestration dependency
    config:
      create_default_sg: true

  database-rds:
    enabled: false
    layer: 4
    dependencies:
      - network
      - security
```

**Key Points:**
- ✅ References multiple stacks
- ✅ Defines dependencies and layers
- ✅ Enables/disables stacks
- ✅ Can override stack template defaults
- ✅ Multiple templates (default, minimal, microservices, etc.)
- ❌ NOT per-stack
- ❌ NOT created during registration

---

### Side-by-Side Comparison

```
┌──────────────────────────────────────────────────────────────────┐
│         STACK TEMPLATE vs DEPLOYMENT TEMPLATE                     │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  STACK TEMPLATE              │  DEPLOYMENT TEMPLATE               │
│  (network.yaml)              │  (default.yaml)                    │
│                              │                                    │
│  • Per-stack config          │  • Multi-stack orchestration      │
│  • Input defaults only       │  • Stack selection + dependencies │
│  • One file per stack        │  • One file per pattern           │
│  • Created by register-stack │  • Created by platform devs       │
│  • Location:                 │  • Location:                      │
│    templates/config/         │    templates/default/             │
│                              │                                    │
│  Example:                    │  Example:                         │
│  name: network               │  stacks:                          │
│  config:                     │    network:                       │
│    vpcCidr: "10.0.0.0/16"   │      enabled: true                │
│                              │      dependencies: []             │
│                              │    security:                      │
│                              │      enabled: true                │
│                              │      dependencies: [network]      │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

---

## The Four Layers of the Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    ARCHITECTURAL LAYERS                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Layer 1: TEMPLATES (Configuration Defaults)                    │
│  ├─ Stack Templates: Per-stack defaults                         │
│  │  └─ tools/templates/config/network.yaml                      │
│  └─ Deployment Templates: Orchestration patterns                │
│     └─ tools/templates/default/default.yaml                     │
│                                                                  │
│  Layer 2: STACK IMPLEMENTATIONS (Infrastructure as Code)        │
│  ├─ Location: cloud/stacks/*/index.ts                          │
│  ├─ Purpose: ACTUAL Pulumi code that creates resources         │
│  ├─ Reads: Input parameters via pulumi.Config()                │
│  └─ Exports: Output values via export const                    │
│                                                                  │
│  Layer 3: DEPLOYMENT CONFIGS (Runtime Configuration)            │
│  ├─ Manifest: deploy/.../Deployment_Manifest.yaml              │
│  │  └─ Template + user overrides + environments                │
│  ├─ Per-Stack Configs: deploy/.../config/*.yaml                │
│  │  └─ Generated by ConfigGenerator from manifest              │
│  └─ Authoritative: YES - what Pulumi actually reads            │
│                                                                  │
│  Layer 4: EXECUTION & STATE (Deployment Tracking)               │
│  ├─ DependencyResolver: Cross-stack references                 │
│  ├─ State: deploy/.../.state/state.yaml                        │
│  └─ Pulumi State: .pulumi/stacks/*.json                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Stack Implementations (Layer 2)

### Purpose and Structure

Stack implementations are the **authoritative infrastructure-as-code**. They are written in TypeScript using Pulumi SDK.

### Directory Structure

```
cloud/stacks/
├── network/
│   ├── index.ts          ← Main Pulumi program
│   ├── Pulumi.yaml       ← Stack metadata
│   ├── package.json      ← Node dependencies
│   └── src/              ← Supporting modules
│       ├── vpc.ts
│       ├── subnets.ts
│       └── nat.ts
│
├── security/
│   ├── index.ts
│   ├── Pulumi.yaml
│   └── src/
│       ├── security-groups.ts
│       └── iam-roles.ts
│
└── ... (16 total stacks)
```

### Anatomy of a Stack

**Pulumi.yaml (Stack Metadata)**
```yaml
# cloud/stacks/network/Pulumi.yaml
name: network
runtime: nodejs
description: Network infrastructure with VPC, subnets, NAT gateways
main: index.ts
```

**index.ts (Main Implementation)**
```typescript
// cloud/stacks/network/index.ts
import * as pulumi from "@pulumi/pulumi";
import * as aws from "@pulumi/aws";

// ═══════════════════════════════════════════════════════════
// STEP 1: READ INPUT PARAMETERS
// ═══════════════════════════════════════════════════════════
const config = new pulumi.Config("network");

// Required parameters (will error if not provided)
const vpcCidr = config.require("vpcCidr");
const deploymentId = config.require("deploymentId");

// Typed required parameters
const availabilityZones = config.requireNumber("availabilityZones");

// Optional parameters with defaults
const enableNatGateway = config.getBoolean("enableNatGateway") ?? false;
const natGatewayType = config.get("natGatewayType") ?? "single";

// ═══════════════════════════════════════════════════════════
// STEP 2: CREATE AWS RESOURCES
// ═══════════════════════════════════════════════════════════
const vpc = new aws.ec2.Vpc("main", {
    cidrBlock: vpcCidr,
    enableDnsHostnames: true,
    enableDnsSupport: true,
    tags: {
        Name: `${deploymentId}-vpc`,
        ManagedBy: "Pulumi"
    }
});

// Create subnets, NAT gateways, etc.
// ... resource creation code ...

// ═══════════════════════════════════════════════════════════
// STEP 3: EXPORT OUTPUT PARAMETERS
// ═══════════════════════════════════════════════════════════
export const vpcId = vpc.id;
export const vpcCidr = vpc.cidrBlock;
export const publicSubnetIds = pulumi.output(
    subnets.publicSubnets.map(s => s.id)
);
export const privateSubnetIds = pulumi.output(
    subnets.privateSubnets.map(s => s.id)
);
```

### Key Points

- ✅ **Authoritative source** - This is the real IaC
- ✅ Written in **TypeScript** using Pulumi SDK
- ✅ Reads input via **pulumi.Config()**
- ✅ Exports outputs via **export const**
- ✅ Can be used **standalone** with `pulumi up`

---

## Complete Configuration Flow (6 Steps)

This is the complete journey from template defaults to deployed infrastructure.

```
┌─────────────────────────────────────────────────────────────────┐
│         COMPLETE 6-STEP CONFIGURATION FLOW                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  STEP 1: STACK TEMPLATE DEFAULTS                                │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ tools/templates/config/network.yaml                    │    │
│  │ (Base defaults for network stack)                      │    │
│  │                                                         │    │
│  │ config:                                                 │    │
│  │   vpcCidr: "10.0.0.0/16"      ← Stack template default │    │
│  │   availabilityZones: 3                                  │    │
│  └────────────────────────────────────────────────────────┘    │
│                           ↓                                      │
│  STEP 2: DEPLOYMENT TEMPLATE (Orchestration Pattern)            │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ tools/templates/default/default.yaml                   │    │
│  │ (Orchestration recipe)                                  │    │
│  │                                                         │    │
│  │ stacks:                                                 │    │
│  │   network:                                              │    │
│  │     enabled: true                                       │    │
│  │     dependencies: []                                    │    │
│  │     config:                                             │    │
│  │       vpc_cidr: "10.0.0.0/16"  ← Can override          │    │
│  └────────────────────────────────────────────────────────┘    │
│                           ↓                                      │
│  STEP 3: USER OVERRIDES (Optional)                              │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ CLI Command:                                            │    │
│  │ cloud init D1PROD1 --vpc-cidr "10.50.0.0/16"          │    │
│  │                                                         │    │
│  │ User override: vpcCidr → "10.50.0.0/16"               │    │
│  └────────────────────────────────────────────────────────┘    │
│                           ↓                                      │
│  STEP 4: MANIFEST GENERATION                                    │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ deploy/D1PROD1-MyOrg-myapp/                           │    │
│  │        Deployment_Manifest.yaml                         │    │
│  │                                                         │    │
│  │ ManifestGenerator combines:                             │    │
│  │   1. Stack template defaults                            │    │
│  │   2. Deployment template                                │    │
│  │   3. User overrides                                     │    │
│  │   4. Environment configuration                          │    │
│  │                                                         │    │
│  │ Result:                                                 │    │
│  │ deployment_id: "D1PROD1"                               │    │
│  │ environments:                                           │    │
│  │   dev:                                                  │    │
│  │     region: "us-east-1"                                │    │
│  │     account_id: "123456789012"                         │    │
│  │ stacks:                                                 │    │
│  │   network:                                              │    │
│  │     config:                                             │    │
│  │       vpc_cidr: "10.50.0.0/16"  ← Final value          │    │
│  └────────────────────────────────────────────────────────┘    │
│                           ↓                                      │
│  STEP 5: ⭐ CONFIG FILE GENERATION ⭐                           │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ ConfigGenerator creates per-stack, per-env configs     │    │
│  │                                                         │    │
│  │ deploy/D1PROD1-MyOrg-myapp/config/                    │    │
│  │   ├── network.dev.yaml                                 │    │
│  │   ├── network.prod.yaml                                │    │
│  │   ├── security.dev.yaml                                │    │
│  │   └── security.prod.yaml                               │    │
│  │                                                         │    │
│  │ network.dev.yaml contents:                              │    │
│  │   network:vpcCidr: "10.50.0.0/16"                     │    │
│  │   network:availabilityZones: "3"                      │    │
│  │   network:region: "us-east-1"                         │    │
│  │   network:deploymentId: "D1PROD1"                     │    │
│  │   network:environment: "dev"                           │    │
│  │                                                         │    │
│  │ ⭐ THESE FILES ARE WHAT PULUMI READS ⭐                │    │
│  └────────────────────────────────────────────────────────┘    │
│                           ↓                                      │
│  STEP 6: RUNTIME RESOLUTION & PULUMI EXECUTION                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ PlaceholderResolver resolves dynamic values:            │    │
│  │   {{RUNTIME:network:vpcId}} → "vpc-0a1b2c3d"          │    │
│  │                                                         │    │
│  │ Then execute:                                           │    │
│  │   cd stacks/network/                                   │    │
│  │   pulumi up --config-file ../../deploy/.../          │    │
│  │               config/network.dev.yaml                   │    │
│  │                                                         │    │
│  │ Stack code reads:                                       │    │
│  │   const config = new pulumi.Config("network");        │    │
│  │   const vpcCidr = config.require("vpcCidr");          │    │
│  │   // vpcCidr = "10.50.0.0/16"                         │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3-Tier Parameter Resolution

Parameters are resolved in a 3-tier hierarchy with later tiers overriding earlier ones:

```
┌─────────────────────────────────────────────────────────────────┐
│              3-TIER PARAMETER RESOLUTION                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  TIER 1: STACK TEMPLATE DEFAULTS (Lowest Priority)              │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ tools/templates/config/network.yaml                    │    │
│  │                                                         │    │
│  │ config:                                                 │    │
│  │   vpcCidr: "10.0.0.0/16"           ← Base default      │    │
│  │   availabilityZones: 3                                  │    │
│  │   enableNatGateway: true                                │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  TIER 2: DEPLOYMENT MANIFEST OVERRIDES (Medium Priority)        │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ deploy/D1PROD1-.../Deployment_Manifest.yaml           │    │
│  │                                                         │    │
│  │ stacks:                                                 │    │
│  │   network:                                              │    │
│  │     config:                                             │    │
│  │       vpcCidr: "10.50.0.0/16"      ← Override          │    │
│  │       availabilityZones: 3          ← Keep default     │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  TIER 3: ENVIRONMENT-SPECIFIC OVERRIDES (Highest Priority)      │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ deploy/D1PROD1-.../Deployment_Manifest.yaml           │    │
│  │                                                         │    │
│  │ stacks:                                                 │    │
│  │   network:                                              │    │
│  │     environments:                                       │    │
│  │       dev:                                              │    │
│  │         config:                                         │    │
│  │           availabilityZones: 2     ← Env override      │    │
│  │           enableNatGateway: false  ← Env override      │    │
│  │       prod:                                             │    │
│  │         config:                                         │    │
│  │           availabilityZones: 3     ← Env override      │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  FINAL RESOLVED VALUES (for dev environment):                   │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ vpcCidr: "10.50.0.0/16"           (from Tier 2)        │    │
│  │ availabilityZones: 2               (from Tier 3)        │    │
│  │ enableNatGateway: false            (from Tier 3)        │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Resolution Rules

1. **Tier 1** values are used if not overridden
2. **Tier 2** overrides Tier 1
3. **Tier 3** overrides both Tier 1 and Tier 2
4. Missing values in higher tiers fall through to lower tiers

---

## Stack Registration Process

### Overview

Before a stack can be used in deployments, it must be **registered**. Registration creates the stack template file with default parameters.

### When to Register

- ✅ After creating new stack code
- ✅ When adding a new infrastructure component
- ✅ One-time per stack (unless updating)

### Registration Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│           STACK REGISTRATION PROCESS                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Developer Action:                                               │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ cloud register-stack my-new-stack \                    │    │
│  │   --description "My custom stack" \                    │    │
│  │   --dependencies network,security \                    │    │
│  │   --defaults-file ./defaults.yaml                      │    │
│  └────────────────────────────────────────────────────────┘    │
│                           ↓                                      │
│  STEP 1: Validate Stack Exists                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ • Check stacks/my-new-stack/ exists                    │    │
│  │ • Check Pulumi.yaml exists                             │    │
│  │ • Check index.ts exists                                │    │
│  │ • Validate structure                                   │    │
│  └────────────────────────────────────────────────────────┘    │
│                           ↓                                      │
│  STEP 2: Extract Stack Metadata                                 │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ • Parse Pulumi.yaml                                    │    │
│  │ • Extract: name, runtime, description                  │    │
│  │ • Validate metadata completeness                       │    │
│  └────────────────────────────────────────────────────────┘    │
│                           ↓                                      │
│  STEP 3: Collect Configuration Parameters                       │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ Option A: From --defaults-file                         │    │
│  │   • Parse YAML file                                    │    │
│  │   • Extract config keys and values                     │    │
│  │                                                         │    │
│  │ Option B: Interactive prompts                          │    │
│  │   • Prompt for parameter name                          │    │
│  │   • Prompt for type                                    │    │
│  │   • Prompt for default value                           │    │
│  │   • Repeat until done                                  │    │
│  │                                                         │    │
│  │ Option C: AST parsing (future)                         │    │
│  │   • Parse index.ts                                     │    │
│  │   • Find config.require() calls                        │    │
│  │   • Infer parameters automatically                     │    │
│  └────────────────────────────────────────────────────────┘    │
│                           ↓                                      │
│  STEP 4: Generate Stack Template File                           │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ Create: tools/templates/config/my-new-stack.yaml       │    │
│  │                                                         │    │
│  │ Contents:                                               │    │
│  │   name: my-new-stack                                   │    │
│  │   description: "My custom stack"                       │    │
│  │   dependencies: [network, security]                    │    │
│  │   config:                                               │    │
│  │     param1: "default-value"                            │    │
│  │     param2: 100                                         │    │
│  └────────────────────────────────────────────────────────┘    │
│                           ↓                                      │
│  STEP 5: Register in Stack Registry                             │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ • Add entry to tools/templates/registry.json           │    │
│  │ • Make stack discoverable                              │    │
│  │ • Make available for deployment templates              │    │
│  └────────────────────────────────────────────────────────┘    │
│                           ↓                                      │
│  SUCCESS!                                                        │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ ✓ Stack registered successfully                        │    │
│  │ ✓ Template: tools/templates/config/my-new-stack.yaml  │    │
│  │ ✓ Stack now available for use in deployments          │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Command Examples

```bash
# Basic registration with defaults file
cloud register-stack my-stack \
  --description "My custom infrastructure" \
  --dependencies network,security \
  --defaults-file ./my-stack-defaults.yaml

# Interactive registration (prompts for parameters)
cloud register-stack my-stack \
  --description "My custom infrastructure" \
  --interactive

# Registration with validation (recommended)
cloud register-stack my-stack \
  --defaults-file ./defaults.yaml \
  --validate

# Update existing registration
cloud update-stack my-stack \
  --add-parameter "newParam:string:default-value"
```

### Defaults File Format

**Simple format:**
```yaml
# my-stack-defaults.yaml
instanceType: "t3.micro"
minSize: 2
maxSize: 10
enableMonitoring: true
```

**Enhanced format with metadata:**
```yaml
# my-stack-defaults-enhanced.yaml
parameters:
  - name: instanceType
    type: string
    default: "t3.micro"
    description: "EC2 instance type"

  - name: minSize
    type: number
    default: 2
    description: "Minimum instance count"

  - name: enableMonitoring
    type: boolean
    default: true
    description: "Enable CloudWatch monitoring"
```

---

## Input Parameters: Declaration and Usage

### Three Locations Where Inputs Are Defined

```
┌─────────────────────────────────────────────────────────────────┐
│              INPUT PARAMETER LOCATIONS                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. DECLARATION (Stack Template)                                │
│     tools/templates/config/network.yaml                         │
│     ├─ Defines: parameter names and defaults                    │
│     └─ Created: During stack registration                       │
│                                                                  │
│  2. OVERRIDE (Deployment Manifest)                              │
│     deploy/.../Deployment_Manifest.yaml                         │
│     ├─ Defines: deployment-specific overrides                   │
│     └─ Created: During cloud init                               │
│                                                                  │
│  3. USAGE (Stack Code)                                          │
│     stacks/network/index.ts                                     │
│     ├─ Reads: via pulumi.Config()                              │
│     └─ Created: By developers writing stack                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Example: Complete Input Parameter Flow

**1. Stack Template (Declaration)**
```yaml
# tools/templates/config/network.yaml
name: network
config:
  vpcCidr: "10.0.0.0/16"          # Default value
  availabilityZones: 3
  enableNatGateway: true
```

**2. Deployment Manifest (Override)**
```yaml
# deploy/D1PROD1-.../Deployment_Manifest.yaml
stacks:
  network:
    config:
      vpcCidr: "10.50.0.0/16"     # Override template default
      availabilityZones: 3         # Keep default
```

**3. Generated Config File**
```yaml
# deploy/D1PROD1-.../config/network.dev.yaml
network:vpcCidr: "10.50.0.0/16"
network:availabilityZones: "3"
network:enableNatGateway: "true"
network:deploymentId: "D1PROD1"
network:environment: "dev"
```

**4. Stack Code (Usage)**
```typescript
// stacks/network/index.ts
import * as pulumi from "@pulumi/pulumi";

const config = new pulumi.Config("network");

// Read parameters
const vpcCidr = config.require("vpcCidr");  // Gets "10.50.0.0/16"
const azCount = config.requireNumber("availabilityZones");  // Gets 3
const enableNat = config.getBoolean("enableNatGateway");    // Gets true

// Use in resource creation
const vpc = new aws.ec2.Vpc("main", {
    cidrBlock: vpcCidr,  // Uses "10.50.0.0/16"
    // ...
});
```

### Parameter Types and Methods

```typescript
// Required string parameter
const vpcCidr = config.require("vpcCidr");

// Required number parameter
const azCount = config.requireNumber("availabilityZones");

// Optional boolean with default
const enableNat = config.getBoolean("enableNatGateway") ?? false;

// Optional string with default
const natType = config.get("natGatewayType") ?? "single";

// Object parameter
const tags = config.getObject<Record<string, string>>("tags") ?? {};

// Secret parameter
const apiKey = config.requireSecret("apiKey");
```

---

## Output Parameters: Declaration and Usage

### Two Locations Where Outputs Are Defined

```
┌─────────────────────────────────────────────────────────────────┐
│              OUTPUT PARAMETER LOCATIONS                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. DECLARATION & EXPORT (Stack Code)                           │
│     stacks/network/index.ts                                     │
│     ├─ Declares: via export const                              │
│     ├─ Stored: in Pulumi state after deployment                │
│     └─ Authoritative: YES                                       │
│                                                                  │
│  2. CONSUMPTION (Dependent Stack Code)                          │
│     stacks/security/index.ts                                    │
│     ├─ Reads: via DependencyResolver.get()                     │
│     ├─ Or: via pulumi.StackReference                           │
│     └─ Or: via {{RUNTIME:...}} placeholders                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Method 1: Export in Stack Code

```typescript
// stacks/network/index.ts
import * as pulumi from "@pulumi/pulumi";
import * as aws from "@pulumi/aws";

// Create resources
const vpc = new aws.ec2.Vpc("main", { ... });
const subnets = createSubnets(vpc);
const natGateways = createNatGateways(subnets);

// ═══════════════════════════════════════════════════════════
// EXPORT OUTPUTS (declare what this stack provides)
// ═══════════════════════════════════════════════════════════

// Simple value export
export const vpcId = vpc.id;
export const vpcCidr = vpc.cidrBlock;

// Array of values
export const publicSubnetIds = pulumi.output(
    subnets.publicSubnets.map(s => s.id)
);

export const privateSubnetIds = pulumi.output(
    subnets.privateSubnets.map(s => s.id)
);

// Conditional export
export const natGatewayIds = natGateways
    ? pulumi.output(natGateways.map(ng => ng.id))
    : undefined;
```

### Method 2: Using Helper Function

```typescript
// stacks/network/src/outputs.ts
import * as pulumi from "@pulumi/pulumi";

export function exportOutputs(outputs: Record<string, any>) {
    for (const [key, value] of Object.entries(outputs)) {
        pulumi.export(key, value);
    }
}

// stacks/network/index.ts
import { exportOutputs } from "./src/outputs";

exportOutputs({
    vpcId: vpc.id,
    vpcCidr: vpc.cidrBlock,
    publicSubnetIds: subnets.publicSubnets.map(s => s.id),
    privateSubnetIds: subnets.privateSubnets.map(s => s.id),
});
```

### Where Outputs Are Stored

After deployment, outputs are stored in Pulumi state:

```
deploy/D1PROD1-.../
└── .pulumi/
    └── stacks/
        └── D1PROD1-network-dev.json    ← Pulumi state file
```

Access via CLI:
```bash
pulumi stack output vpcId --stack D1PROD1-network-dev
# Output: vpc-0a1b2c3d4e5f
```

---

## DependencyResolver: Cross-Stack References

### Purpose

**DependencyResolver** is a utility that allows stacks to read outputs from other stacks they depend on.

### Why Use It?

Instead of manually constructing StackReference names, DependencyResolver:
- ✅ Automatically formats stack names
- ✅ Caches outputs for performance
- ✅ Provides consistent error handling
- ✅ Simplifies code

### Location

```
cloud/tools/utils/dependency-resolver.ts
```

### Usage in Dependent Stacks

```typescript
// stacks/security/index.ts
import * as pulumi from "@pulumi/pulumi";
import * as aws from "@pulumi/aws";
import { DependencyResolver } from "../../../tools/utils/dependency-resolver";

// ═══════════════════════════════════════════════════════════
// INITIALIZE RESOLVER
// ═══════════════════════════════════════════════════════════
const config = new pulumi.Config("security");
const deploymentId = config.require("deploymentId");
const environment = config.require("environment");

const resolver = new DependencyResolver(deploymentId, environment);

// ═══════════════════════════════════════════════════════════
// GET OUTPUTS FROM NETWORK STACK
// ═══════════════════════════════════════════════════════════
const vpcId = resolver.get("network", "vpcId");
// Returns: pulumi.Output<string>

const privateSubnetIds = resolver.get("network", "privateSubnetIds");
// Returns: pulumi.Output<string[]>

// ═══════════════════════════════════════════════════════════
// USE IN RESOURCE CREATION
// ═══════════════════════════════════════════════════════════
const securityGroup = new aws.ec2.SecurityGroup("web-sg", {
    vpcId: vpcId,  // Pulumi handles Output<T> automatically
    description: "Security group for web servers",
    ingress: [
        {
            protocol: "tcp",
            fromPort: 80,
            toPort: 80,
            cidrBlocks: ["0.0.0.0/0"]
        }
    ]
});

// Use subnet IDs for resources
const dbInstance = new aws.rds.Instance("db", {
    subnetIds: privateSubnetIds,  // Output<string[]> works directly
    // ...
});
```

### Alternative: Direct StackReference

```typescript
// Without DependencyResolver (manual approach)
import * as pulumi from "@pulumi/pulumi";

// Manually construct full stack name
// Format: orgName/projectName/deploymentId-stackName-environment
const stackName = `MyOrg/my-project/D1PROD1-network-dev`;
const networkStack = new pulumi.StackReference(stackName);

const vpcId = networkStack.getOutput("vpcId");
const privateSubnetIds = networkStack.getOutput("privateSubnetIds");

// Use as normal
```

### Alternative: Runtime Placeholders

```yaml
# In manifest - resolved by CLI before deployment
stacks:
  security:
    config:
      vpcId: "{{RUNTIME:network:vpcId}}"
      subnetIds: "{{RUNTIME:network:privateSubnetIds}}"
```

Then in stack code:
```typescript
const config = new pulumi.Config("security");
const vpcId = config.require("vpcId");  // Already resolved to actual value
```

### Comparison of Methods

| Method | When to Use | Pros | Cons |
|--------|-------------|------|------|
| **DependencyResolver** | Most stack-to-stack references | Simple, consistent, cached | Requires utility import |
| **StackReference** | Direct Pulumi approach | No utility needed, standard Pulumi | Manual name construction |
| **Runtime Placeholders** | Simple value passing | Resolved before deployment | Less flexible, string only |

---

## Directory Structure Complete Map

```
./cloud/
├── stacks/                                   # ⭐ STACK IMPLEMENTATIONS
│   ├── network/
│   │   ├── index.ts                         # ACTUAL Pulumi code
│   │   ├── Pulumi.yaml                      # Stack metadata
│   │   ├── package.json
│   │   └── src/
│   │       ├── vpc.ts
│   │       ├── subnets.ts
│   │       └── outputs.ts
│   │
│   ├── security/
│   │   ├── index.ts
│   │   ├── Pulumi.yaml
│   │   └── src/
│   │
│   └── ... (16 stacks total)
│
├── tools/
│   ├── templates/
│   │   ├── config/                          # ⭐ STACK TEMPLATES (per-stack defaults)
│   │   │   ├── network.yaml                 # Created by: cloud register-stack
│   │   │   ├── security.yaml
│   │   │   ├── database-rds.yaml
│   │   │   └── ... (one per stack)
│   │   │
│   │   ├── default/                         # ⭐ DEPLOYMENT TEMPLATES (orchestration)
│   │   │   └── default.yaml                 # Full platform pattern
│   │   │
│   │   ├── minimal/
│   │   │   └── minimal.yaml                 # Minimal deployment pattern
│   │   │
│   │   ├── custom/
│   │   │   └── my-org/
│   │   │       └── custom-template.yaml
│   │   │
│   │   ├── stack/
│   │   │   └── stack-config-template.yaml   # Template for new registrations
│   │   │
│   │   └── registry.json                    # Stack registry (all registered stacks)
│   │
│   ├── utils/
│   │   ├── dependency-resolver.ts           # ⭐ CROSS-STACK REFERENCE UTILITY
│   │   ├── parameter-extractor.ts           # AST parsing for auto-registration
│   │   └── export-extractor.ts              # Extract exports from code
│   │
│   └── core/                                # CLI implementation
│       ├── cloud_core/
│       │   ├── deployment/
│       │   │   ├── deployment_manager.py
│       │   │   ├── state_manager.py
│       │   │   └── config_generator.py      # ⭐ Generates Step 5 config files
│       │   │
│       │   ├── templates/
│       │   │   ├── template_manager.py
│       │   │   └── manifest_generator.py    # ⭐ Generates Step 4 manifest
│       │   │
│       │   ├── orchestrator/
│       │   │   ├── orchestrator.py
│       │   │   ├── execution_engine.py
│       │   │   └── dependency_resolver.py
│       │   │
│       │   └── runtime/
│       │       ├── placeholder_resolver.py
│       │       └── aws_query_resolver.py
│       │
│       └── tests/
│           └── fixtures/
│               └── templates/
│                   └── default/
│                       └── standard-template.yaml  # TEST ONLY!
│
└── deploy/                                  # ⭐ DEPLOYMENT INSTANCES
    └── D1PROD1-MyOrg-myapp/                # One deployment
        ├── Deployment_Manifest.yaml         # ⭐ Step 4: Generated manifest
        │                                    #    (template + overrides + envs)
        │
        ├── config/                          # ⭐ Step 5: PER-STACK CONFIG FILES
        │   ├── network.dev.yaml             #    (What Pulumi actually reads!)
        │   ├── network.prod.yaml
        │   ├── security.dev.yaml
        │   ├── security.prod.yaml
        │   └── ... (all stacks × all envs)
        │
        ├── .state/                          # Deployment state tracking
        │   ├── state.yaml
        │   └── operations.jsonl
        │
        ├── .pulumi/                         # Pulumi state
        │   └── stacks/
        │       ├── D1PROD1-network-dev.json # ⭐ Outputs stored here!
        │       └── D1PROD1-security-dev.json
        │
        └── logs/
            ├── init.log
            └── deploy-dev-20251028.log
```

### Purpose Summary Table

| Location | Type | Purpose | Authoritative? | Created When |
|----------|------|---------|----------------|--------------|
| `stacks/*/index.ts` | Implementation | **Actual IaC code** | ✅ YES | Development |
| `tools/templates/config/*.yaml` | Stack Template | **Per-stack defaults** | ❌ NO | `register-stack` |
| `tools/templates/default/*.yaml` | Deployment Template | **Orchestration pattern** | ❌ NO | Development |
| `tools/utils/dependency-resolver.ts` | Utility | **Cross-stack refs** | N/A | Development |
| `deploy/.../Deployment_Manifest.yaml` | Manifest | **Deployment config** | ✅ YES | `cloud init` |
| `deploy/.../config/*.yaml` | Config Files | **Runtime config** | ✅ YES | `cloud init` |
| `.pulumi/stacks/*.json` | State | **Outputs storage** | ✅ YES | After deploy |

---

## Example: Full Lifecycle Walkthrough

Let's walk through a complete example from stack creation to deployment.

### Scenario

Create and deploy a new "cache" stack that depends on network and security stacks.

### Phase 1: Create Stack Code

```bash
# Create stack directory
mkdir -p cloud/stacks/cache
cd cloud/stacks/cache
```

**Create Pulumi.yaml:**
```yaml
# cloud/stacks/cache/Pulumi.yaml
name: cache
runtime: nodejs
description: Redis/ElastiCache cluster
main: index.ts
```

**Create package.json:**
```json
{
  "name": "cache",
  "dependencies": {
    "@pulumi/pulumi": "^3.0.0",
    "@pulumi/aws": "^6.0.0"
  }
}
```

**Create index.ts:**
```typescript
// cloud/stacks/cache/index.ts
import * as pulumi from "@pulumi/pulumi";
import * as aws from "@pulumi/aws";
import { DependencyResolver } from "../../../tools/utils/dependency-resolver";

// ═══════════════════════════════════════════════════════════
// READ CONFIGURATION
// ═══════════════════════════════════════════════════════════
const config = new pulumi.Config("cache");

// Input parameters
const nodeType = config.require("nodeType");
const numNodes = config.requireNumber("numNodes");
const engineVersion = config.get("engineVersion") ?? "7.0";
const deploymentId = config.require("deploymentId");
const environment = config.require("environment");

// ═══════════════════════════════════════════════════════════
// GET DEPENDENCIES
// ═══════════════════════════════════════════════════════════
const resolver = new DependencyResolver(deploymentId, environment);

const vpcId = resolver.get("network", "vpcId");
const privateSubnetIds = resolver.get("network", "privateSubnetIds");
const securityGroupId = resolver.get("security", "cacheSecurityGroupId");

// ═══════════════════════════════════════════════════════════
// CREATE RESOURCES
// ═══════════════════════════════════════════════════════════

// Subnet group
const subnetGroup = new aws.elasticache.SubnetGroup("cache-subnets", {
    subnetIds: privateSubnetIds,
    description: "Subnet group for ElastiCache cluster",
});

// Redis cluster
const cluster = new aws.elasticache.Cluster("redis", {
    engine: "redis",
    engineVersion: engineVersion,
    nodeType: nodeType,
    numCacheNodes: numNodes,
    subnetGroupName: subnetGroup.name,
    securityGroupIds: [securityGroupId],
    tags: {
        Name: `${deploymentId}-redis`,
        Environment: environment,
    },
});

// ═══════════════════════════════════════════════════════════
// EXPORT OUTPUTS
// ═══════════════════════════════════════════════════════════
export const clusterId = cluster.id;
export const clusterAddress = cluster.cacheNodes[0].address;
export const clusterPort = cluster.port;
export const clusterEndpoint = pulumi.interpolate`${cluster.cacheNodes[0].address}:${cluster.port}`;
```

### Phase 2: Register Stack

```bash
# Create defaults file
cat > cache-defaults.yaml <<EOF
nodeType: "cache.t3.micro"
numNodes: 1
engineVersion: "7.0"
EOF

# Register the stack
cloud register-stack cache \
  --description "Redis/ElastiCache cluster" \
  --dependencies network,security \
  --defaults-file ./cache-defaults.yaml \
  --validate
```

**Output:**
```
Registering stack: cache
Validating stack directory... ✓
Extracting metadata from Pulumi.yaml... ✓
Loading defaults from cache-defaults.yaml... ✓
Generating stack template...
Creating: tools/templates/config/cache.yaml ✓
Registering in stack registry... ✓

✓ Stack 'cache' registered successfully
```

**Generated file: tools/templates/config/cache.yaml**
```yaml
name: cache
description: Redis/ElastiCache cluster
dependencies:
  - network
  - security
priority: 200

config:
  nodeType: "cache.t3.micro"
  numNodes: 1
  engineVersion: "7.0"
```

### Phase 3: Add to Deployment Template

```bash
# Edit deployment template to include cache stack
vim tools/templates/default/default.yaml
```

**Add to default.yaml:**
```yaml
stacks:
  # ... existing stacks ...

  cache:
    enabled: false  # Disabled by default, enable per deployment
    layer: 4
    dependencies:
      - network
      - security
    config:
      nodeType: "cache.t3.micro"
      numNodes: 1
      engineVersion: "7.0"
```

### Phase 4: Initialize Deployment

```bash
# Create new deployment with cache enabled
cloud init D1PROD1 \
  --template default \
  --org MyCompany \
  --project ecommerce \
  --domain mystore.com \
  --enable-stack cache \
  --override cache.nodeType=cache.t3.small \
  --override cache.numNodes=2
```

**What happens:**
1. Loads deployment template (`default.yaml`)
2. Loads stack templates (including `cache.yaml`)
3. Enables cache stack (disabled by default)
4. Applies overrides (larger node type, 2 nodes)
5. Generates manifest: `deploy/D1PROD1-MyCompany-ecommerce/Deployment_Manifest.yaml`
6. Generates config files:
   - `config/cache.dev.yaml`
   - `config/cache.prod.yaml`

**Generated config/cache.dev.yaml:**
```yaml
cache:nodeType: "cache.t3.small"       # Override applied
cache:numNodes: "2"                    # Override applied
cache:engineVersion: "7.0"             # From template
cache:deploymentId: "D1PROD1"
cache:environment: "dev"
cache:region: "us-east-1"
```

### Phase 5: Deploy

```bash
# Deploy to dev environment
cloud deploy D1PROD1 --environment dev
```

**Orchestrator execution:**
```
Planning deployment for D1PROD1 (dev)...

Dependency analysis:
  Layer 1: [network]
  Layer 2: [security]
  Layer 3: []
  Layer 4: [cache]

Executing layer 1...
  Deploying network... ✓ (45s)

Executing layer 2...
  Deploying security... ✓ (30s)

Executing layer 4...
  Deploying cache...
    cd stacks/cache/
    pulumi up --stack dev --config-file ../../deploy/D1PROD1-.../config/cache.dev.yaml

    Resources:
      + aws:elasticache:SubnetGroup cache-subnets created
      + aws:elasticache:Cluster redis created

    Outputs:
      clusterId: "redis-abc123"
      clusterAddress: "redis-abc123.cache.amazonaws.com"
      clusterPort: 6379
      clusterEndpoint: "redis-abc123.cache.amazonaws.com:6379"

  ✓ (120s)

Deployment completed successfully!
  Total time: 3m 15s
  Stacks deployed: 3
```

### Phase 6: Use Outputs in Another Stack

Now the cache outputs are available for other stacks:

```typescript
// stacks/api/index.ts
import { DependencyResolver } from "../../../tools/utils/dependency-resolver";

const resolver = new DependencyResolver(deploymentId, environment);

// Get cache endpoint
const cacheEndpoint = resolver.get("cache", "clusterEndpoint");

// Use in application config
const appConfig = new aws.ssm.Parameter("app-config", {
    name: "/app/cache-endpoint",
    type: "String",
    value: cacheEndpoint,
});
```

---

## Advanced Topics

### Automated Parameter Extraction

Instead of manually creating defaults files, parameters can be extracted automatically from stack code using AST parsing.

**Example utility:**
```typescript
// tools/utils/parameter-extractor.ts
import * as ts from "typescript";
import * as fs from "fs";

interface Parameter {
    name: string;
    type: 'string' | 'number' | 'boolean' | 'object';
    required: boolean;
    defaultValue?: any;
}

export function extractParametersFromStack(stackPath: string): Parameter[] {
    const indexPath = `${stackPath}/index.ts`;
    const sourceCode = fs.readFileSync(indexPath, 'utf-8');

    const sourceFile = ts.createSourceFile(
        indexPath,
        sourceCode,
        ts.ScriptTarget.Latest,
        true
    );

    const parameters: Parameter[] = [];

    function visit(node: ts.Node) {
        // Look for config.require('paramName')
        if (ts.isCallExpression(node)) {
            const expression = node.expression;

            if (ts.isPropertyAccessExpression(expression) &&
                expression.expression.getText() === 'config') {

                const methodName = expression.name.getText();
                const paramName = node.arguments[0]?.getText().replace(/['"]/g, '');

                if (methodName === 'require') {
                    parameters.push({
                        name: paramName,
                        type: 'string',
                        required: true,
                    });
                } else if (methodName === 'requireNumber') {
                    parameters.push({
                        name: paramName,
                        type: 'number',
                        required: true,
                    });
                } else if (methodName === 'getBoolean') {
                    // Check for default value
                    let defaultValue = undefined;
                    if (node.parent && ts.isBinaryExpression(node.parent)) {
                        defaultValue = node.parent.right.getText() === 'true';
                    }

                    parameters.push({
                        name: paramName,
                        type: 'boolean',
                        required: false,
                        defaultValue,
                    });
                }
            }
        }

        ts.forEachChild(node, visit);
    }

    visit(sourceFile);
    return parameters;
}
```

**Usage:**
```bash
# Register with auto-extraction
cloud register-stack cache \
  --auto-extract-params \
  --validate
```

### Template-First Approach

Make templates the authoritative source of truth by declaring outputs and validating code matches.

**Enhanced template format:**
```yaml
# tools/templates/config/network.yaml
name: network
description: Core networking infrastructure
dependencies: []

parameters:
  inputs:
    - name: vpcCidr
      type: string
      required: true
      default: "10.0.0.0/16"
      description: "CIDR block for VPC"
      validation:
        pattern: "^\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}/\\d{1,2}$"

    - name: availabilityZones
      type: number
      required: true
      default: 3
      validation:
        min: 1
        max: 6

  outputs:
    - name: vpcId
      type: string
      description: "VPC ID"
      required: true
      usedBy: [security, database-rds, cache]

    - name: privateSubnetIds
      type: array
      items: string
      description: "Private subnet IDs"
      required: true
      usedBy: [database-rds, cache]
```

**Validation command:**
```bash
# Validate stack code matches template
cloud validate-stack network

# Output:
# Validating network stack...
# ✓ All required inputs used in code
# ✓ All required outputs exported
# ✓ All parameter types match
```

### Output Extraction and Validation

```typescript
// tools/utils/export-extractor.ts
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
                exports.push({
                    name: declaration.name.text,
                    type: inferType(declaration),
                });
            }
        }

        ts.forEachChild(node, visit);
    }

    visit(sourceFile);
    return exports;
}
```

---

## Why This Architecture?

### Design Rationale

#### 1. Separation of Concerns

```
┌─────────────────────────────────────────────────────────┐
│             SEPARATION OF CONCERNS                       │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  WHAT to deploy?    → Deployment templates              │
│  HOW to deploy?     → Stack implementations             │
│  WHERE to deploy?   → Deployment manifests              │
│  WITH WHAT values?  → Stack templates + config files    │
│  HOW to reference?  → DependencyResolver                │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

#### 2. Reusability

**One Stack Template → All Deployments**
```
Stack Template: cache.yaml
    ↓
    Used by:
    ├─ Deployment 1: D1DEV1-TeamA
    ├─ Deployment 2: D1PROD1-TeamA
    ├─ Deployment 3: D1DEV1-TeamB
    └─ Deployment 4: D1PROD1-TeamB
```

**One Deployment Template → Multiple Deployments**
```
Deployment Template: default.yaml
    ↓
    ├─ D1PROD1-CompanyA-app1 (prod, us-west-2)
    ├─ D1DEV1-CompanyA-app1 (dev, us-east-1)
    └─ D1PROD2-CompanyB-app2 (prod, eu-west-1)
```

#### 3. Flexibility

**Per-Deployment Customization:**
- Dev: Small instances, fewer AZs
- Prod: Large instances, multi-AZ
- Custom: Organization-specific settings

**Per-Environment Overrides:**
```yaml
stacks:
  cache:
    config:
      nodeType: "cache.t3.small"  # Base
    environments:
      dev:
        config:
          nodeType: "cache.t3.micro"  # Dev override
      prod:
        config:
          nodeType: "cache.r6g.large"  # Prod override
```

#### 4. Maintainability

- ✅ Stack template = Single source for defaults
- ✅ Registration process = Structured onboarding
- ✅ DependencyResolver = Consistent cross-stack refs
- ✅ Validation = Catch errors early

#### 5. Documentation

Templates serve as:
- 📖 API documentation (inputs/outputs)
- 📖 Dependency documentation
- 📖 Default value documentation
- 📖 Usage examples

---

## Summary and Quick Reference

### The Complete Picture

```
┌─────────────────────────────────────────────────────────────┐
│                  THE COMPLETE PICTURE                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Stack Templates:          Per-stack config defaults        │
│    Location:               tools/templates/config/          │
│    Created by:             cloud register-stack             │
│    Purpose:                Default input parameters         │
│    Authoritative:          NO (defaults only)               │
│                                                              │
│  Deployment Templates:     Orchestration recipes            │
│    Location:               tools/templates/default/         │
│    Created by:             Platform developers              │
│    Purpose:                Which stacks + dependencies      │
│    Authoritative:          NO (patterns only)               │
│                                                              │
│  Stack Code:               Infrastructure as Code           │
│    Location:               stacks/*/index.ts                │
│    Created by:             Developers                       │
│    Purpose:                Create AWS resources             │
│    Authoritative:          YES (actual IaC)                 │
│                                                              │
│  DependencyResolver:       Cross-stack references           │
│    Location:               tools/utils/                     │
│    Purpose:                Read other stacks' outputs       │
│    Usage:                  resolver.get("stack", "output")  │
│                                                              │
│  Deployment Manifest:      Deployment configuration         │
│    Location:               deploy/.../Deployment_Manifest   │
│    Created by:             cloud init (ManifestGenerator)   │
│    Purpose:                Template + overrides + envs      │
│    Authoritative:          YES (per deployment)             │
│                                                              │
│  Per-Stack Config Files:   Runtime configuration            │
│    Location:               deploy/.../config/*.yaml         │
│    Created by:             cloud init (ConfigGenerator)     │
│    Purpose:                What Pulumi actually reads       │
│    Authoritative:          YES (runtime config)             │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Quick Command Reference

```bash
# Create and register new stack
cloud register-stack <stack-name> \
  --description "Description" \
  --dependencies stack1,stack2 \
  --defaults-file ./defaults.yaml

# Initialize deployment
cloud init <deployment-id> \
  --template default \
  --org MyOrg \
  --project myproject

# Deploy
cloud deploy <deployment-id> --environment dev

# Validate
cloud validate <deployment-id>
cloud validate-stack <stack-name>

# List registered stacks
cloud list-stacks
```

### File Location Quick Reference

| What | Where |
|------|-------|
| Stack code | `stacks/*/index.ts` |
| Stack template | `tools/templates/config/<stack>.yaml` |
| Deployment template | `tools/templates/default/default.yaml` |
| DependencyResolver | `tools/utils/dependency-resolver.ts` |
| Manifest | `deploy/.../Deployment_Manifest.yaml` |
| Config files | `deploy/.../config/*.yaml` |
| Pulumi state | `.pulumi/stacks/*.json` |

### Parameter Resolution Order

1. **Stack template defaults** (lowest priority)
2. **Deployment manifest overrides** (medium priority)
3. **Environment-specific overrides** (highest priority)

### Cross-Stack Reference Methods

1. **DependencyResolver** (recommended)
   ```typescript
   const resolver = new DependencyResolver(deploymentId, environment);
   const vpcId = resolver.get("network", "vpcId");
   ```

2. **StackReference** (direct Pulumi)
   ```typescript
   const stack = new pulumi.StackReference("org/project/stack-env");
   const vpcId = stack.getOutput("vpcId");
   ```

3. **Runtime placeholders** (CLI-resolved)
   ```yaml
   config:
     vpcId: "{{RUNTIME:network:vpcId}}"
   ```

---

## Appendix: Common Questions

### Q: What's the difference between stack template and deployment template?

**A:**
- **Stack template**: Per-stack config defaults (one file per stack)
- **Deployment template**: Multi-stack orchestration pattern (multiple stacks)

### Q: When do I use DependencyResolver vs StackReference?

**A:** Use **DependencyResolver** for consistency and convenience. Use **StackReference** if you need direct Pulumi control or are working outside the CLI.

### Q: Can I skip registration and just write stack code?

**A:** Yes, stacks work standalone with Pulumi. But registration enables CLI orchestration, default management, and template-based deployments.

### Q: Where are outputs actually stored?

**A:** In Pulumi state files: `.pulumi/stacks/<deployment-id>-<stack>-<env>.json`

### Q: How do I add a parameter to an existing stack?

**A:**
1. Add parameter usage in stack code
2. Update stack template: `cloud update-stack <name> --add-parameter "param:type:default"`
3. Or manually edit `tools/templates/config/<stack>.yaml`

### Q: What's the test template for?

**A:** `tests/fixtures/templates/default/standard-template.yaml` is **ONLY** for unit testing the CLI. Never use for real deployments!

### Q: Can I have multiple deployment templates?

**A:** Yes! Create multiple patterns:
- `default.yaml` - Full platform
- `minimal.yaml` - Basic stacks only
- `microservices.yaml` - Service-oriented
- `custom/my-org.yaml` - Organization-specific

### Q: How do I override config for just one environment?

**A:** Use environment-specific overrides in the manifest:
```yaml
stacks:
  cache:
    config:
      nodeType: "cache.t3.small"  # Base
    environments:
      prod:
        config:
          nodeType: "cache.r6g.large"  # Prod override
```

---

**Document Version:** 2.0
**Created:** 2025-10-28
**Platform:** cloud-0.7
**Architecture:** 3.1

**Related Documents:**
- Multi_Stack_Architecture.3.1.md
- Stack_Parameters_and_Registration_Guide.md
- Understanding_Templates_Stacks_and_Config_Flow.md (v1.0 - superseded by this document)

---

*End of Complete Guide*
