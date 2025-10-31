# Architecture v4.6: Composite Project Naming Scheme

**Version:** 4.6
**Date:** January 2025
**Status:** Authoritative

---

## Overview

Architecture version 4.6 introduces a **composite project naming scheme** that provides complete deployment isolation in Pulumi Cloud while maintaining clear separation between business organizations and Pulumi infrastructure.

This architectural enhancement builds upon v4.5's dynamic Pulumi.yaml management and extends it to create globally unique, deployment-specific project identifiers.

---

## What Changed in v4.6

### Composite Project Name Format

**Format:** `{DeploymentID}-{Organization}-{Project}`

**Example:** `DT28749-TestOrg-demo-test`

**Components:**
- `DeploymentID`: Unique identifier for this deployment instance (e.g., `DT28749`)
- `Organization`: Business organization name (e.g., `TestOrg`)
- `Project`: Project name (e.g., `demo-test`)

### Where Composite Naming is Applied

1. **Pulumi Cloud Project Names**
   - Full stack path: `{pulumiOrg}/{composite-project}/{stack-name}-{environment}`
   - Example: `andre-2112/DT28749-TestOrg-demo-test/network-dev`

2. **Configuration File Key Prefixes**
   - Format: `{composite-project}:{key}: "{value}"`
   - Example: `DT28749-TestOrg-demo-test:vpc_cidr: "10.0.0.0/16"`

3. **Generated Pulumi.yaml Files**
   - The `name:` field uses the composite project name
   - Example: `name: DT28749-TestOrg-demo-test`

---

## Benefits and Rationale

### Complete Deployment Isolation

Each deployment gets a unique Pulumi Cloud project namespace, preventing conflicts when:
- Multiple teams deploy the same template
- Same organization has multiple environments
- Testing/development instances run in parallel

**Example Scenario:**
```
TeamA deploys:  andre-2112/DT28749-TeamA-platform/network-dev
TeamB deploys:  andre-2112/DT28750-TeamB-platform/network-dev
```

Both teams can work independently without stack naming conflicts.

### Organization vs Pulumi Organization Clarity

The composite scheme clearly separates:
- **Business Organization** (`TestOrg`): Your company/team name
- **Pulumi Organization** (`andre-2112`): Infrastructure provider org

This eliminates confusion about which "organization" is being referenced in configuration.

### Simplified Cleanup and Management

Deleting a deployment becomes straightforward:
1. Identify all stacks by composite project name prefix
2. Destroy stacks in dependency order
3. Remove Pulumi Cloud project
4. Delete deployment directory

**Example:**
```bash
# All stacks for deployment DT28749 are under:
andre-2112/DT28749-TestOrg-demo-test/*
```

### Consistent Naming Across All Artifacts

The same composite name appears in:
- Pulumi Cloud project
- Stack configuration files
- Deployment directory names
- Pulumi.yaml files

This consistency reduces cognitive load and makes debugging easier.

---

## Technical Implementation

### ConfigGenerator (config_generator.py)

**Lines 98-108:** Composite project name generation and usage

```python
# Build composite project name: DeploymentID-Organization-Project
deployment_id = manifest.get("deployment_id", "")
organization = manifest.get("organization", "")
project = manifest.get("project", "")
composite_project = f"{deployment_id}-{organization}-{project}"

with open(config_file, "w", encoding="utf-8") as f:
    # Write deployment metadata
    f.write(f'{composite_project}:deploymentId: "{deployment_id}"\n')
    f.write(f'{composite_project}:organization: "{organization}"\n')
    f.write(f'{composite_project}:project: "{project}"\n')
```

**Lines 267-290:** UpdateStackConfig also uses composite naming

All configuration keys are prefixed with the composite project name.

### PulumiWrapper (pulumi_wrapper.py)

**Lines 444-485:** `_generate_pulumi_yaml()` method

```python
def _generate_pulumi_yaml(self, stack_dir: Path, manifest: Dict[str, Any],
                         deployment_dir: Optional[Path] = None) -> None:
    # Build composite project name: DeploymentID-Organization-Project
    deployment_id = manifest.get("deployment_id", "")
    organization = manifest.get("organization", "")
    project = manifest.get("project", "")
    composite_project = f"{deployment_id}-{organization}-{project}"

    # Generate new content with deployment project name
    new_content = {
        'name': composite_project,  # Use composite project name
        'runtime': original_content.get('runtime', 'nodejs'),
        'description': original_content.get('description',
                       f'Deployment {composite_project} stack'),
    }
```

**Lines 487-520:** `deployment_context()` context manager

Ensures all Pulumi operations use the composite project name by temporarily replacing Pulumi.yaml.

### DeploymentOrchestrator (deploy_cmd.py)

**Lines 96-97:** Passes manifest to deployment_context

```python
# Use deployment context with manifest for composite naming
with pulumi_wrapper.deployment_context(stack_dir, manifest, deployment_dir):
```

### StackOperations (stack_operations.py)

**Lines 57, 310:** Stack name format (no deployment_id prefix)

Stack names remain simple: `{stack-name}-{environment}`

The deployment isolation comes from the composite project name, not the stack name.

---

## Configuration File Format Changes

### Before v4.6 (Stack Name Prefix)

```yaml
network:deploymentId: "DT28749"
network:organization: "TestOrg"
network:project: "demo-test"
network:vpc_cidr: "10.0.0.0/16"
aws:region: "us-east-1"
```

### After v4.6 (Composite Project Prefix)

```yaml
DT28749-TestOrg-demo-test:deploymentId: "DT28749"
DT28749-TestOrg-demo-test:organization: "TestOrg"
DT28749-TestOrg-demo-test:project: "demo-test"
DT28749-TestOrg-demo-test:vpc_cidr: "10.0.0.0/16"
aws:region: "us-east-1"
```

**Key Difference:** Configuration keys now use the full composite project name as prefix instead of just the stack name.

---

## Pulumi Cloud Structure

### Stack Naming Pattern

```
{pulumiOrg}/{composite-project}/{stack-name}-{environment}
```

### Example Deployment

**Manifest Values:**
- deployment_id: `DT28749`
- organization: `TestOrg`
- project: `demo-test`
- pulumiOrg: `andre-2112`

**Resulting Stacks:**
```
andre-2112/DT28749-TestOrg-demo-test/network-dev
andre-2112/DT28749-TestOrg-demo-test/compute-dev
andre-2112/DT28749-TestOrg-demo-test/storage-dev
```

---

## Migration from v4.5 to v4.6

### Existing Deployments

Deployments created with v4.5 used stack name prefixes in configuration files. These will continue to work but won't benefit from deployment isolation in Pulumi Cloud.

### New Deployments

All new deployments automatically use the composite naming scheme. No special configuration required.

### Upgrading Existing Deployments

To upgrade an existing deployment:

1. **Backup Configuration**
   ```bash
   cp -r deploy/<deployment-id>/ deploy/<deployment-id>.backup/
   ```

2. **Regenerate Configurations**
   ```bash
   cd deploy/<deployment-id>
   # Re-run config generation (automatic during deploy)
   ```

3. **Update Pulumi Cloud Project**
   - This happens automatically through deployment_context
   - Old stacks will be preserved
   - New operations use composite project name

### Breaking Changes

**None.** The v4.6 changes are backward compatible. Stack selection still uses the original Pulumi organization and project passed to PulumiWrapper.

---

## Deployment Directory Structure

The deployment directory name uses a composite format:

```
deploy/
├── <deployment-id>-<organization>-<project>/
│   ├── deployment-manifest.yaml
│   ├── config/
│   │   ├── network.dev.yaml      # Uses composite prefix in keys
│   │   ├── compute.dev.yaml      # Uses composite prefix in keys
│   │   └── storage.dev.yaml      # Uses composite prefix in keys
│   ├── state/
│   └── logs/
```

**Example:**
```
deploy/
├── DT28749-TestOrg-demo-test/
│   ├── deployment-manifest.yaml
│   ├── config/
│   │   ├── network.dev.yaml
│   │   └── compute.dev.yaml
```

---

## Best Practices

### Deployment ID Naming

Choose short, unique deployment IDs:
- Use prefixes: `DT` (demo/test), `PRD` (production), `STG` (staging)
- Include number: `DT28749`, `PRD00123`
- Keep under 10 characters for readability

### Organization Naming

- Use your company/team name
- Avoid special characters
- Keep concise: `Acme`, `TeamAlpha`, `EngOps`

### Project Naming

- Describe the deployment purpose
- Use kebab-case: `platform-core`, `ml-pipeline`
- Be specific enough to identify in Pulumi Cloud

### Example Composite Names

```
Good Examples:
- DT28749-Acme-platform
- PRD00123-EngOps-ml-pipeline
- STG99-TeamA-web-app

Bad Examples:
- deployment-123-my-org-project-name-with-many-words (too long)
- DT-TestOrg-test (deployment ID too short)
- DT28749-Test-Org-demo (spaces/dashes in org name)
```

---

## Testing and Validation

### Verify Composite Naming

After deploying, check Pulumi Cloud:

```bash
pulumi stack ls
```

Expected output:
```
NAME                                          LAST UPDATE    RESOURCE COUNT  URL
andre-2112/DT28749-TestOrg-demo-test/network-dev  2 minutes ago  15       https://app.pulumi.com/...
```

### Verify Configuration Format

Check generated config files:

```bash
cat deploy/DT28749-TestOrg-demo-test/config/network.dev.yaml
```

Expected format:
```yaml
DT28749-TestOrg-demo-test:deploymentId: "DT28749"
DT28749-TestOrg-demo-test:organization: "TestOrg"
...
```

### Verify Pulumi.yaml Generation

During deployment, check stack directory:

```bash
cat stacks/network/Pulumi.yaml
```

Expected content:
```yaml
name: DT28749-TestOrg-demo-test
runtime: nodejs
description: Deployment DT28749-TestOrg-demo-test stack
```

Note: This file is temporary and restored after deployment.

---

## Relationship to v4.5 Features

### Dynamic Pulumi.yaml Management (v4.5)

v4.6 builds directly on v4.5's `deployment_context()` context manager:
- v4.5: Introduced temporary Pulumi.yaml generation
- v4.6: Uses composite naming in generated Pulumi.yaml

### Disabled-by-Default Stacks (v4.5)

Composite naming works seamlessly with disabled-by-default:
- Only enabled stacks get composite-named projects
- Disabled stacks are skipped in deployment
- No orphaned Pulumi Cloud projects

### Template-First Validation (v4.0+)

Composite naming enhances validation:
- Template code validated before deployment
- Each deployment instance isolated
- No cross-deployment interference during validation

---

## Future Enhancements

### Potential v4.7 Features

1. **Automatic Cleanup Commands**
   - `cloud cleanup-deployment <deployment-id>`
   - Removes all stacks with matching composite project

2. **Deployment List View**
   - `cloud list-deployments`
   - Groups stacks by composite project

3. **Cross-Deployment Dependencies**
   - Reference outputs from other deployments
   - Use composite project name as identifier

---

## See Also

- **Multi_Stack_Architecture.4.6.md** - Complete architecture overview
- **Deployment_Manifest_Specification.4.6.md** - Manifest format details
- **Directory_Structure_Diagram.4.6.md** - File structure with composite naming
- **INSTALL.md** - Installation and upgrade instructions

---

## Document History

- **v4.6** (January 2025): Initial documentation of composite naming scheme
