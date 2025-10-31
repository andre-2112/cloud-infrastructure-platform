# Understanding Templates, Stacks, and Configuration Flow

## Overview

This document clarifies the architecture of the Cloud Infrastructure Orchestration Platform, specifically how templates, stack implementations, and configuration files work together to enable flexible, repeatable infrastructure deployments.

---

## Table of Contents

1. [Key Architectural Components](#key-architectural-components)
2. [The Two Different Concepts](#the-two-different-concepts)
3. [Complete Configuration Flow](#complete-configuration-flow)
4. [Directory Structure Map](#directory-structure-map)
5. [Example: Full Deployment Flow](#example-full-deployment-flow)
6. [Why This Architecture?](#why-this-architecture)

---

## Key Architectural Components

### Component Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    ARCHITECTURAL LAYERS                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Layer 1: TEMPLATES (Orchestration Recipes)                     │
│  ├─ Production: cloud/tools/templates/default/default.yaml     │
│  ├─ Test: tests/fixtures/templates/default/standard-template.yaml│
│  └─ Purpose: Define WHICH stacks + dependencies + defaults      │
│                                                                  │
│  Layer 2: STACK IMPLEMENTATIONS (Infrastructure as Code)        │
│  ├─ Location: cloud/stacks/*/index.ts                          │
│  ├─ Purpose: ACTUAL Pulumi code that creates resources         │
│  └─ Authoritative: YES - this is the real IaC                  │
│                                                                  │
│  Layer 3: DEPLOYMENT CONFIGS (Runtime Configuration)            │
│  ├─ Generated: cloud/deploy/D1PROD1-.../config/*.yaml         │
│  ├─ Purpose: Per-stack, per-environment config values          │
│  └─ Authoritative: YES - what Pulumi actually reads            │
│                                                                  │
│  Layer 4: DEPLOYMENT STATE (Execution Tracking)                 │
│  ├─ Location: cloud/deploy/D1PROD1-.../.state/                │
│  └─ Purpose: Track deployment status and history               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## The Two Different Concepts

### Understanding the Separation

Many people confuse **templates** with **stack implementations**. They serve completely different purposes:

### 1. Stack Implementations (The Actual Infrastructure Code)

**Location:** `cloud/stacks/*/`

```
cloud/stacks/
├── network/
│   ├── index.ts          ← ACTUAL Pulumi TypeScript code
│   ├── Pulumi.yaml       ← Stack metadata
│   ├── package.json      ← Dependencies
│   └── src/              ← Additional TypeScript modules
│       ├── vpc.ts
│       ├── subnets.ts
│       └── nat.ts
│
├── security/
│   ├── index.ts          ← Security groups, IAM roles
│   └── Pulumi.yaml
│
├── database-rds/
│   ├── index.ts          ← RDS instances, parameter groups
│   └── Pulumi.yaml
│
└── ... (16 total stacks)
```

**Key Points:**
- ✅ **Authoritative source** for infrastructure
- ✅ Contains the **actual Pulumi code** that creates AWS resources
- ✅ Written in TypeScript using Pulumi SDK
- ✅ Reads configuration via `pulumi.Config` API
- ✅ Can be used standalone with `pulumi up`

**Example: network/index.ts**
```typescript
import * as pulumi from "@pulumi/pulumi";
import * as aws from "@pulumi/aws";

const config = new pulumi.Config("network");
const vpcCidr = config.require("vpcCidr");  // Reads from config file
const azCount = config.requireNumber("availabilityZones");

// Create VPC
const vpc = new aws.ec2.Vpc("main", {
    cidrBlock: vpcCidr,
    enableDnsHostnames: true,
    enableDnsSupport: true,
});

// Export VPC ID for other stacks
export const vpcId = vpc.id;
```

### 2. Deployment Templates (Orchestration Recipes)

**Location (Production):** `cloud/tools/templates/default/default.yaml`
**Location (Test):** `cloud/tools/core/tests/fixtures/templates/default/standard-template.yaml`

```yaml
# Deployment Template Example
version: "3.1"
template_name: "default"
description: "Full platform deployment with all stacks"

stacks:
  network:
    enabled: true
    layer: 1                    # Deploy first
    dependencies: []            # No dependencies
    config:
      vpc_cidr: "10.0.0.0/16"  # Default value
      availability_zones: 3

  security:
    enabled: true
    layer: 2                    # Deploy after network
    dependencies:
      - network                 # Depends on network stack
    config:
      create_default_sg: true

  database-rds:
    enabled: false              # Optional stack (disabled by default)
    layer: 4
    dependencies:
      - network
      - security
    config:
      engine: "postgres"
      instance_class: "db.t3.micro"
```

**Key Points:**
- ❌ **NOT infrastructure code** - just orchestration metadata
- ✅ Defines **which stacks** to deploy together
- ✅ Defines **dependencies** between stacks
- ✅ Provides **default configuration values**
- ✅ Enables **stack selection** (enable/disable stacks)
- ✅ Supports **multiple deployment patterns** (dev, prod, minimal, etc.)

### Side-by-Side Comparison

```
┌────────────────────────────────────────────────────────────────────┐
│                 STACK IMPLEMENTATION vs TEMPLATE                    │
├────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  STACK IMPLEMENTATION           │  TEMPLATE                         │
│  (cloud/stacks/network/)        │  (tools/templates/default/)      │
│                                 │                                   │
│  • WHAT: Pulumi TypeScript      │  • WHAT: YAML orchestration      │
│  • PURPOSE: Create resources    │  • PURPOSE: Define which stacks  │
│  • LANGUAGE: TypeScript         │  • LANGUAGE: YAML                │
│  • RUNS: pulumi up              │  • RUNS: Never (just metadata)   │
│  • AUTHORITATIVE: YES           │  • AUTHORITATIVE: NO             │
│  • REUSABLE: Via imports        │  • REUSABLE: Multiple deploys    │
│  • EXAMPLE:                     │  • EXAMPLE:                      │
│    const vpc = new aws.Vpc()   │    stacks:                       │
│                                 │      network:                     │
│                                 │        enabled: true              │
│                                 │        dependencies: []           │
│                                                                     │
└────────────────────────────────────────────────────────────────────┘
```

---

## Complete Configuration Flow

### The 6-Step Configuration Resolution Process

```
┌─────────────────────────────────────────────────────────────────────┐
│              COMPLETE CONFIGURATION FLOW (6 STEPS)                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Step 1: TEMPLATE DEFAULTS                                          │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │ cloud/tools/templates/config/network.yaml                  │    │
│  │                                                             │    │
│  │ vpc_cidr: "10.0.0.0/16"           ← Base defaults          │    │
│  │ availability_zones: 3                                       │    │
│  │ enable_nat_gateway: true                                    │    │
│  └────────────────────────────────────────────────────────────┘    │
│                              ↓                                       │
│  Step 2: USER OVERRIDES (Optional)                                  │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │ CLI Command:                                                │    │
│  │ cloud init D1PROD1 --vpc-cidr "10.50.0.0/16"              │    │
│  │                                                             │    │
│  │ Overrides vpc_cidr → "10.50.0.0/16"                       │    │
│  └────────────────────────────────────────────────────────────┘    │
│                              ↓                                       │
│  Step 3: MANIFEST GENERATION                                        │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │ cloud/deploy/D1PROD1-MyOrg-myapp/                         │    │
│  │         Deployment_Manifest.yaml                            │    │
│  │                                                             │    │
│  │ deployment_id: "D1PROD1"                                   │    │
│  │ organization: "MyOrg"                                       │    │
│  │ environments:                                               │    │
│  │   dev:                                                      │    │
│  │     region: "us-east-1"                                    │    │
│  │     account_id: "123456789012"                             │    │
│  │   prod:                                                     │    │
│  │     region: "us-west-2"                                    │    │
│  │     account_id: "987654321098"                             │    │
│  │ stacks:                                                     │    │
│  │   network:                                                  │    │
│  │     enabled: true                                           │    │
│  │     config:                                                 │    │
│  │       vpc_cidr: "10.50.0.0/16"  ← Override applied         │    │
│  │       availability_zones: 3                                 │    │
│  └────────────────────────────────────────────────────────────┘    │
│                              ↓                                       │
│  Step 4: ⭐ CONFIG FILE GENERATION ⭐                               │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │ ConfigGenerator creates per-stack, per-environment configs │    │
│  │                                                             │    │
│  │ cloud/deploy/D1PROD1-MyOrg-myapp/config/                  │    │
│  │   ├── network.dev.yaml      ← For dev environment         │    │
│  │   ├── network.prod.yaml     ← For prod environment        │    │
│  │   ├── security.dev.yaml                                    │    │
│  │   ├── security.prod.yaml                                   │    │
│  │   └── ... (all stacks × all environments)                 │    │
│  │                                                             │    │
│  │ network.dev.yaml contents:                                  │    │
│  │   network:vpcCidr: "10.50.0.0/16"                         │    │
│  │   network:availabilityZones: "3"                          │    │
│  │   network:region: "us-east-1"                             │    │
│  │   network:accountId: "123456789012"                       │    │
│  │   network:environment: "dev"                               │    │
│  │   network:deploymentId: "D1PROD1"                         │    │
│  └────────────────────────────────────────────────────────────┘    │
│                              ↓                                       │
│  Step 5: RUNTIME RESOLUTION                                         │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │ PlaceholderResolver resolves dynamic values:                │    │
│  │                                                             │    │
│  │ {{RUNTIME:network:vpcId}}                                  │    │
│  │   → Query Pulumi state for network stack's vpcId output   │    │
│  │   → "vpc-0a1b2c3d4e5f"                                     │    │
│  │                                                             │    │
│  │ {{RUNTIME:aws:latestAmiId:amazonLinux2}}                   │    │
│  │   → Query AWS for latest AMI ID                            │    │
│  │   → "ami-0c55b159cbfafe1f0"                               │    │
│  └────────────────────────────────────────────────────────────┘    │
│                              ↓                                       │
│  Step 6: PULUMI EXECUTION                                           │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │ cd cloud/stacks/network/                                   │    │
│  │                                                             │    │
│  │ pulumi up \                                                │    │
│  │   --stack dev \                                            │    │
│  │   --config-file ../../deploy/D1PROD1-.../config/         │    │
│  │                 network.dev.yaml                            │    │
│  │                                                             │    │
│  │ Stack code (index.ts) reads config:                        │    │
│  │   const config = new pulumi.Config("network");            │    │
│  │   const vpcCidr = config.require("vpcCidr");              │    │
│  │   // vpcCidr = "10.50.0.0/16"                             │    │
│  │                                                             │    │
│  │ Creates AWS VPC with specified CIDR                        │    │
│  └────────────────────────────────────────────────────────────┘    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Key Insights from the Flow

1. **Step 1-3**: Configuration **aggregation** (gathering values from multiple sources)
2. **Step 4**: Configuration **distribution** (creating per-stack files)
3. **Step 5**: Configuration **resolution** (replacing dynamic placeholders)
4. **Step 6**: Configuration **consumption** (Pulumi reads and uses values)

**The config files in Step 4 ARE the authoritative runtime configuration!**

---

## Directory Structure Map

### Complete Directory Layout with Purpose

```
./cloud/
├── stacks/                                   # ⭐ STACK IMPLEMENTATIONS
│   ├── network/
│   │   ├── index.ts                         # Actual Pulumi IaC code
│   │   ├── Pulumi.yaml                      # Stack metadata
│   │   ├── package.json
│   │   └── src/                             # Supporting modules
│   ├── security/
│   │   ├── index.ts
│   │   └── Pulumi.yaml
│   └── ... (16 stacks total)
│
├── tools/
│   ├── templates/                           # ⭐ TEMPLATES (Orchestration)
│   │   ├── default/
│   │   │   └── default.yaml                 # Full platform template
│   │   ├── minimal/
│   │   │   └── minimal.yaml                 # Minimal deployment
│   │   ├── config/                          # ⭐ TEMPLATE CONFIG DEFAULTS
│   │   │   ├── network.yaml                 # Default network config
│   │   │   ├── security.yaml                # Default security config
│   │   │   └── ... (config per stack)
│   │   ├── custom/
│   │   │   └── my-org/                      # Org-specific templates
│   │   └── stack/
│   │       └── stack-config-template.yaml   # New stack registration
│   │
│   └── core/                                # CLI implementation
│       ├── cloud_core/                      # Python package
│       │   ├── deployment/
│       │   │   ├── deployment_manager.py
│       │   │   ├── state_manager.py
│       │   │   └── config_generator.py      # Generates Step 4 configs
│       │   ├── templates/
│       │   │   ├── template_manager.py
│       │   │   └── manifest_generator.py    # Generates Step 3 manifest
│       │   └── orchestrator/
│       │       └── orchestrator.py          # Manages deployment flow
│       │
│       └── tests/
│           └── fixtures/
│               └── templates/
│                   └── default/
│                       └── standard-template.yaml  # ⭐ TEST TEMPLATE ONLY
│
└── deploy/                                  # ⭐ DEPLOYMENT INSTANCES
    └── D1PROD1-MyOrg-myapp/                # One deployment
        ├── Deployment_Manifest.yaml         # Step 3: Generated manifest
        │
        ├── config/                          # ⭐ Step 4: GENERATED CONFIGS
        │   ├── network.dev.yaml             # Per-stack, per-environment
        │   ├── network.prod.yaml
        │   ├── security.dev.yaml
        │   ├── security.prod.yaml
        │   └── ... (all stacks × all envs)
        │
        ├── .state/                          # Deployment state tracking
        │   ├── state.yaml                   # Current deployment state
        │   └── operations.jsonl             # Operation history
        │
        └── logs/
            ├── init.log
            └── deploy-dev-20251027.log
```

### Purpose Summary Table

| Location | Purpose | Authoritative? | Created When |
|----------|---------|----------------|--------------|
| `stacks/*/index.ts` | **Infrastructure code** (Pulumi TypeScript) | ✅ YES | Development |
| `tools/templates/default/` | **Orchestration recipes** (which stacks + deps) | ❌ NO | Development |
| `tools/templates/config/` | **Default config values** | ❌ NO | Development |
| `deploy/.../Deployment_Manifest.yaml` | **Deployment-specific manifest** | ✅ YES | `cloud init` |
| `deploy/.../config/*.yaml` | **Per-stack runtime configs** | ✅ YES | `cloud init` |
| `tests/fixtures/templates/` | **Test-only templates** | ❌ NO (test only) | Testing |

---

## Example: Full Deployment Flow

### Real-World Scenario

**Goal:** Deploy production infrastructure for an e-commerce application

### Step-by-Step Execution

#### 1. Initialize Deployment

```bash
cloud init D1PROD1 \
  --template default \
  --org MyCompany \
  --project ecommerce \
  --domain mystore.com \
  --vpc-cidr "10.50.0.0/16" \
  --region us-west-2
```

**What Happens:**
1. Loads template: `tools/templates/default/default.yaml`
2. Merges config defaults from `tools/templates/config/*.yaml`
3. Applies user overrides (vpc-cidr, region, etc.)
4. Generates manifest: `deploy/D1PROD1-MyCompany-ecommerce/Deployment_Manifest.yaml`
5. **Generates config files**: `deploy/D1PROD1-.../config/*.yaml` (one per stack per environment)

#### 2. Review Generated Manifest

```bash
cat deploy/D1PROD1-MyCompany-ecommerce/Deployment_Manifest.yaml
```

```yaml
deployment_id: "D1PROD1"
organization: "MyCompany"
project: "ecommerce"
domain: "mystore.com"

environments:
  dev:
    enabled: true
    region: "us-west-2"
    account_id: "123456789012"
  prod:
    enabled: false  # Will enable after testing
    region: "us-west-2"
    account_id: "987654321098"

stacks:
  network:
    enabled: true
    layer: 1
    dependencies: []
    config:
      vpc_cidr: "10.50.0.0/16"  # User override applied
      availability_zones: 3

  security:
    enabled: true
    layer: 2
    dependencies: ["network"]
    config:
      create_default_sg: true

  storage:
    enabled: true
    layer: 3
    dependencies: ["security"]
    config:
      versioning_enabled: true
```

#### 3. Review Generated Config File

```bash
cat deploy/D1PROD1-MyCompany-ecommerce/config/network.dev.yaml
```

```yaml
# Generated by ConfigGenerator from Deployment_Manifest.yaml
network:vpcCidr: "10.50.0.0/16"
network:availabilityZones: "3"
network:region: "us-west-2"
network:accountId: "123456789012"
network:environment: "dev"
network:deploymentId: "D1PROD1"
network:organization: "MyCompany"
network:project: "ecommerce"
network:domain: "mystore.com"
```

**This file is what Pulumi will actually read!**

#### 4. Deploy to Dev Environment

```bash
cloud deploy D1PROD1 --environment dev
```

**What Happens (Orchestrator Logic):**

```
┌──────────────────────────────────────────────────────────┐
│           ORCHESTRATOR EXECUTION SEQUENCE                 │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  1. Load manifest                                         │
│     └─▶ Read deployment configuration                    │
│                                                           │
│  2. Calculate dependency layers                           │
│     └─▶ Layer 1: [network]                              │
│         Layer 2: [security, dns]                         │
│         Layer 3: [storage]                               │
│                                                           │
│  3. For each layer (sequential):                         │
│     For each stack in layer (parallel):                  │
│                                                           │
│       Layer 1: Deploy network                            │
│       ┌─────────────────────────────────────────┐       │
│       │ cd cloud/stacks/network/                │       │
│       │ pulumi up --stack dev \                 │       │
│       │   --config-file ../../deploy/D1PROD1-..│       │
│       │                 /config/network.dev.yaml│       │
│       │                                          │       │
│       │ Stack reads config:                     │       │
│       │   const cfg = new pulumi.Config("network")│    │
│       │   const cidr = cfg.require("vpcCidr")   │       │
│       │   // cidr = "10.50.0.0/16"              │       │
│       │                                          │       │
│       │ Creates: VPC, Subnets, NAT, etc.        │       │
│       │ Exports: vpcId, subnetIds, etc.         │       │
│       └─────────────────────────────────────────┘       │
│                                                           │
│       Layer 2: Deploy security (parallel with dns)       │
│       ┌─────────────────────────────────────────┐       │
│       │ cd cloud/stacks/security/               │       │
│       │ pulumi up --stack dev \                 │       │
│       │   --config-file ../../deploy/D1PROD1-..│       │
│       │                 /config/security.dev.yaml│      │
│       │                                          │       │
│       │ Stack reads config + cross-stack refs:  │       │
│       │   const cfg = new pulumi.Config("security")│   │
│       │   const vpcId = pulumi.StackReference   │       │
│       │     .getOutput("vpcId")                 │       │
│       │   // vpcId from network stack           │       │
│       │                                          │       │
│       │ Creates: Security Groups, IAM roles     │       │
│       └─────────────────────────────────────────┘       │
│                                                           │
│       Layer 3: Deploy storage                            │
│       └─▶ Similar process...                            │
│                                                           │
│  4. Update state                                         │
│     └─▶ Record deployment status in .state/state.yaml  │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

#### 5. Stack Code Reads Config

**Inside `cloud/stacks/network/index.ts`:**

```typescript
import * as pulumi from "@pulumi/pulumi";
import * as aws from "@pulumi/aws";

// Read configuration from network.dev.yaml
const config = new pulumi.Config("network");
const vpcCidr = config.require("vpcCidr");              // "10.50.0.0/16"
const azCount = config.requireNumber("availabilityZones"); // 3
const region = config.require("region");                 // "us-west-2"
const deploymentId = config.require("deploymentId");    // "D1PROD1"

// Create VPC using the configuration
const vpc = new aws.ec2.Vpc("main", {
    cidrBlock: vpcCidr,
    enableDnsHostnames: true,
    enableDnsSupport: true,
    tags: {
        Name: `${deploymentId}-vpc`,
        Environment: config.require("environment"),
        ManagedBy: "Pulumi"
    }
});

// Export outputs for other stacks to use
export const vpcId = vpc.id;
export const vpcCidr = vpc.cidrBlock;
```

#### 6. Promote to Production

```bash
# Enable prod environment
cloud enable-environment D1PROD1 prod

# Deploy to prod
cloud deploy D1PROD1 --environment prod
```

Uses `config/network.prod.yaml` instead of `config/network.dev.yaml`!

---

## Why This Architecture?

### Design Rationale

#### 1. Separation of Concerns

```
┌─────────────────────────────────────────────────────────┐
│             SEPARATION OF CONCERNS                       │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  WHAT to deploy    → Templates (orchestration)          │
│  HOW to deploy     → Stack code (Pulumi TypeScript)     │
│  WHERE to deploy   → Manifests (environments)           │
│  WITH WHAT values  → Config files (per-stack configs)   │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

#### 2. Reusability

**One Template → Many Deployments:**

```
Template: default.yaml
    ↓
    ├─▶ Deployment 1: D1DEV1-TeamA-app1 (dev, us-east-1)
    ├─▶ Deployment 2: D1PROD1-TeamA-app1 (prod, us-west-2)
    ├─▶ Deployment 3: D1DEV2-TeamB-app2 (dev, eu-west-1)
    └─▶ Deployment 4: D1PROD2-TeamB-app2 (prod, eu-west-1)
```

**One Stack Implementation → All Deployments:**

```
Stack: cloud/stacks/network/index.ts
    ↓
    Used by ALL deployments (just with different configs)
```

#### 3. Flexibility

**Stack Selection:**
- Dev: Enable only necessary stacks (network, security)
- Prod: Enable all stacks including databases, monitoring

**Configuration Overrides:**
- Dev: Small instance types, relaxed security
- Prod: Large instance types, strict security

#### 4. Consistency

**Template ensures:**
- Correct dependency order
- Required configuration present
- Valid stack combinations
- Consistent naming conventions

#### 5. Testability

**Test Template** (`tests/fixtures/templates/default/standard-template.yaml`):
- Simplified for unit testing
- Tests CLI logic without deploying real infrastructure
- Fast test execution

**Production Template** (`tools/templates/default/default.yaml`):
- Complete, production-ready configuration
- All 16 stacks defined
- Real-world dependencies

---

## Summary

### The Key Takeaway

```
┌─────────────────────────────────────────────────────────────┐
│                  THE COMPLETE PICTURE                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Templates:           Orchestration recipes (YAML)          │
│    Purpose:           Define WHICH stacks + dependencies    │
│    Location:          tools/templates/default/              │
│    Authoritative:     NO (just metadata)                    │
│                                                              │
│  Stack Code:          Infrastructure as Code (TypeScript)   │
│    Purpose:           Create AWS resources                  │
│    Location:          stacks/*/index.ts                     │
│    Authoritative:     YES (the actual IaC)                  │
│                                                              │
│  Config Files:        Runtime configuration (YAML)          │
│    Purpose:           Values Pulumi reads                   │
│    Location:          deploy/.../config/*.yaml              │
│    Authoritative:     YES (what stacks actually use)        │
│    Generated:         By ConfigGenerator from manifest      │
│                                                              │
│  Manifest:            Deployment specification (YAML)       │
│    Purpose:           Template + overrides + environments   │
│    Location:          deploy/.../Deployment_Manifest.yaml   │
│    Authoritative:     YES (per deployment)                  │
│    Generated:         By ManifestGenerator from template    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Flow in One Sentence

**Templates define WHICH stacks to deploy, Manifests add WHERE to deploy them, ConfigGenerator creates per-stack config files, and Stack code (the authoritative IaC) reads those configs to create actual AWS resources.**

---

## Appendix: Common Questions

### Q: Why not just use Pulumi stacks directly?

**A:** Pulumi manages individual stacks well, but doesn't orchestrate multi-stack dependencies, parallel execution, or provide deployment templates. Our CLI adds this orchestration layer.

### Q: Can I deploy a single stack without the CLI?

**A:** Yes! Each stack in `cloud/stacks/*/` is a valid Pulumi program:

```bash
cd cloud/stacks/network
pulumi up --stack dev
```

But you lose: dependency management, automatic config generation, multi-stack orchestration, and state tracking.

### Q: What's the difference between template and manifest?

**A:**
- **Template**: Reusable recipe (defines stack structure)
- **Manifest**: Deployment-specific instance (template + your values)

Template is the cookie cutter, manifest is the actual cookie!

### Q: Where do I put custom configuration values?

**A:** Three places, in order of precedence:

1. **CLI flags** (highest): `cloud init --vpc-cidr "10.50.0.0/16"`
2. **Manifest edits** (medium): Edit `Deployment_Manifest.yaml` after init
3. **Template defaults** (lowest): Edit `tools/templates/config/*.yaml`

### Q: Can I create my own templates?

**A:** Yes! Two ways:

1. **Custom template**: Create `tools/templates/custom/my-org/my-template.yaml`
2. **Modify existing**: Edit `tools/templates/default/default.yaml`

### Q: What's the test template for?

**A:** `tests/fixtures/templates/default/standard-template.yaml` is ONLY for unit testing the CLI itself. It's a simplified template that allows testing without deploying real infrastructure.

Never use it for actual deployments!

---

*Document created: 2025-10-28*
*Architecture version: 3.1*
*For more details, see: Multi_Stack_Architecture.3.1.md*
