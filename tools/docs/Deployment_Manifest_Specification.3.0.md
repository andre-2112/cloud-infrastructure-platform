# Cloud Architecture v3.0 - Deployment Manifest Specification

**Version:** 3.0
**Last Updated:** 2025-10-09
**Status:** Production Ready

---

## Table of Contents

1. [Overview](#overview)
2. [Manifest File Structure](#manifest-file-structure)
3. [Manifest Schema](#manifest-schema)
4. [Deployment Metadata](#deployment-metadata)
5. [Environment Configuration](#environment-configuration)
6. [Stack Configuration](#stack-configuration)
7. [Runtime Placeholders](#runtime-placeholders)
8. [Validation Rules](#validation-rules)
9. [Example Manifests](#example-manifests)
10. [Migration from 2.3](#migration-from-23)

---

## Overview

The Deployment Manifest is the **single source of truth** for all deployment configuration in Cloud Architecture v3.0. Each deployment has exactly one `manifest.json` file that defines:

- Deployment metadata (ID, organization, project, template)
- Environment configurations (dev, stage, prod)
- Stack configurations per environment
- AWS account and region mappings
- Custom parameters and overrides

### Key Principles

1. **Single File Per Deployment**: One `manifest.json` per deployment
2. **Multi-Environment Support**: All three environments in single file
3. **Template-Based**: Generated from deployment templates
4. **Runtime Resolution**: Supports dynamic value placeholders
5. **Validation Required**: Must pass validation before deployment

### File Location

```
./cloud/deploy/<deployment-id>/manifest.json
```

Example:
```
./cloud/deploy/D1BRV40/manifest.json
```

---

## Manifest File Structure

### High-Level Structure

```json
{
  "deployment": {
    // Deployment metadata
  },
  "environments": {
    "dev": {
      // Dev environment configuration
    },
    "stage": {
      // Stage environment configuration
    },
    "prod": {
      // Prod environment configuration
    }
  },
  "stacks": {
    "network": {
      // Stack-level configuration
    },
    "security": {
      // Stack-level configuration
    }
    // ... more stacks
  }
}
```

---

## Manifest Schema

### Complete JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Cloud Architecture v3.0 Deployment Manifest",
  "type": "object",
  "required": ["deployment", "environments", "stacks"],
  "properties": {
    "deployment": {
      "type": "object",
      "required": ["id", "org", "project", "template", "createdAt"],
      "properties": {
        "id": {
          "type": "string",
          "pattern": "^D[A-Z0-9]{6}$",
          "description": "Unique deployment ID (e.g., D1BRV40)"
        },
        "org": {
          "type": "string",
          "minLength": 1,
          "maxLength": 100,
          "description": "Organization name"
        },
        "project": {
          "type": "string",
          "minLength": 1,
          "maxLength": 100,
          "description": "Project name"
        },
        "template": {
          "type": "string",
          "enum": ["default", "minimal", "microservices", "data-platform"],
          "description": "Deployment template name"
        },
        "createdAt": {
          "type": "string",
          "format": "date-time",
          "description": "ISO 8601 timestamp of creation"
        },
        "updatedAt": {
          "type": "string",
          "format": "date-time",
          "description": "ISO 8601 timestamp of last update"
        },
        "description": {
          "type": "string",
          "description": "Optional deployment description"
        },
        "tags": {
          "type": "object",
          "additionalProperties": {
            "type": "string"
          },
          "description": "Custom tags for deployment"
        }
      }
    },
    "environments": {
      "type": "object",
      "required": ["dev"],
      "properties": {
        "dev": { "$ref": "#/definitions/environment" },
        "stage": { "$ref": "#/definitions/environment" },
        "prod": { "$ref": "#/definitions/environment" }
      }
    },
    "stacks": {
      "type": "object",
      "additionalProperties": {
        "$ref": "#/definitions/stack"
      }
    }
  },
  "definitions": {
    "environment": {
      "type": "object",
      "required": ["enabled", "account", "region"],
      "properties": {
        "enabled": {
          "type": "boolean",
          "description": "Whether environment is enabled for deployment"
        },
        "account": {
          "type": "string",
          "pattern": "^[0-9]{12}$",
          "description": "12-digit AWS account ID"
        },
        "region": {
          "type": "string",
          "pattern": "^[a-z]{2}-[a-z]+-[0-9]$",
          "description": "AWS region (e.g., us-east-1)"
        },
        "tags": {
          "type": "object",
          "additionalProperties": {
            "type": "string"
          },
          "description": "Environment-specific tags"
        },
        "config": {
          "type": "object",
          "description": "Environment-specific configuration overrides"
        }
      }
    },
    "stack": {
      "type": "object",
      "required": ["enabled", "dependencies"],
      "properties": {
        "enabled": {
          "type": "boolean",
          "description": "Whether stack is enabled globally"
        },
        "dependencies": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "List of stack dependencies (from template)"
        },
        "priority": {
          "type": "number",
          "minimum": 0,
          "maximum": 100,
          "description": "Stack priority (0-100, higher = earlier deployment)"
        },
        "config": {
          "type": "object",
          "description": "Stack-level configuration"
        },
        "environments": {
          "type": "object",
          "properties": {
            "dev": { "$ref": "#/definitions/stackEnvironmentConfig" },
            "stage": { "$ref": "#/definitions/stackEnvironmentConfig" },
            "prod": { "$ref": "#/definitions/stackEnvironmentConfig" }
          },
          "description": "Per-environment stack configuration"
        }
      }
    },
    "stackEnvironmentConfig": {
      "type": "object",
      "properties": {
        "enabled": {
          "type": "boolean",
          "description": "Whether stack is enabled in this environment"
        },
        "config": {
          "type": "object",
          "description": "Environment-specific stack configuration"
        }
      }
    }
  }
}
```

---

## Deployment Metadata

### Deployment Object

The `deployment` object contains immutable metadata about the deployment:

```json
{
  "deployment": {
    "id": "D1BRV40",
    "org": "CompanyA",
    "project": "ecommerce",
    "template": "default",
    "createdAt": "2025-10-09T10:30:00Z",
    "updatedAt": "2025-10-09T14:25:00Z",
    "description": "E-commerce platform infrastructure",
    "tags": {
      "cost-center": "engineering",
      "team": "platform",
      "environment-type": "multi-tier"
    }
  }
}
```

### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique deployment ID (format: `D[A-Z0-9]{6}`) |
| `org` | string | Yes | Organization name (1-100 characters) |
| `project` | string | Yes | Project name (1-100 characters) |
| `template` | string | Yes | Template name (default, minimal, microservices, data-platform) |
| `createdAt` | string | Yes | ISO 8601 timestamp of creation |
| `updatedAt` | string | No | ISO 8601 timestamp of last update |
| `description` | string | No | Optional deployment description |
| `tags` | object | No | Custom key-value tags |

### Deployment ID Format

Deployment IDs follow the format: `D<base36-timestamp>`

- **Prefix**: `D` (for Deployment)
- **Length**: 7 characters (1 prefix + 6 alphanumeric)
- **Encoding**: Base36 (uppercase)
- **Example**: `D1BRV40`

Generation algorithm:
```typescript
function generateDeploymentId(): string {
  const timestamp = Date.now();
  const base36 = timestamp.toString(36).toUpperCase();
  return `D${base36.slice(-6).padStart(6, '0')}`;
}
```

---

## Environment Configuration

### Environment Object

Each environment (dev, stage, prod) has its own configuration:

```json
{
  "environments": {
    "dev": {
      "enabled": true,
      "account": "111111111111",
      "region": "us-east-1",
      "tags": {
        "Environment": "dev",
        "ManagedBy": "cloud-0.7"
      },
      "config": {
        "instanceType": "t3.micro",
        "minCapacity": 1,
        "maxCapacity": 3,
        "enableBackups": false,
        "logRetentionDays": 7
      }
    },
    "stage": {
      "enabled": false,
      "account": "222222222222",
      "region": "us-west-2",
      "tags": {
        "Environment": "stage",
        "ManagedBy": "cloud-0.7"
      },
      "config": {
        "instanceType": "t3.small",
        "minCapacity": 2,
        "maxCapacity": 5,
        "enableBackups": true,
        "logRetentionDays": 30
      }
    },
    "prod": {
      "enabled": false,
      "account": "333333333333",
      "region": "us-west-2",
      "tags": {
        "Environment": "prod",
        "ManagedBy": "cloud-0.7"
      },
      "config": {
        "instanceType": "t3.medium",
        "minCapacity": 3,
        "maxCapacity": 10,
        "enableBackups": true,
        "logRetentionDays": 90
      }
    }
  }
}
```

### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `enabled` | boolean | Yes | Whether environment is enabled for deployment |
| `account` | string | Yes | 12-digit AWS account ID |
| `region` | string | Yes | AWS region (e.g., us-east-1) |
| `tags` | object | No | Environment-specific resource tags |
| `config` | object | No | Environment-specific configuration overrides |

### Environment Lifecycle

1. **dev**: Always enabled by default, cannot be disabled
2. **stage**: Disabled by default, must be explicitly enabled
3. **prod**: Disabled by default, must be explicitly enabled

Enable environment command:
```bash
cloud enable-environment D1BRV40 stage
cloud enable-environment D1BRV40 prod
```

---

## Stack Configuration

### Stack Object

Each stack in the deployment has configuration at two levels:
1. **Global stack configuration** (applies to all environments)
2. **Per-environment configuration** (overrides global)

```json
{
  "stacks": {
    "network": {
      "enabled": true,
      "dependencies": [],
      "priority": 100,
      "config": {
        "vpcCidr": "10.0.0.0/16",
        "availabilityZones": 3,
        "enableNatGateway": true,
        "enableVpnGateway": false
      },
      "environments": {
        "dev": {
          "enabled": true,
          "config": {
            "availabilityZones": 2,
            "enableNatGateway": false
          }
        },
        "stage": {
          "enabled": true,
          "config": {
            "availabilityZones": 2
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
    },
    "security": {
      "enabled": true,
      "dependencies": ["network"],
      "priority": 90,
      "config": {
        "enableGuardDuty": true,
        "enableSecurityHub": false,
        "enableCloudTrail": true
      },
      "environments": {
        "dev": {
          "enabled": true,
          "config": {
            "enableGuardDuty": false,
            "enableSecurityHub": false
          }
        },
        "prod": {
          "enabled": true,
          "config": {
            "enableGuardDuty": true,
            "enableSecurityHub": true,
            "enableCloudTrail": true
          }
        }
      }
    },
    "database-rds": {
      "enabled": true,
      "dependencies": ["network", "security"],
      "priority": 70,
      "config": {
        "engine": "postgres",
        "engineVersion": "15.3",
        "instanceClass": "{{ENV:instanceType}}",
        "allocatedStorage": 100,
        "multiAz": false,
        "backupRetentionPeriod": 7
      },
      "environments": {
        "dev": {
          "enabled": true,
          "config": {
            "instanceClass": "db.t3.micro",
            "allocatedStorage": 20,
            "multiAz": false
          }
        },
        "prod": {
          "enabled": true,
          "config": {
            "instanceClass": "db.r5.large",
            "allocatedStorage": 500,
            "multiAz": true,
            "backupRetentionPeriod": 30
          }
        }
      }
    }
  }
}
```

### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `enabled` | boolean | Yes | Whether stack is enabled globally |
| `dependencies` | array | Yes | List of stack dependencies (from template) |
| `priority` | number | No | Stack priority (0-100, higher = earlier) |
| `config` | object | No | Global stack configuration |
| `environments` | object | No | Per-environment stack configuration |

### Configuration Inheritance

Configuration values are resolved in this order (last wins):

1. **Template defaults** (from stack template)
2. **Global stack config** (from `stacks.<name>.config`)
3. **Environment overrides** (from `environments.<env>.config`)
4. **Stack environment config** (from `stacks.<name>.environments.<env>.config`)
5. **Runtime resolution** (placeholder values resolved at deployment time)

Example:
```json
// Template default: instanceType = "t3.small"
// Global stack config: instanceType = "t3.medium"
// Environment override: instanceType = "t3.large"
// Stack environment config: instanceType = "t3.xlarge"
// → Final value: "t3.xlarge"
```

---

## Runtime Placeholders

### Placeholder Syntax

Runtime placeholders allow dynamic value resolution at deployment time:

```
{{TYPE:source:key}}
```

### Supported Placeholder Types

#### 1. ENV (Environment Configuration)

Reference environment-level configuration:

```json
{
  "config": {
    "instanceType": "{{ENV:instanceType}}"
  }
}
```

Resolves to: `environments.<env>.config.instanceType`

#### 2. RUNTIME (Cross-Stack Dependencies)

Reference outputs from other stacks:

```json
{
  "config": {
    "vpcId": "{{RUNTIME:network:vpcId}}",
    "securityGroupId": "{{RUNTIME:security:webSecurityGroupId}}"
  }
}
```

Resolves to: Output from `network` or `security` stack

#### 3. AWS (AWS API Queries)

Query AWS resources at runtime:

```json
{
  "config": {
    "hostedZoneId": "{{AWS:route53:hostedZone:example.com}}",
    "certificateArn": "{{AWS:acm:certificate:*.example.com}}"
  }
}
```

Resolves to: Result of AWS API call

#### 4. SECRET (AWS Secrets Manager)

Retrieve secrets from AWS Secrets Manager:

```json
{
  "config": {
    "dbPassword": "{{SECRET:database/prod/password}}",
    "apiKey": "{{SECRET:third-party/api-key}}"
  }
}
```

Resolves to: Secret value from Secrets Manager

### Placeholder Resolution Order

1. **ENV placeholders**: Resolved first (no dependencies)
2. **AWS placeholders**: Resolved second (requires AWS access)
3. **SECRET placeholders**: Resolved third (requires AWS access)
4. **RUNTIME placeholders**: Resolved last (requires stack outputs)

### DependencyResolver Integration

The `DependencyResolver` utility handles runtime placeholder resolution:

```typescript
import { DependencyResolver } from '../../../cloud/tools/utils/dependency-resolver';

const resolver = new DependencyResolver(deploymentId, environment);

// Get value with automatic runtime resolution
const vpcId = resolver.get('network', 'vpcId');
const securityGroupId = resolver.get('security', 'webSecurityGroupId');
```

---

## Validation Rules

### Manifest Validation

The manifest must pass validation before deployment:

```bash
cloud validate D1BRV40
```

### Validation Checks

#### 1. Schema Validation
- JSON syntax is valid
- All required fields are present
- Field types match schema
- Field values match constraints (patterns, enums, ranges)

#### 2. Deployment Metadata Validation
- Deployment ID matches format `D[A-Z0-9]{6}`
- Organization and project names are non-empty
- Template name is valid (default, minimal, microservices, data-platform)
- Timestamps are valid ISO 8601 format

#### 3. Environment Validation
- At least `dev` environment is present
- All environment AWS account IDs are 12 digits
- All environment regions are valid AWS regions
- Dev environment is always enabled

#### 4. Stack Validation
- All stacks in template are present
- All dependencies exist in the deployment
- No circular dependencies exist
- Stack priorities are valid (0-100)

#### 5. Configuration Validation
- All placeholders use valid syntax
- All RUNTIME placeholders reference existing stacks
- All ENV placeholders reference existing environment config
- No infinite placeholder loops

#### 6. Cross-Stack Dependency Validation
- Dependencies form a valid DAG (Directed Acyclic Graph)
- All referenced stacks exist
- Dependency chains are resolvable

### Validation Output

```json
{
  "valid": true,
  "errors": [],
  "warnings": [
    "Stack 'monitoring' is disabled in prod environment",
    "Stack 'compute-lambda' has no dependencies (intentional?)"
  ],
  "info": {
    "totalStacks": 12,
    "enabledStacks": 11,
    "environments": ["dev", "stage", "prod"],
    "dependencyLayers": 5
  }
}
```

---

## Example Manifests

### Example 1: Minimal Template

```json
{
  "deployment": {
    "id": "DMIN001",
    "org": "StartupCo",
    "project": "mvp",
    "template": "minimal",
    "createdAt": "2025-10-09T10:00:00Z"
  },
  "environments": {
    "dev": {
      "enabled": true,
      "account": "111111111111",
      "region": "us-east-1",
      "tags": {
        "Environment": "dev"
      },
      "config": {
        "instanceType": "t3.micro"
      }
    },
    "stage": {
      "enabled": false,
      "account": "222222222222",
      "region": "us-west-2"
    },
    "prod": {
      "enabled": false,
      "account": "333333333333",
      "region": "us-west-2"
    }
  },
  "stacks": {
    "network": {
      "enabled": true,
      "dependencies": [],
      "config": {
        "vpcCidr": "10.0.0.0/16",
        "availabilityZones": 2
      }
    },
    "compute-ec2": {
      "enabled": true,
      "dependencies": ["network"],
      "config": {
        "instanceType": "{{ENV:instanceType}}",
        "vpcId": "{{RUNTIME:network:vpcId}}"
      }
    }
  }
}
```

### Example 2: Default Template

```json
{
  "deployment": {
    "id": "D1BRV40",
    "org": "CompanyA",
    "project": "ecommerce",
    "template": "default",
    "createdAt": "2025-10-09T10:30:00Z",
    "description": "E-commerce platform"
  },
  "environments": {
    "dev": {
      "enabled": true,
      "account": "111111111111",
      "region": "us-east-1",
      "config": {
        "instanceType": "t3.micro",
        "enableBackups": false
      }
    },
    "stage": {
      "enabled": false,
      "account": "222222222222",
      "region": "us-west-2",
      "config": {
        "instanceType": "t3.small",
        "enableBackups": true
      }
    },
    "prod": {
      "enabled": false,
      "account": "333333333333",
      "region": "us-west-2",
      "config": {
        "instanceType": "t3.medium",
        "enableBackups": true
      }
    }
  },
  "stacks": {
    "network": {
      "enabled": true,
      "dependencies": [],
      "priority": 100,
      "config": {
        "vpcCidr": "10.0.0.0/16",
        "availabilityZones": 3
      }
    },
    "dns": {
      "enabled": true,
      "dependencies": ["network"],
      "priority": 95,
      "config": {
        "domainName": "example.com"
      }
    },
    "security": {
      "enabled": true,
      "dependencies": ["network"],
      "priority": 90,
      "config": {
        "vpcId": "{{RUNTIME:network:vpcId}}"
      }
    },
    "database-rds": {
      "enabled": true,
      "dependencies": ["network", "security"],
      "priority": 70,
      "config": {
        "engine": "postgres",
        "instanceClass": "{{ENV:instanceType}}",
        "vpcId": "{{RUNTIME:network:vpcId}}",
        "securityGroupId": "{{RUNTIME:security:databaseSecurityGroupId}}"
      }
    },
    "compute-ec2": {
      "enabled": true,
      "dependencies": ["network", "security", "database-rds"],
      "priority": 50,
      "config": {
        "instanceType": "{{ENV:instanceType}}",
        "vpcId": "{{RUNTIME:network:vpcId}}",
        "securityGroupId": "{{RUNTIME:security:webSecurityGroupId}}",
        "dbEndpoint": "{{RUNTIME:database-rds:endpoint}}"
      }
    }
  }
}
```

### Example 3: Microservices Template

```json
{
  "deployment": {
    "id": "DMICRO1",
    "org": "TechCorp",
    "project": "services",
    "template": "microservices",
    "createdAt": "2025-10-09T11:00:00Z"
  },
  "environments": {
    "dev": {
      "enabled": true,
      "account": "111111111111",
      "region": "us-east-1",
      "config": {
        "ecsTaskCpu": "256",
        "ecsTaskMemory": "512",
        "minCapacity": 1,
        "maxCapacity": 3
      }
    },
    "prod": {
      "enabled": false,
      "account": "333333333333",
      "region": "us-west-2",
      "config": {
        "ecsTaskCpu": "1024",
        "ecsTaskMemory": "2048",
        "minCapacity": 3,
        "maxCapacity": 10
      }
    }
  },
  "stacks": {
    "network": {
      "enabled": true,
      "dependencies": []
    },
    "containers-images": {
      "enabled": true,
      "dependencies": []
    },
    "containers-apps": {
      "enabled": true,
      "dependencies": ["network", "containers-images"],
      "config": {
        "services": [
          {
            "name": "api",
            "image": "{{RUNTIME:containers-images:apiImageUri}}",
            "cpu": "{{ENV:ecsTaskCpu}}",
            "memory": "{{ENV:ecsTaskMemory}}"
          },
          {
            "name": "worker",
            "image": "{{RUNTIME:containers-images:workerImageUri}}",
            "cpu": "{{ENV:ecsTaskCpu}}",
            "memory": "{{ENV:ecsTaskMemory}}"
          }
        ]
      }
    }
  }
}
```

---

## Migration from 2.3

### Changes from v2.3

1. **File Location**:
   - v2.3: `./aws/deploy/<deployment-id>/manifest.json`
   - v3.0: `./cloud/deploy/<deployment-id>/manifest.json`

2. **Environment Naming**:
   - v2.3: `staging`
   - v3.0: `stage`

3. **Stack Naming**:
   - v2.3: `<org>/<stack>/<env>` (e.g., "myorg/network/dev")
   - v3.0: `<deployment-id>-<environment>` (e.g., "D1BRV40-dev")

4. **Template Dependencies**:
   - v2.3: Dependencies in stack code
   - v3.0: Dependencies in manifest (from template)

5. **Runtime Placeholders**:
   - v2.3: Not supported
   - v3.0: Full support for ENV, RUNTIME, AWS, SECRET

### Migration Script

```bash
# Migrate manifest from 2.3 to 3.0
cloud migrate-manifest <deployment-id>

# Manual migration steps:
# 1. Move file from ./aws/deploy/ to ./cloud/deploy/
# 2. Rename "staging" to "stage" throughout
# 3. Add dependencies array to each stack (from template)
# 4. Update placeholder syntax if needed
# 5. Validate migrated manifest
```

### Validation After Migration

```bash
cloud validate D1BRV40
```

---

## Conclusion

The Deployment Manifest is the cornerstone of Cloud Architecture v3.0, providing a unified configuration format for all deployments across all environments. Key features include:

- **Single Source of Truth**: One file per deployment
- **Multi-Environment Support**: Dev, stage, prod in one file
- **Runtime Placeholders**: Dynamic value resolution
- **Template-Based**: Generated from deployment templates
- **Validation**: Comprehensive validation before deployment

For implementation details, see:
- Main Architecture Document (Multi-Stack-Architecture-3.0.md)
- CLI Commands Reference (CLI_Commands_Reference.3.0.md)
- Platform Code Addendum (Addendum_Platform_Code.3.0.md)
