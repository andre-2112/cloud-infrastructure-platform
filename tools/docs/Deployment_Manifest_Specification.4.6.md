# Cloud Architecture v4.6 - Deployment Manifest Specification

**Version:** 4.6
**Last Updated:** 2025-01-30
**Status:** Production Ready
**Architecture:** Aligned with v4.0 authoritative documents, enhanced in v4.5, v4.6

**Changes from v3.1 to v4.1:**
- **CRITICAL:** Changed from JSON to YAML format
- **CRITICAL:** Updated config file location to config/ subdirectory
- **CRITICAL:** Updated config format to Pulumi native format
- Updated placeholder syntax from `{{TYPE:source:key}}` to `${stack.output}` or `{{stack.output}}`
- Added enhanced template parameter system
- Documented cross-stack dependency workflow
- Added validation against enhanced stack templates
- Updated all examples to reflect Python CLI implementation
- Aligned with Complete_Stack_Management_Guide_v4.md

**Changes from v4.1 to v4.5:**
- **CRITICAL:** Added `pulumiOrg` field for Pulumi Cloud organization (distinct from `organization`)
- **CRITICAL:** Added `project` field for Pulumi Cloud project naming
- Documented dynamic Pulumi.yaml management integration
- All stacks default to `enabled: false` in templates
- Enhanced Pulumi stack naming: `{pulumiOrg}/{project}/{deployment-id}-{stack-name}-{environment}`

**Changes from v4.5 to v4.6:**
- **CRITICAL:** Composite Project Naming - config file key prefixes now use `{DeploymentID}-{Organization}-{Project}` format
- Configuration keys changed from `stackname:key` to `{composite-project}:key` format
- Complete deployment isolation in Pulumi Cloud via composite project names
- Updated ConfigGenerator to generate composite project prefixes
- Pulumi Cloud stack structure: `{pulumiOrg}/{composite-project}/{stack-name}-{environment}`
- Example: `andre-2112/DT28749-TestOrg-demo-test/network-dev`
- Config example: `DT28749-TestOrg-demo-test:vpcCidr: "10.0.0.0/16"`

---

## Table of Contents

1. [Overview](#overview)
2. [File Format and Location](#file-format-and-location)
3. [Manifest Schema](#manifest-schema)
4. [Deployment Metadata](#deployment-metadata)
5. [Environment Configuration](#environment-configuration)
6. [Stack Configuration](#stack-configuration)
7. [Runtime Placeholders](#runtime-placeholders)
8. [Configuration Files (Pulumi Format)](#configuration-files-pulumi-format)
9. [Cross-Stack Dependencies](#cross-stack-dependencies)
10. [Validation Rules](#validation-rules)
11. [Example Manifests](#example-manifests)
12. [Migration from Previous Versions](#migration-from-previous-versions)

---

## Overview

The Deployment Manifest is the **single source of truth** for all deployment configuration in Cloud Architecture v4.6. Each deployment has exactly one `deployment-manifest.yaml` file that defines:

- Deployment metadata (ID, organization, project, domain, pulumiOrg)
- Environment configurations (dev, stage, prod)
- Stack configurations and parameters
- Cross-stack dependencies
- Environment-specific overrides
- Pulumi Cloud organization structure (v4.5)
- Composite project naming for complete deployment isolation (NEW in v4.6)

### Key Principles

1. **Single YAML File Per Deployment**: One `deployment-manifest.yaml` per deployment
2. **Multi-Environment Support**: All three environments in single file
3. **Template-Based**: Generated from deployment templates, validated against stack templates
4. **Runtime Resolution**: Supports dynamic placeholder resolution for cross-stack references
5. **Validation Required**: Must pass validation against enhanced stack templates
6. **Deployment Isolation**: Each deployment gets unique Pulumi Cloud namespace (v4.6)

### File Location and Format

**Location:**
```
./cloud/deploy/<deployment-id>-<org>-<project>/deployment-manifest.yaml
```

**Format:** YAML (not JSON!)

**Example:**
```
./cloud/deploy/DT28749-TestOrg-demo-test/deployment-manifest.yaml
```

---

## File Format and Location

### Manifest File

**Path:** `deploy/<deployment-id>-<org>-<project>/deployment-manifest.yaml`

**Format:** YAML

**Naming:** `deployment-manifest.yaml` (hyphenated, lowercase)

### Generated Configuration Files

**Path:** `deploy/<deployment-id>-<org>-<project>/config/<stack>.<environment>.yaml`

**Format:** Pulumi native format with composite project prefix (v4.6)

**Examples:**
- `config/network.dev.yaml`
- `config/database-rds.prod.yaml`
- `config/services-ecs.stage.yaml`

**Key Changes:**
- **v3.1:** Configuration files flat in deployment root
- **v4.1:** Configuration files in `config/` subdirectory, Pulumi native format with stack name prefix
- **v4.6:** Configuration files use composite project name prefix for complete deployment isolation

---

## Manifest Schema

### High-Level Structure

```yaml
deployment_id: DT28749
organization: TestOrg
project: demo-test
domain: example.com
pulumiOrg: andre-2112

environments:
  dev:
    # Dev environment configuration
  stage:
    # Stage environment configuration
  prod:
    # Prod environment configuration

stacks:
  network:
    # Network stack configuration
  database-rds:
    # Database stack configuration
  # ... more stacks
```

### Complete YAML Schema

```yaml
# Required fields
deployment_id: string          # Format: [A-Z0-9]{6,10}
organization: string            # Business organization name
project: string                 # Business project name
domain: string                  # Domain name
pulumiOrg: string              # Pulumi Cloud organization (v4.5+)

# Optional metadata
description: string
tags:
  key: value

# Environments (at least 'dev' required)
environments:
  dev:
    region: string              # AWS region (e.g., us-east-1)
    account_id: string          # 12-digit AWS account ID
    tags:                       # Optional environment tags
      key: value

  stage:
    region: string
    account_id: string
    tags:
      key: value

  prod:
    region: string
    account_id: string
    tags:
      key: value

# Stacks
stacks:
  <stack-name>:
    enabled: boolean            # Whether stack is enabled
    dependencies: array         # From stack template (read-only)
    layer: number               # From stack template (read-only)
    config:                     # Stack configuration
      <param>: value            # Parameter values
    environments:               # Per-environment overrides
      dev:
        enabled: boolean
        config:
          <param>: value
      stage:
        enabled: boolean
        config:
          <param>: value
      prod:
        enabled: boolean
        config:
          <param>: value
```

---

## Deployment Metadata

### Deployment Object

The deployment metadata section contains information about the deployment:

```yaml
version: "4.6"
deployment_id: DT28749
organization: TestOrg
pulumiOrg: andre-2112
project: demo-test
domain: example.com
template: default
created_at: "2025-01-30T10:00:00Z"
description: "Demo deployment for platform testing"
metadata:
  generated_from_template: default
  generator_version: 0.8.0
  author: Cloud Platform
  created: "2025-01-30"
  architecture_version: "4.6"
tags:
  cost-center: engineering
  team: platform
  environment-type: multi-tier
```

### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `version` | string | Yes | Manifest format version (e.g., "4.6") |
| `deployment_id` | string | Yes | Unique deployment ID (format: alphanumeric, 6-10 chars) |
| `organization` | string | Yes | Business organization name (for directory naming, tags) |
| `pulumiOrg` | string | Yes | **v4.5+:** Pulumi Cloud organization (e.g., "andre-2112") |
| `project` | string | Yes | Business project name (used for Pulumi Cloud project naming) |
| `domain` | string | Yes | Domain name for the deployment |
| `template` | string | Yes | Template name used to generate manifest (e.g., "default") |
| `created_at` | string | Yes | ISO 8601 timestamp of deployment creation |
| `description` | string | No | Optional deployment description |
| `metadata` | object | No | Template generation metadata |
| `tags` | object | No | Custom key-value tags |

### Important Distinctions (v4.5+)

**`organization` vs `pulumiOrg`:**
- `organization`: Business organization name used for directory naming and tagging
  - Example: "TestOrg", "CompanyA", "Acme Corporation"
  - Used in deployment directory: `DT28749-TestOrg-demo-test/`
  - **v4.6:** Used in composite project name: `DT28749-TestOrg-demo-test`
- `pulumiOrg`: Pulumi Cloud organization identifier
  - Example: "andre-2112", "acme-corp", "my-pulumi-org"
  - Used in Pulumi stack path: `andre-2112/DT28749-TestOrg-demo-test/network-dev`
  - Must match your Pulumi Cloud organization name exactly

**`project` field:**
- Business project name used for Pulumi Cloud project grouping
- **v4.6:** Combined with deployment_id and organization to form composite project name
- All stacks for this deployment grouped under this composite project in Pulumi Cloud
- Enables proper organization: `{pulumiOrg}/{composite-project}/{stack-name}-{env}`
- Example: project "demo-test" becomes part of "DT28749-TestOrg-demo-test"

### Composite Project Naming (NEW in v4.6)

**Format:** `{DeploymentID}-{Organization}-{Project}`

**Example:** `DT28749-TestOrg-demo-test`

**Benefits:**
- Complete deployment isolation in Pulumi Cloud
- No stack naming conflicts between deployments
- Clear separation between business organization and Pulumi organization
- Simplified cleanup (all stacks under one composite project)

**Applied To:**
1. Pulumi Cloud project names
2. Configuration file key prefixes
3. Generated Pulumi.yaml `name` field

**Pulumi Cloud Stack Structure:**
```
{pulumiOrg}/{composite-project}/{stack-name}-{environment}

Example:
andre-2112/DT28749-TestOrg-demo-test/network-dev
andre-2112/DT28749-TestOrg-demo-test/compute-dev
andre-2112/DT28749-TestOrg-demo-test/storage-dev
```

For complete details, see: `Architecture_v4.6_Composite_Naming_Summary.md`

### Deployment ID Format

Deployment IDs are unique identifiers for each deployment:

- **Format**: Alphanumeric string, 6-10 characters
- **Examples**: `DT28749`, `D1TEST1`, `PRD00123`
- **Best Practices**:
  - Use prefixes: `DT` (demo/test), `PRD` (production), `STG` (staging)
  - Include sequential number for tracking
  - Keep under 10 characters for composite name readability

Generation (Python):
```python
def generate_deployment_id(prefix: str = "DT") -> str:
    timestamp = int(time.time() * 1000)
    base36 = base36encode(timestamp)
    return f"{prefix}{base36[-5:].upper()}"
```

---

## Environment Configuration

### Environment Object

Each environment (dev, stage, prod) has its own configuration:

```yaml
environments:
  dev:
    region: us-east-1
    account_id: "111111111111"
    tags:
      Environment: dev
      ManagedBy: cloud-platform

  stage:
    region: us-west-2
    account_id: "222222222222"
    tags:
      Environment: stage
      ManagedBy: cloud-platform

  prod:
    region: us-west-2
    account_id: "333333333333"
    tags:
      Environment: prod
      ManagedBy: cloud-platform
```

### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `region` | string | Yes | AWS region (e.g., us-east-1) |
| `account_id` | string | Yes | 12-digit AWS account ID |
| `tags` | object | No | Environment-specific resource tags |

### Environment Lifecycle

1. **dev**: Always enabled by default, primary development environment
2. **stage**: Optional staging environment
3. **prod**: Production environment

Enable/disable environments:
```bash
# Enable environment
cloud enable-environment DT28749 stage

# Disable environment
cloud disable-environment DT28749 prod
```

---

## Stack Configuration

### Stack Object

Each stack has configuration at two levels:
1. **Global stack configuration** (applies to all environments)
2. **Per-environment configuration** (overrides global)

```yaml
stacks:
  network:
    enabled: true
    dependencies: []        # From stack template (read-only)
    layer: 1                # From stack template (read-only)
    config:
      vpcCidr: "10.0.0.0/16"
      availabilityZones: 3
      enableNatGateway: true
      enableVpnGateway: false
    environments:
      dev:
        enabled: true
        config:
          availabilityZones: 2
          enableNatGateway: false
      stage:
        enabled: true
        config:
          availabilityZones: 2
      prod:
        enabled: true
        config:
          availabilityZones: 3
          enableNatGateway: true

  database-rds:
    enabled: true
    dependencies:           # From stack template
      - network
      - security
    layer: 3                # From stack template
    config:
      engine: postgres
      engineVersion: "15.3"
      instanceClass: db.t3.micro
      allocatedStorage: 100
      multiAz: false
      # Cross-stack reference (v4 syntax)
      subnets: "${network.privateSubnetIds}"
      securityGroups: "${security.databaseSecurityGroupIds}"
    environments:
      dev:
        enabled: true
        config:
          instanceClass: db.t3.micro
          allocatedStorage: 20
          multiAz: false
      prod:
        enabled: true
        config:
          instanceClass: db.r5.large
          allocatedStorage: 500
          multiAz: true
```

### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `enabled` | boolean | Yes | Whether stack is enabled globally |
| `dependencies` | array | Yes | List of stack dependencies (from template, read-only) |
| `layer` | number | Yes | Execution layer (from template, read-only) |
| `config` | object | No | Global stack configuration |
| `environments` | object | No | Per-environment stack configuration |

### Configuration Inheritance

Configuration values are resolved in this order (last wins):

1. **Template defaults** (from stack template `parameters.inputs.default`)
2. **Global stack config** (from `stacks.<name>.config`)
3. **Stack environment config** (from `stacks.<name>.environments.<env>.config`)
4. **Runtime resolution** (placeholder values resolved at deployment time)

Example resolution:
```yaml
# Template default: instanceClass = "db.t3.small"
# Global stack config: instanceClass = "db.t3.medium"
# Stack environment config (prod): instanceClass = "db.r5.large"
# → Final value for prod: "db.r5.large"
```

---

## Runtime Placeholders

### Placeholder Syntax (v4+)

Runtime placeholders allow dynamic value resolution at deployment time.

**Supported Syntaxes:**
- `${stack.output}` - Dollar-brace syntax (recommended)
- `{{stack.output}}` - Double-brace syntax (legacy)

**Both syntaxes are supported and equivalent.**

### Cross-Stack References

Reference outputs from other stacks:

```yaml
stacks:
  database-rds:
    config:
      vpcId: "${network.vpcId}"
      subnets: "${network.privateSubnetIds}"
      securityGroups: "${security.databaseSecurityGroupIds}"
```

**Resolution Process:**
1. Placeholder detected: `${network.privateSubnetIds}`
2. StackReferenceResolver queries Pulumi state for network stack
3. Retrieves output: `privateSubnetIds`
4. Value substituted in config before deployment

### Placeholder Resolution Order

1. **Cross-stack placeholders**: Resolved based on dependency order
2. **Validation**: All referenced stacks must exist and be deployed
3. **Type checking**: Output types validated against input parameter types

### Resolution Example

**Network Stack Output (TypeScript):**
```typescript
// stacks/network/index.ts
export const vpcId = vpc.id;
export const privateSubnetIds = privateSubnets.map(s => s.id);
```

**Database Stack Template:**
```yaml
# tools/templates/config/database-rds.yaml
parameters:
  inputs:
    subnets:
      type: array
      required: true
      description: "Subnet IDs for RDS"
```

**Deployment Manifest:**
```yaml
stacks:
  database-rds:
    config:
      subnets: "${network.privateSubnetIds}"  # Placeholder
```

**Generated Config (After Resolution) - v4.6 Format:**
```yaml
# deploy/DT28749-TestOrg-demo-test/config/database-rds.dev.yaml
DT28749-TestOrg-demo-test:subnets: '["subnet-abc123", "subnet-def456"]'
```

---

## Configuration Files (Pulumi Format)

### Generated Configuration Files

The ConfigGenerator creates Pulumi native format configuration files from the deployment manifest.

**Location:** `deploy/<deployment-id>-<org>-<project>/config/<stack>.<environment>.yaml`

**Format:** Pulumi native key-value format with composite project prefix (v4.6)

### Pulumi Native Format (v4.6)

**Format:** `{composite-project}:{key}: "value"`

**Composite Project:** `{DeploymentID}-{Organization}-{Project}`

**Rules:**
1. All keys prefixed with composite project name: `DT28749-TestOrg-demo-test:vpcCidr`
2. All values are strings: `"10.0.0.0/16"`
3. Complex types serialized as JSON strings: `'["subnet-1", "subnet-2"]'`
4. AWS provider config: `aws:region: "us-east-1"`

### Example Configuration File (v4.6)

**Source Manifest:**
```yaml
deployment_id: DT28749
organization: TestOrg
project: demo-test
pulumiOrg: andre-2112

environments:
  dev:
    region: us-east-1
    account_id: "111111111111"

stacks:
  network:
    config:
      vpcCidr: "10.0.0.0/16"
      availabilityZones: 2
      enableNatGateway: false
```

**Generated Config (deploy/DT28749-TestOrg-demo-test/config/network.dev.yaml) - v4.6:**
```yaml
DT28749-TestOrg-demo-test:deploymentId: "DT28749"
DT28749-TestOrg-demo-test:organization: "TestOrg"
DT28749-TestOrg-demo-test:project: "demo-test"
DT28749-TestOrg-demo-test:domain: "example.com"
DT28749-TestOrg-demo-test:environment: "dev"
DT28749-TestOrg-demo-test:region: "us-east-1"
DT28749-TestOrg-demo-test:accountId: "111111111111"
DT28749-TestOrg-demo-test:stackName: "network"
DT28749-TestOrg-demo-test:layer: "1"
DT28749-TestOrg-demo-test:vpcCidr: "10.0.0.0/16"
DT28749-TestOrg-demo-test:availabilityZones: "2"
DT28749-TestOrg-demo-test:enableNatGateway: "false"
aws:region: "us-east-1"
```

### Key Format Changes Across Versions

| Version | Key Format | Example |
|---------|-----------|---------|
| **v3.1** | Nested YAML | `config.vpcCidr: "10.0.0.0/16"` |
| **v4.1-v4.5** | Stack name prefix | `network:vpcCidr: "10.0.0.0/16"` |
| **v4.6** | Composite project prefix | `DT28749-TestOrg-demo-test:vpcCidr: "10.0.0.0/16"` |

### Benefits of Composite Project Prefix (v4.6)

1. **Complete Deployment Isolation**: Each deployment gets unique namespace in Pulumi Cloud
2. **No Naming Conflicts**: Multiple deployments can use same stack names
3. **Clear Organization**: Immediately identifies which deployment configuration belongs to
4. **Simplified Cleanup**: All stacks for deployment grouped under composite project name

---

## Cross-Stack Dependencies

### Declaring Dependencies

Dependencies are declared in **stack templates** (single source of truth):

**Stack Template (tools/templates/config/database-rds.yaml):**
```yaml
name: database-rds
version: "1.0"

parameters:
  inputs:
    subnets:
      type: array
      required: true
      description: "Subnet IDs for RDS"

    securityGroups:
      type: array
      required: true
      description: "Security group IDs"

dependencies:
  - network
  - security

layer: 3
```

### Using Cross-Stack References

**In Deployment Manifest:**
```yaml
stacks:
  network:
    enabled: true
    config:
      vpcCidr: "10.0.0.0/16"

  security:
    enabled: true
    config:
      vpcId: "${network.vpcId}"

  database-rds:
    enabled: true
    dependencies:  # From template (read-only)
      - network
      - security
    config:
      subnets: "${network.privateSubnetIds}"
      securityGroups: "${security.databaseSecurityGroupIds}"
```

### Resolution Workflow

```
1. User writes manifest with placeholders
   └─> subnets: "${network.privateSubnetIds}"

2. Deployment starts
   └─> Network stack deployed first (layer 1)
   └─> Outputs exported: privateSubnetIds = ["subnet-1", "subnet-2"]

3. Database stack deployment begins (layer 3)
   └─> StackReferenceResolver queries network stack
   └─> Retrieves privateSubnetIds output
   └─> Generates config with resolved values

4. Generated config (v4.6 format):
   └─> DT28749-TestOrg-demo-test:subnets: '["subnet-1", "subnet-2"]'

5. Database stack deploys with resolved values
```

### Validation

**Pre-Deployment Validation:**
1. All referenced stacks exist in manifest
2. All referenced stacks are enabled
3. Dependency order is correct (no cycles)
4. Referenced outputs exist in stack template

**Runtime Validation:**
1. Referenced stack is deployed
2. Output exists in Pulumi state
3. Output type matches input parameter type

---

## Validation Rules

### Manifest Validation

The manifest must pass validation before deployment:

```bash
# Validate manifest
cloud validate DT28749

# Validate with strict mode
cloud validate DT28749 --strict
```

### Validation Checks

#### 1. Schema Validation
- YAML syntax is valid
- All required fields are present
- Field types match schema
- Field values match constraints

#### 2. Deployment Metadata Validation
- Deployment ID matches expected format
- Organization, project, and domain names are non-empty
- No invalid characters in names
- pulumiOrg matches Pulumi Cloud organization

#### 3. Environment Validation
- At least `dev` environment is present
- All AWS account IDs are 12 digits
- All regions are valid AWS regions
- Account IDs are unique per environment

#### 4. Stack Validation (Enhanced v4)
- All stacks exist in stack templates
- All stack configurations match template `parameters.inputs`
- All dependencies exist in the deployment
- No circular dependencies exist
- Layer assignments are consistent

#### 5. Configuration Validation
- All parameters match stack template declarations
- Required parameters are provided
- Parameter types match template specifications
- Default values used when appropriate

#### 6. Placeholder Validation
- All placeholders use valid syntax (`${...}` or `{{...}}`)
- All referenced stacks exist in manifest
- All referenced outputs exist in stack templates
- No infinite placeholder loops

#### 7. Cross-Stack Dependency Validation
- Dependencies form a valid DAG (Directed Acyclic Graph)
- All referenced stacks are enabled
- Dependency chains are resolvable
- Output types match input parameter types

### Validation Output

```json
{
  "valid": true,
  "errors": [],
  "warnings": [
    "Stack 'monitoring' is disabled in prod environment",
    "Parameter 'backupRetentionDays' using default value"
  ],
  "info": {
    "totalStacks": 12,
    "enabledStacks": 11,
    "environments": ["dev", "stage", "prod"],
    "dependencyLayers": 5,
    "crossStackReferences": 8,
    "compositeProject": "DT28749-TestOrg-demo-test"
  }
}
```

---

## Example Manifests

### Example 1: Minimal Deployment (v4.6)

```yaml
version: "4.6"
deployment_id: DMIN001
organization: StartupCo
project: mvp
domain: startup.example.com
pulumiOrg: startupco-cloud

environments:
  dev:
    region: us-east-1
    account_id: "111111111111"

stacks:
  network:
    enabled: true
    dependencies: []
    layer: 1
    config:
      vpcCidr: "10.0.0.0/16"
      availabilityZones: 2

  compute-ec2:
    enabled: true
    dependencies:
      - network
    layer: 2
    config:
      instanceType: t3.micro
      vpcId: "${network.vpcId}"
      subnetIds: "${network.publicSubnetIds}"
```

**Resulting Pulumi Cloud Structure:**
```
startupco-cloud/DMIN001-StartupCo-mvp/network-dev
startupco-cloud/DMIN001-StartupCo-mvp/compute-ec2-dev
```

**Generated Config Example (config/network.dev.yaml):**
```yaml
DMIN001-StartupCo-mvp:deploymentId: "DMIN001"
DMIN001-StartupCo-mvp:organization: "StartupCo"
DMIN001-StartupCo-mvp:project: "mvp"
DMIN001-StartupCo-mvp:vpcCidr: "10.0.0.0/16"
DMIN001-StartupCo-mvp:availabilityZones: "2"
aws:region: "us-east-1"
```

### Example 2: Multi-Environment Deployment (v4.6)

```yaml
version: "4.6"
deployment_id: DT28749
organization: TestOrg
project: platform
domain: test.example.com
pulumiOrg: andre-2112
description: "Multi-environment test deployment"

environments:
  dev:
    region: us-east-1
    account_id: "111111111111"
    tags:
      Environment: dev
      CostCenter: engineering

  stage:
    region: us-west-2
    account_id: "222222222222"
    tags:
      Environment: stage
      CostCenter: engineering

  prod:
    region: us-west-2
    account_id: "333333333333"
    tags:
      Environment: prod
      CostCenter: engineering

stacks:
  network:
    enabled: true
    dependencies: []
    layer: 1
    config:
      vpcCidr: "10.0.0.0/16"
      availabilityZones: 3
      enableNatGateway: true
    environments:
      dev:
        enabled: true
        config:
          availabilityZones: 2
          enableNatGateway: false
      stage:
        enabled: true
        config:
          availabilityZones: 2
      prod:
        enabled: true
        config:
          availabilityZones: 3
          enableNatGateway: true

  security:
    enabled: true
    dependencies:
      - network
    layer: 2
    config:
      vpcId: "${network.vpcId}"
      enableGuardDuty: true
    environments:
      dev:
        enabled: true
        config:
          enableGuardDuty: false
      prod:
        enabled: true
        config:
          enableGuardDuty: true

  database-rds:
    enabled: true
    dependencies:
      - network
      - security
    layer: 3
    config:
      engine: postgres
      engineVersion: "15.3"
      instanceClass: db.t3.micro
      allocatedStorage: 100
      multiAz: false
      subnets: "${network.privateSubnetIds}"
      securityGroups: "${security.databaseSecurityGroupIds}"
    environments:
      dev:
        enabled: true
        config:
          instanceClass: db.t3.micro
          allocatedStorage: 20
          multiAz: false
      prod:
        enabled: true
        config:
          instanceClass: db.r5.large
          allocatedStorage: 500
          multiAz: true
          backupRetentionPeriod: 30
```

**Resulting Pulumi Cloud Structure:**
```
andre-2112/DT28749-TestOrg-platform/network-dev
andre-2112/DT28749-TestOrg-platform/security-dev
andre-2112/DT28749-TestOrg-platform/database-rds-dev
andre-2112/DT28749-TestOrg-platform/network-stage
andre-2112/DT28749-TestOrg-platform/security-stage
andre-2112/DT28749-TestOrg-platform/database-rds-stage
andre-2112/DT28749-TestOrg-platform/network-prod
andre-2112/DT28749-TestOrg-platform/security-prod
andre-2112/DT28749-TestOrg-platform/database-rds-prod
```

---

## Migration from Previous Versions

### Migration from v4.5 to v4.6

**Key Change:** Configuration file key prefixes changed from stack name to composite project name.

**What Changed:**
- Configuration file format changed from `stackname:key` to `{deployment-id}-{org}-{project}:key`
- Pulumi Cloud project naming now uses composite format
- Generated Pulumi.yaml uses composite project name

**Migration Steps:**

**1. No manifest changes required**
The deployment manifest format is unchanged. Composite naming is automatically applied during config generation.

**2. Regenerate configuration files:**
```bash
# Regenerate all config files with new composite prefix format
cloud generate-configs DT28749

# This regenerates:
# config/network.dev.yaml
# config/security.dev.yaml
# etc.
```

**3. Update Pulumi stacks (if needed):**
```bash
# The deployment_context automatically handles Pulumi.yaml generation
# No manual intervention needed

# Deploy with new composite naming
cloud deploy DT28749
```

**4. Verify Pulumi Cloud structure:**
```bash
pulumi stack ls

# Expected output (v4.6):
# andre-2112/DT28749-TestOrg-demo-test/network-dev
# andre-2112/DT28749-TestOrg-demo-test/security-dev

# Previous output (v4.5):
# andre-2112/demo-test/DT28749-network-dev
# andre-2112/demo-test/DT28749-security-dev
```

**Compatibility Notes:**
- Existing v4.5 deployments continue to work
- New deployments automatically use v4.6 composite naming
- No breaking changes to manifest schema
- Configuration files automatically regenerated with correct format

### Migration from v3.1 to v4.6

For complete migration from v3.1, follow these steps:

**1. Convert JSON to YAML:**
```bash
# Use migration tool
cloud migrate-manifest D1BRV40 --from-version 3.1

# Or manually convert
python -c "import json, yaml; print(yaml.dump(json.load(open('manifest.json'))))" > deployment-manifest.yaml
```

**2. Update placeholder syntax:**
```yaml
# Old (v3.1):
vpcId: "{{RUNTIME:network:vpcId}}"

# New (v4.6):
vpcId: "${network.vpcId}"
```

**3. Add pulumiOrg field:**
```yaml
# Add to manifest
pulumiOrg: your-pulumi-org-name
```

**4. Move config files:**
```bash
# Create config directory
mkdir -p deploy/D1BRV40-CompanyA-project/config/

# Move config files
mv deploy/D1BRV40/*.dev.yaml deploy/D1BRV40-CompanyA-project/config/
mv deploy/D1BRV40/*.stage.yaml deploy/D1BRV40-CompanyA-project/config/
mv deploy/D1BRV40/*.prod.yaml deploy/D1BRV40-CompanyA-project/config/
```

**5. Regenerate configs with composite naming:**
```bash
cloud generate-configs D1BRV40
```

**6. Validate migrated manifest:**
```bash
cloud validate D1BRV40 --strict
```

### Breaking Changes Summary

| From v3.1 | From v4.5 |
|-----------|-----------|
| Manifest format: JSON → YAML | None (manifest unchanged) |
| Config location: flat → config/ | None |
| Config format: nested → Pulumi native | Key prefix: stackname → composite |
| Placeholder: {{TYPE:...}} → ${...} | None |
| Dependencies: in manifest → in templates | None |

---

## Conclusion

The Deployment Manifest in v4.6 provides a comprehensive, validated configuration system for multi-stack deployments with complete deployment isolation. Key features include:

- **YAML Format**: Human-readable and maintainable
- **Pulumi Native Configs**: Direct integration with Pulumi
- **Composite Project Naming (v4.6)**: Complete deployment isolation in Pulumi Cloud
- **Enhanced Validation**: Template-based validation ensures correctness
- **Cross-Stack References**: Simple `${stack.output}` syntax
- **Multi-Environment**: Unified configuration for all environments
- **Type Safety**: Parameter types validated against stack templates
- **No Naming Conflicts**: Each deployment gets unique namespace

For implementation details, see:
- Multi_Stack_Architecture.4.6.md - Architecture overview
- Architecture_v4.6_Composite_Naming_Summary.md - Composite naming details
- Complete_Stack_Management_Guide_v4.6.md - Complete workflow guide
- Stack_Parameters_and_Registration_Guide_v4.6.md - Parameter system details
- Directory_Structure_Diagram.4.6.md - Directory layout

---

**Document Version:** 4.6
**Last Updated:** 2025-01-30
**Architecture Version:** 4.6
**Previous Version:** Deployment_Manifest_Specification.4.5.md
**Authoritative Documents:** Complete_Stack_Management_Guide_v4.6.md, Stack_Parameters_and_Registration_Guide_v4.6.md, Complete_Guide_Templates_Stacks_Config_and_Registration_v4.6.md, Architecture_v4.6_Composite_Naming_Summary.md
