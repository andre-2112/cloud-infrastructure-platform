# Cloud Architecture v3.0 - Stack Cloning Addendum

**Version:** 3.0
**Last Updated:** 2025-10-09
**Status:** Production Ready

---

## Table of Contents

1. [Overview](#overview)
2. [Stack Cloning Concept](#stack-cloning-concept)
3. [Use Cases](#use-cases)
4. [Cloning Architecture](#cloning-architecture)
5. [Cloning Process](#cloning-process)
6. [Configuration Handling](#configuration-handling)
7. [State Management](#state-management)
8. [CLI Commands](#cli-commands)
9. [REST API Endpoints](#rest-api-endpoints)
10. [Implementation Examples](#implementation-examples)

---

## Overview

Stack Cloning is an advanced feature in Cloud Architecture v3.0 that enables rapid duplication of existing stacks with configuration modifications. This capability supports:

- **Environment Promotion**: Clone dev stack to stage/prod
- **Multi-Region Deployment**: Clone stack across AWS regions
- **Testing & Experimentation**: Create sandbox copies
- **Disaster Recovery**: Rapid stack recreation
- **Multi-Tenant Deployments**: Clone stacks for different customers

### Key Benefits

1. **Speed**: Clone existing stack in minutes vs. hours of manual setup
2. **Consistency**: Exact replication of working configurations
3. **Safety**: Preserves original stack, allows rollback
4. **Flexibility**: Modify configuration during cloning
5. **Automation**: Scriptable for CI/CD pipelines

---

## Stack Cloning Concept

### What is Stack Cloning?

Stack Cloning creates a new stack instance based on an existing stack's:
- Configuration values
- Resource definitions
- Dependencies
- State (optionally)

The cloned stack is **independent** - changes to clone don't affect original.

### Cloning vs. Copying

| Cloning | Copying |
|---------|---------|
| Creates new Pulumi stack | Duplicates files only |
| New AWS resources created | No AWS resources created |
| Independent state | No state |
| Can modify configuration | Exact copy |
| Production-ready | Requires setup |

### Cloning Modes

#### 1. Full Clone
Clone everything including resource state and data.

**Use Case**: Disaster recovery, exact replication

**Command:**
```bash
cloud clone-stack D1BRV40 network --source-env dev --target-env stage --mode full
```

#### 2. Configuration Clone
Clone configuration only, recreate resources from scratch.

**Use Case**: Environment promotion, configuration reuse

**Command:**
```bash
cloud clone-stack D1BRV40 network --source-env dev --target-env stage --mode config
```

#### 3. Cross-Region Clone
Clone stack to different AWS region.

**Use Case**: Multi-region deployment, geographic expansion

**Command:**
```bash
cloud clone-stack D1BRV40 network --source-env dev --target-env stage --target-region us-west-2
```

---

## Use Cases

### Use Case 1: Environment Promotion

**Scenario**: Promote working dev configuration to stage

```bash
# Clone network stack from dev to stage
cloud clone-stack D1BRV40 network \
  --source-env dev \
  --target-env stage \
  --mode config

# Result: stage environment gets identical network configuration
```

**Benefits:**
- Ensures stage matches working dev config
- Eliminates manual configuration errors
- Maintains consistency across environments

### Use Case 2: Multi-Region Deployment

**Scenario**: Deploy infrastructure in multiple regions

```bash
# Clone entire deployment to us-west-2
cloud clone-deployment D1BRV40 \
  --source-env prod \
  --target-env prod \
  --target-region us-west-2 \
  --new-id D2WEST2

# Result: Complete infrastructure in new region
```

**Benefits:**
- Rapid geographic expansion
- Consistent multi-region configuration
- Supports disaster recovery

### Use Case 3: Testing & Experimentation

**Scenario**: Test configuration changes safely

```bash
# Clone prod stack to experimental environment
cloud clone-stack D1BRV40 database-rds \
  --source-env prod \
  --target-env dev \
  --suffix "-experimental" \
  --modify "instanceClass=db.t3.micro"

# Result: dev-experimental environment for testing
```

**Benefits:**
- Safe experimentation without affecting production
- Quick setup of test environments
- Easy cleanup after testing

### Use Case 4: Customer Deployments

**Scenario**: Deploy infrastructure for new customer

```bash
# Clone template deployment for new customer
cloud clone-deployment DTEMPLATE \
  --new-id DCUSTOMER1 \
  --modify "org=Customer1" \
  --modify "project=customer1-prod"

# Result: Dedicated deployment for Customer1
```

**Benefits:**
- Rapid customer onboarding
- Consistent architecture across customers
- Isolated resources per customer

---

## Cloning Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────┐
│                  Stack Cloning System                    │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  1. Source Analysis                                      │
│     ├─ Read source stack configuration                  │
│     ├─ Read source stack state                          │
│     ├─ Identify dependencies                            │
│     └─ Extract resource definitions                     │
│                                                          │
│  2. Configuration Transformation                         │
│     ├─ Apply target environment config                  │
│     ├─ Modify specified parameters                      │
│     ├─ Update dependencies                              │
│     └─ Resolve placeholders                             │
│                                                          │
│  3. Target Creation                                      │
│     ├─ Create new Pulumi stack                          │
│     ├─ Apply transformed configuration                  │
│     ├─ Deploy resources (or import state)               │
│     └─ Capture outputs                                  │
│                                                          │
│  4. Verification                                         │
│     ├─ Validate cloned stack                            │
│     ├─ Verify dependencies                              │
│     ├─ Run health checks                                │
│     └─ Update deployment manifest                       │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Cloning Workflow

```
[Source Stack] ──┐
                 │
        [1] Read Configuration
                 │
                 ├─> manifest.json
                 ├─> Pulumi state
                 └─> Stack outputs
                 │
        [2] Transform Configuration
                 │
                 ├─> Apply modifications
                 ├─> Update environment
                 ├─> Resolve dependencies
                 └─> Generate new config
                 │
        [3] Create Target Stack
                 │
                 ├─> pulumi stack init
                 ├─> pulumi config set (all)
                 └─> pulumi up (or import)
                 │
        [4] Verify & Register
                 │
                 ├─> Validate deployment
                 ├─> Update manifest
                 └─> Run health checks
                 │
                 v
           [Target Stack]
```

---

## Cloning Process

### Step-by-Step Process

#### Step 1: Pre-Clone Validation

```bash
# Validate source stack exists and is healthy
cloud validate-stack D1BRV40 network --environment dev
```

Checks:
- Source stack exists
- Source stack is deployed successfully
- Source environment is accessible
- Target environment is enabled

#### Step 2: Configuration Extraction

```bash
# Extract source configuration
cloud export-stack-config D1BRV40 network --environment dev --output network-config.json
```

Extracted data:
- Stack configuration values
- Pulumi config (encrypted secrets preserved)
- Resource outputs
- Dependencies

#### Step 3: Configuration Transformation

```bash
# Transform configuration for target
cloud transform-config network-config.json \
  --target-env stage \
  --target-region us-west-2 \
  --modify "vpcCidr=10.1.0.0/16" \
  --output network-config-stage.json
```

Transformations:
- Update environment-specific values
- Modify specified parameters
- Update region references
- Resolve new placeholders

#### Step 4: Target Stack Creation

```bash
# Create and deploy target stack
cloud import-stack-config D1BRV40 network-config-stage.json \
  --environment stage \
  --deploy
```

Actions:
- Create new Pulumi stack
- Apply transformed configuration
- Deploy resources
- Capture outputs

#### Step 5: Post-Clone Verification

```bash
# Verify cloned stack
cloud verify-stack D1BRV40 network --environment stage
```

Verifications:
- Stack deployed successfully
- All resources created
- Health checks pass
- Dependencies resolved

### Single-Command Cloning

All steps combined:

```bash
cloud clone-stack D1BRV40 network \
  --source-env dev \
  --target-env stage \
  --modify "vpcCidr=10.1.0.0/16" \
  --verify
```

---

## Configuration Handling

### Configuration Inheritance

Cloned stack inherits configuration with override precedence:

```
1. Source stack configuration (lowest priority)
2. Target environment defaults
3. Explicit modifications (--modify)
4. Runtime placeholders (highest priority)
```

### Modification Syntax

```bash
# Single modification
--modify "key=value"

# Multiple modifications
--modify "key1=value1" --modify "key2=value2"

# Nested modifications
--modify "config.database.instanceClass=db.r5.large"

# Array modifications
--modify "availabilityZones=[us-west-2a,us-west-2b]"

# Object modifications
--modify "tags={Environment:stage,Team:platform}"
```

### Example Configuration Transformation

**Source (dev):**
```json
{
  "vpcCidr": "10.0.0.0/16",
  "availabilityZones": 2,
  "enableNatGateway": false,
  "instanceType": "t3.micro"
}
```

**Modifications:**
```bash
--modify "vpcCidr=10.1.0.0/16"
--modify "availabilityZones=3"
--modify "enableNatGateway=true"
--modify "instanceType=t3.small"
```

**Target (stage):**
```json
{
  "vpcCidr": "10.1.0.0/16",
  "availabilityZones": 3,
  "enableNatGateway": true,
  "instanceType": "t3.small"
}
```

---

## State Management

### State Cloning Options

#### Option 1: No State (Default)
Clone configuration only, deploy from scratch.

**Command:**
```bash
cloud clone-stack D1BRV40 network --source-env dev --target-env stage
```

**Behavior:**
- Copies configuration
- Creates new resources
- No existing state
- Fresh deployment

#### Option 2: Import Existing Resources
Clone to manage existing AWS resources.

**Command:**
```bash
cloud clone-stack D1BRV40 network \
  --source-env dev \
  --target-env stage \
  --import-resources
```

**Behavior:**
- Copies configuration
- Imports existing AWS resources into Pulumi state
- No resource creation (unless missing)
- Manages existing infrastructure

#### Option 3: Copy State (Advanced)
Copy Pulumi state directly (use with caution).

**Command:**
```bash
cloud clone-stack D1BRV40 network \
  --source-env dev \
  --target-env stage \
  --copy-state \
  --confirm
```

**Behavior:**
- Copies configuration AND state
- No resource creation
- Assumes identical resources exist
- ⚠️ Dangerous if resources don't match

### State Export/Import

```bash
# Export source state
pulumi stack export --stack D1BRV40-dev > state-dev.json

# Import to target (after modification)
pulumi stack import --stack D1BRV40-stage < state-stage.json
```

---

## CLI Commands

### Clone Single Stack

```bash
cloud clone-stack <deployment-id> <stack-name> \
  --source-env <env> \
  --target-env <env> \
  [--target-region <region>] \
  [--mode <mode>] \
  [--modify <key=value>] \
  [--suffix <suffix>] \
  [--verify]
```

**Options:**
- `--source-env`: Source environment (dev, stage, prod)
- `--target-env`: Target environment (dev, stage, prod)
- `--target-region`: Target AWS region (optional)
- `--mode`: Cloning mode (config, full, cross-region)
- `--modify`: Configuration modifications (repeatable)
- `--suffix`: Stack name suffix (optional)
- `--verify`: Run post-clone verification

**Examples:**
```bash
# Basic clone
cloud clone-stack D1BRV40 network --source-env dev --target-env stage

# Clone with modifications
cloud clone-stack D1BRV40 network \
  --source-env dev \
  --target-env stage \
  --modify "vpcCidr=10.1.0.0/16"

# Cross-region clone
cloud clone-stack D1BRV40 network \
  --source-env prod \
  --target-env prod \
  --target-region us-west-2

# Clone to experimental environment
cloud clone-stack D1BRV40 database-rds \
  --source-env prod \
  --target-env dev \
  --suffix "-experiment"
```

### Clone Entire Deployment

```bash
cloud clone-deployment <deployment-id> \
  --source-env <env> \
  --target-env <env> \
  [--new-id <new-deployment-id>] \
  [--target-region <region>] \
  [--modify <key=value>] \
  [--exclude-stacks <stack-list>] \
  [--verify]
```

**Options:**
- `--source-env`: Source environment
- `--target-env`: Target environment
- `--new-id`: New deployment ID (optional, auto-generated if omitted)
- `--target-region`: Target AWS region (optional)
- `--modify`: Global configuration modifications
- `--exclude-stacks`: Comma-separated list of stacks to skip
- `--verify`: Run post-clone verification

**Examples:**
```bash
# Clone entire deployment to stage
cloud clone-deployment D1BRV40 \
  --source-env dev \
  --target-env stage

# Clone to new region
cloud clone-deployment D1BRV40 \
  --source-env prod \
  --target-env prod \
  --target-region us-west-2 \
  --new-id D2WEST2

# Clone with excluded stacks
cloud clone-deployment D1BRV40 \
  --source-env prod \
  --target-env dev \
  --exclude-stacks "monitoring,logging"
```

### Export/Import Stack Configuration

```bash
# Export stack configuration
cloud export-stack-config <deployment-id> <stack-name> \
  --environment <env> \
  --output <file>

# Import stack configuration
cloud import-stack-config <deployment-id> <config-file> \
  --environment <env> \
  [--deploy]
```

### Transform Configuration

```bash
# Transform configuration file
cloud transform-config <input-file> \
  --target-env <env> \
  [--target-region <region>] \
  [--modify <key=value>] \
  --output <output-file>
```

---

## REST API Endpoints

### Clone Stack

```http
POST /api/v1/deployments/:deploymentId/stacks/:stackName/clone
```

**Request Body:**
```json
{
  "sourceEnvironment": "dev",
  "targetEnvironment": "stage",
  "targetRegion": "us-west-2",
  "mode": "config",
  "modifications": {
    "vpcCidr": "10.1.0.0/16",
    "availabilityZones": 3
  },
  "verify": true
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "jobId": "job-abc123",
    "status": "cloning",
    "sourceStack": "D1BRV40-dev-network",
    "targetStack": "D1BRV40-stage-network",
    "estimatedDuration": 600
  }
}
```

### Clone Deployment

```http
POST /api/v1/deployments/:deploymentId/clone
```

**Request Body:**
```json
{
  "sourceEnvironment": "dev",
  "targetEnvironment": "stage",
  "newDeploymentId": "D2STAGE",
  "targetRegion": "us-west-2",
  "modifications": {
    "org": "CompanyB",
    "project": "ecommerce-clone"
  },
  "excludeStacks": ["monitoring", "logging"],
  "verify": true
}
```

### Export Stack Configuration

```http
GET /api/v1/deployments/:deploymentId/stacks/:stackName/export?environment=dev
```

**Response:**
```json
{
  "success": true,
  "data": {
    "stackName": "network",
    "environment": "dev",
    "configuration": {
      "vpcCidr": "10.0.0.0/16",
      "availabilityZones": 2
    },
    "outputs": {
      "vpcId": "vpc-abc123",
      "publicSubnetIds": ["subnet-1", "subnet-2"]
    },
    "dependencies": []
  }
}
```

---

## Implementation Examples

### Example 1: Environment Promotion Pipeline

```bash
#!/bin/bash
# promote-to-stage.sh

DEPLOYMENT_ID="D1BRV40"

echo "Promoting dev to stage..."

# Clone all stacks
cloud clone-deployment $DEPLOYMENT_ID \
  --source-env dev \
  --target-env stage \
  --modify "instanceType=t3.small" \
  --verify

# Run integration tests
cloud test $DEPLOYMENT_ID --environment stage

echo "Promotion complete!"
```

### Example 2: Multi-Region DR Setup

```bash
#!/bin/bash
# setup-dr-region.sh

DEPLOYMENT_ID="D1BRV40"
DR_REGION="us-west-2"
DR_DEPLOYMENT_ID="D2WEST2"

echo "Setting up DR in $DR_REGION..."

# Clone entire deployment to DR region
cloud clone-deployment $DEPLOYMENT_ID \
  --source-env prod \
  --target-env prod \
  --target-region $DR_REGION \
  --new-id $DR_DEPLOYMENT_ID \
  --verify

echo "DR region ready!"
```

### Example 3: Customer Onboarding Automation

```typescript
// onboard-customer.ts
import { CloudAPI } from '@cloud/api';

async function onboardCustomer(customerName: string) {
  const api = new CloudAPI();

  // Clone template deployment
  const result = await api.cloneDeployment('DTEMPLATE', {
    sourceEnvironment: 'dev',
    targetEnvironment: 'prod',
    modifications: {
      org: customerName,
      project: `${customerName}-prod`,
      'tags.Customer': customerName
    },
    verify: true
  });

  console.log(`Customer ${customerName} onboarded: ${result.newDeploymentId}`);
  return result.newDeploymentId;
}

// Usage
onboardCustomer('AcmeCorp');
```

### Example 4: Experimentation Workflow

```bash
#!/bin/bash
# experiment.sh

DEPLOYMENT_ID="D1BRV40"
STACK="database-rds"

# Clone to experimental environment
EXPERIMENT_STACK=$(cloud clone-stack $DEPLOYMENT_ID $STACK \
  --source-env prod \
  --target-env dev \
  --suffix "-experiment" \
  --modify "instanceClass=db.t3.micro")

# Run experiments
echo "Running experiments on $EXPERIMENT_STACK..."
# ... test changes ...

# Cleanup
cloud destroy-stack $DEPLOYMENT_ID ${STACK}-experiment --environment dev
```

---

## Conclusion

Stack Cloning is a powerful feature enabling rapid infrastructure duplication with configuration flexibility. Key capabilities include:

1. **Multiple Cloning Modes**: Config-only, full, and cross-region
2. **Flexible Modifications**: Override any configuration during cloning
3. **State Management**: Control over state handling
4. **Automation Support**: CLI and API for scripting
5. **Safety**: Independent clones, verification built-in

**Common Use Cases:**
- Environment promotion (dev → stage → prod)
- Multi-region deployment
- Testing and experimentation
- Customer onboarding
- Disaster recovery

For implementation details, see:
- Main Architecture Document (Multi-Stack-Architecture-3.0.md)
- CLI Commands Reference (CLI_Commands_Reference.3.0.md)
- REST API Documentation (REST_API_Documentation.3.0.md)
