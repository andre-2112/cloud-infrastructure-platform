# Cloud Architecture v4.5 - Deployment Manifest Specification

**Version:** 4.5
**Last Updated:** 2025-10-30
**Status:** Production Ready
**Architecture:** Aligned with v4.0 authoritative documents, enhanced in v4.5

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
12. [Migration from v3.1](#migration-from-v31)

---

## Overview

The Deployment Manifest is the **single source of truth** for all deployment configuration in Cloud Architecture v4.5. Each deployment has exactly one `deployment-manifest.yaml` file that defines:

- Deployment metadata (ID, organization, project, domain, pulumiOrg)
- Environment configurations (dev, stage, prod)
- Stack configurations and parameters
- Cross-stack dependencies
- Environment-specific overrides
- Pulumi Cloud organization structure (NEW in v4.5)

### Key Principles

1. **Single YAML File Per Deployment**: One `deployment-manifest.yaml` per deployment
2. **Multi-Environment Support**: All three environments in single file
3. **Template-Based**: Generated from deployment templates, validated against stack templates
4. **Runtime Resolution**: Supports dynamic placeholder resolution for cross-stack references
5. **Validation Required**: Must pass validation against enhanced stack templates

### File Location and Format

**Location:**
```
./cloud/deploy/<deployment-id>-<org>-<project>/deployment-manifest.yaml
```

**Format:** YAML (not JSON!)

**Example:**
```
./cloud/deploy/D1TEST1-TestOrg-test-project/deployment-manifest.yaml
```

---

## File Format and Location

### Manifest File

**Path:** `deploy/<deployment-id>-<org>-<project>/deployment-manifest.yaml`

**Format:** YAML

**Naming:** `deployment-manifest.yaml` (hyphenated, lowercase)

### Generated Configuration Files

**Path:** `deploy/<deployment-id>-<org>-<project>/config/<stack>.<environment>.yaml`

**Format:** Pulumi native format

**Examples:**
- `config/network.dev.yaml`
- `config/database-rds.prod.yaml`
- `config/services-ecs.stage.yaml`

**Key Change from v3.1:**
- Configuration files now in `config/` subdirectory (not flat in deployment root)
- Pulumi native format: `stackname:key: "value"` (not nested YAML)

---

## Manifest Schema

### High-Level Structure

```yaml
deployment_id: D1TEST1
organization: TestOrg
project: test-project
domain: example.com

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
deployment_id: string          # Format: D[A-Z0-9]{6}
organization: string            # Organization name
project: string                 # Project name
domain: string                  # Domain name

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
version: "4.5"
deployment_id: D1TEST1
organization: TestOrg
pulumiOrg: acme-corp                        # NEW in v4.5: Pulumi Cloud organization
project: test-project
domain: example.com
template: default
created_at: "2025-10-30T10:00:00Z"
description: "Test deployment for e-commerce platform"
metadata:
  generated_from_template: default
  generator_version: 0.7.0
  author: Cloud Platform
  created: "2025-10-30"
  architecture_version: "4.5"
tags:
  cost-center: engineering
  team: platform
  environment-type: multi-tier
```

### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `version` | string | Yes | Manifest format version (e.g., "4.5") |
| `deployment_id` | string | Yes | Unique deployment ID (format: `D[A-Z0-9]{6}`) |
| `organization` | string | Yes | Business organization name (for directory naming, tags) |
| `pulumiOrg` | string | Yes | **NEW v4.5:** Pulumi Cloud organization (e.g., "acme-corp") |
| `project` | string | Yes | Business project name (used for Pulumi Cloud project naming) |
| `domain` | string | Yes | Domain name for the deployment |
| `template` | string | Yes | Template name used to generate manifest (e.g., "default") |
| `created_at` | string | Yes | ISO 8601 timestamp of deployment creation |
| `description` | string | No | Optional deployment description |
| `metadata` | object | No | Template generation metadata |
| `tags` | object | No | Custom key-value tags |

### Important Distinctions (NEW in v4.5)

**`organization` vs `pulumiOrg`:**
- `organization`: Business organization name used for directory naming and tagging
  - Example: "TestOrg", "CompanyA", "Acme Corporation"
  - Used in deployment directory: `D1TEST1-TestOrg-test-project/`
- `pulumiOrg`: Pulumi Cloud organization identifier
  - Example: "andre-2112", "acme-corp", "my-pulumi-org"
  - Used in Pulumi stack naming: `andre-2112/test-project/D1TEST1-network-dev`
  - Must match your Pulumi Cloud organization name exactly

**`project` field:**
- Business project name used for Pulumi Cloud project grouping
- All stacks for this deployment grouped under this project in Pulumi Cloud
- Enables proper organization: `{pulumiOrg}/{project}/{deployment-id}-{stack}-{env}`
- Example: project "ecommerce" groups all ecommerce stacks together

### Deployment ID Format

Deployment IDs follow the format: `D<base36-timestamp>`

- **Prefix**: `D` (for Deployment)
- **Length**: 7 characters (1 prefix + 6 alphanumeric)
- **Encoding**: Base36 (uppercase)
- **Example**: `D1TEST1`, `D1BRV40`

Generation (Python):
```python
def generate_deployment_id() -> str:
    timestamp = int(time.time() * 1000)
    base36 = base36encode(timestamp)
    return f"D{base36[-6:].upper().zfill(6)}"
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
cloud-cli enable-environment D1TEST1 stage

# Disable environment
cloud-cli disable-environment D1TEST1 prod
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
      # Cross-stack reference (NEW v4 syntax)
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

### Placeholder Syntax (NEW in v4)

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

**Generated Config (After Resolution):**
```yaml
# deploy/D1TEST1/config/database-rds.dev.yaml
database-rds:subnets: '["subnet-abc123", "subnet-def456"]'
```

---

## Configuration Files (Pulumi Format)

### Generated Configuration Files

The ConfigGenerator creates Pulumi native format configuration files from the deployment manifest.

**Location:** `deploy/<deployment-id>/config/<stack>.<environment>.yaml`

**Format:** Pulumi native key-value format

### Pulumi Native Format

**Format:** `stackname:key: "value"`

**Rules:**
1. All keys prefixed with stack name: `network:vpcCidr`
2. All values are strings: `"10.0.0.0/16"`
3. Complex types serialized as JSON strings: `'["subnet-1", "subnet-2"]'`
4. AWS provider config: `aws:region: "us-east-1"`

### Example Configuration File

**Source Manifest:**
```yaml
deployment_id: D1TEST1
organization: TestOrg
project: test-project

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

**Generated Config (deploy/D1TEST1/config/network.dev.yaml):**
```yaml
network:deploymentId: "D1TEST1"
network:organization: "TestOrg"
network:project: "test-project"
network:domain: "example.com"
network:environment: "dev"
network:region: "us-east-1"
network:accountId: "111111111111"
network:stackName: "network"
network:layer: "1"
network:vpcCidr: "10.0.0.0/16"
network:availabilityZones: "2"
network:enableNatGateway: "false"
aws:region: "us-east-1"
```

### Key Differences from v3.1

| Aspect | v3.1 | v4.1 |
|--------|------|------|
| **File location** | `deploy/<id>/*.yaml` | `deploy/<id>/config/*.yaml` |
| **Format** | Nested YAML dictionary | Pulumi flat key-value |
| **Key format** | `config.vpcCidr` | `network:vpcCidr` |
| **Value type** | Mixed types | All strings |
| **Complex types** | Native YAML | JSON-serialized strings |

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

4. Generated config:
   └─> database-rds:subnets: '["subnet-1", "subnet-2"]'

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
cloud-cli validate D1TEST1

# Validate with strict mode
cloud-cli validate D1TEST1 --strict
```

### Validation Checks

#### 1. Schema Validation
- YAML syntax is valid
- All required fields are present
- Field types match schema
- Field values match constraints

#### 2. Deployment Metadata Validation
- Deployment ID matches format `D[A-Z0-9]{6}`
- Organization, project, and domain names are non-empty
- No invalid characters in names

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
    "crossStackReferences": 8
  }
}
```

---

## Example Manifests

### Example 1: Minimal Deployment

```yaml
deployment_id: DMIN001
organization: StartupCo
project: mvp
domain: startup.example.com

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

### Example 2: Multi-Environment Deployment

```yaml
deployment_id: D1TEST1
organization: TestOrg
project: test-project
domain: test.example.com
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

### Example 3: Microservices Deployment

```yaml
deployment_id: DMICRO1
organization: TechCorp
project: microservices
domain: api.techcorp.com

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
      availabilityZones: 3

  services-ecr:
    enabled: true
    dependencies: []
    layer: 1
    config:
      repositories:
        - api-service
        - worker-service
        - frontend

  services-ecs:
    enabled: true
    dependencies:
      - network
      - services-ecr
    layer: 2
    config:
      clusterName: microservices-cluster
      vpcId: "${network.vpcId}"
      privateSubnets: "${network.privateSubnetIds}"
      publicSubnets: "${network.publicSubnetIds}"

  containers-apps:
    enabled: true
    dependencies:
      - network
      - services-ecs
      - services-ecr
    layer: 3
    config:
      services:
        - name: api-service
          image: "${services-ecr.apiServiceImageUri}"
          cpu: "256"
          memory: "512"
          desiredCount: 2
        - name: worker-service
          image: "${services-ecr.workerServiceImageUri}"
          cpu: "256"
          memory: "512"
          desiredCount: 1
```

---

## Migration from v3.1

### Key Changes Summary

| Aspect | v3.1 | v4.1 |
|--------|------|------|
| **Manifest format** | JSON | YAML |
| **Manifest filename** | `manifest.json` | `deployment-manifest.yaml` |
| **Config location** | `deploy/<id>/*.yaml` | `deploy/<id>/config/*.yaml` |
| **Config format** | Nested YAML | Pulumi native format |
| **Placeholder syntax** | `{{TYPE:source:key}}` | `${stack.output}` or `{{stack.output}}` |
| **Dependencies** | In manifest | In stack templates (read-only in manifest) |
| **Validation** | Basic schema | Enhanced template-based validation |

### Migration Steps

**1. Convert JSON to YAML:**
```bash
# Use migration tool
cloud-cli migrate-manifest D1BRV40 --from-version 3.1

# Or manually convert
python -c "import json, yaml; print(yaml.dump(json.load(open('manifest.json'))))" > deployment-manifest.yaml
```

**2. Update placeholder syntax:**
```yaml
# Old (v3.1):
vpcId: "{{RUNTIME:network:vpcId}}"

# New (v4.1):
vpcId: "${network.vpcId}"
```

**3. Move config files:**
```bash
# Create config directory
mkdir -p deploy/D1BRV40/config/

# Move config files
mv deploy/D1BRV40/*.dev.yaml deploy/D1BRV40/config/
mv deploy/D1BRV40/*.stage.yaml deploy/D1BRV40/config/
mv deploy/D1BRV40/*.prod.yaml deploy/D1BRV40/config/
```

**4. Convert config format:**
```bash
# Use config generator
cloud-cli generate-configs D1BRV40

# This regenerates all config files in Pulumi native format
```

**5. Validate migrated manifest:**
```bash
cloud-cli validate D1BRV40 --strict
```

### Compatibility Notes

**Breaking Changes:**
- Manifest format changed from JSON to YAML
- Config files moved to config/ subdirectory
- Config format changed to Pulumi native format
- Placeholder syntax simplified

**Backward Compatibility:**
- Old placeholder syntax `{{...}}` still supported (translated to new syntax)
- Migration tool handles most conversions automatically

---

## Conclusion

The Deployment Manifest in v4.1 provides a comprehensive, validated configuration system for multi-stack deployments. Key features include:

- **YAML Format**: Human-readable and maintainable
- **Pulumi Native Configs**: Direct integration with Pulumi
- **Enhanced Validation**: Template-based validation ensures correctness
- **Cross-Stack References**: Simple `${stack.output}` syntax
- **Multi-Environment**: Unified configuration for all environments
- **Type Safety**: Parameter types validated against stack templates

For implementation details, see:
- Multi_Stack_Architecture.4.1.md - Architecture overview
- Complete_Stack_Management_Guide_v4.md - Complete workflow guide
- Stack_Parameters_and_Registration_Guide_v4.md - Parameter system details
- Directory_Structure_Diagram.4.1.md - Directory layout

---

**Document Version:** 4.1
**Last Updated:** 2025-10-29
**Architecture Version:** 4.1
**Authoritative Documents:** Complete_Stack_Management_Guide_v4.md, Stack_Parameters_and_Registration_Guide_v4.md, Complete_Guide_Templates_Stacks_Config_and_Registration_v4.md
