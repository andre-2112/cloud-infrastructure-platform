# Pulumi Stack Naming Discrepancy - Addendum v4.1

**Version:** 4.1
**Date:** 2025-10-30
**Status:** Implementation Discrepancy Identified
**Severity:** Medium - Affects stack organization in Pulumi Cloud

---

## Summary

A discrepancy exists between the documented Pulumi stack naming convention in `Multi_Stack_Architecture.4.1.md` and the implementation in `deploy_stack_cmd.py` and `destroy_stack_cmd.py`.

---

## Architecture Documentation (Correct Specification)

**Source:** `Multi_Stack_Architecture.4.1.md`, lines 2861-2888

### Pulumi Stack Naming Convention

**Format:** `<deployment-id>-<stack-name>-<environment>`

**Full Pulumi Cloud Path:** `{pulumiOrg}/{project}/{stack-name}`

Where:
- `{pulumiOrg}` = Pulumi Cloud organization (from `pulumiOrg` field in manifest)
- `{project}` = **Deployment project name** (from `project` field in manifest)
- `{stack-name}` = `{deployment-id}-{stack-name}-{environment}`

### Documentation Example

```
Pulumi Organization: CompanyA
└── Project: ecommerce  # Business project
    ├── Stack: D1BRV40-network-dev
    ├── Stack: D1BRV40-network-stage
    ├── Stack: D1BRV40-network-prod
    ├── Stack: D1BRV40-security-dev
    ├── Stack: D1BRV40-security-stage
    └── ... (all stacks for this deployment)
```

**Full path example:** `CompanyA/ecommerce/D1BRV40-network-dev`

- Pulumi Organization = "CompanyA" (from manifest `pulumiOrg`)
- Pulumi Project = "ecommerce" (from manifest `project` field)
- Pulumi Stack = "D1BRV40-network-dev"

### Design Intent

All stacks for a given **deployment** (business project like "ecommerce") should be organized under **one Pulumi project** named after the business project. This allows:

1. **Logical grouping** - All infrastructure for "ecommerce" project grouped together
2. **Easy discovery** - Navigate Pulumi Cloud: CompanyA → ecommerce → see all stacks
3. **Access control** - Grant permissions at project level for all related stacks
4. **Deployment isolation** - Different deployments (e.g., "mobile-app") use different Pulumi projects

---

## Current Implementation Status

### ✓ Correct Implementation: `deploy_cmd.py` (Full Orchestration)

**File:** `cloud/tools/cli/src/cloud_cli/commands/deploy_cmd.py`, line 181

```python
# Initialize Pulumi
# Use pulumiOrg (Pulumi Cloud organization), NOT organization (deployment org)
pulumi_org = manifest.get("pulumiOrg", manifest.get("organization", ""))
project = manifest.get("project", deployment_id)  # ✓ CORRECT
pulumi_wrapper = PulumiWrapper(organization=pulumi_org, project=project)
```

**Result:** `andre-2112/live-test-6/DX6604E-network-dev` ✓

### ✗ Incorrect Implementation: `deploy_stack_cmd.py` (Individual Stack)

**File:** `cloud/tools/cli/src/cloud_cli/commands/deploy_stack_cmd.py`, lines 96-99

```python
# Get Pulumi organization and project from manifest
pulumi_org = manifest.get("pulumiOrg", manifest.get("organization", ""))
project = stack_name  # Use stack name as project for Pulumi  # ✗ WRONG!

pulumi_wrapper = PulumiWrapper(organization=pulumi_org, project=project)
```

**Result:** `andre-2112/network/DX6604E-network-dev` ✗

**Issue:** Uses **stack name** ("network") as Pulumi project instead of **deployment project** ("live-test-6")

### ✗ Incorrect Implementation: `destroy_stack_cmd.py` (Individual Stack)

**File:** `cloud/tools/cli/src/cloud_cli/commands/destroy_stack_cmd.py`, lines 96-97

```python
pulumi_org = manifest.get("pulumiOrg", manifest.get("organization", ""))
project = stack_name  # Use stack name as project for Pulumi  # ✗ WRONG!
```

**Result:** `andre-2112/network/DX6604E-network-dev` ✗

**Same issue as deploy_stack_cmd.py**

---

## Impact Analysis

### Current Behavior

When using individual stack commands (`cloud deploy-stack`, `cloud destroy-stack`):

1. **Wrong Pulumi project used:**
   - Creates stacks under `andre-2112/network/` instead of `andre-2112/live-test-6/`
   - Each stack type gets its own Pulumi project (network, security, database-rds, etc.)

2. **Pulumi Cloud organization:**
   ```
   Pulumi Organization: andre-2112
   ├── Project: network
   │   ├── Stack: DX6604E-network-dev
   │   ├── Stack: DX4NGF1-network-dev
   │   └── Stack: DTEST03-network-dev
   ├── Project: security
   │   ├── Stack: DX6604E-security-dev
   │   └── ...
   ├── Project: database-rds
   │   └── ...
   └── Project: live-test-6  # ← Correct location, but empty!
       └── (no stacks when using deploy-stack!)
   ```

3. **Fragmentation:**
   - Stack for deployment "DX6604E" are scattered across multiple Pulumi projects
   - Cannot view all stacks for a deployment in one place
   - Confusing organization structure

### Expected Behavior (Per Architecture)

All stacks for a deployment should be under the same Pulumi project:

```
Pulumi Organization: andre-2112
└── Project: live-test-6  # Deployment project name
    ├── Stack: DX6604E-network-dev
    ├── Stack: DX6604E-security-dev
    ├── Stack: DX6604E-database-rds-dev
    └── ... (all stacks for DX6604E)
```

---

## Why This Discrepancy Exists

### Hypothesized Reasoning (Incorrect)

The comment in deploy_stack_cmd.py suggests a misunderstanding:

```python
# Use stack name as project for Pulumi
```

This might have been done to:
1. Avoid conflicts between different stack types
2. Match Pulumi project to TypeScript project name (e.g., network → network/)
3. Simplify per-stack Pulumi.yaml configuration

However, this contradicts the architecture specification.

### Architectural Intent (Correct)

From Multi_Stack_Architecture.4.1.md line 2881:
- Pulumi **project** = Business project / Deployment name
- Pulumi **stack** = Deployment ID + Stack name + Environment

This separates concerns:
- **Project level:** Deployment/business domain
- **Stack level:** Individual infrastructure component + environment

---

## Recommended Fix

### Update deploy_stack_cmd.py

**Line 98 - Change:**
```python
# BEFORE (wrong)
project = stack_name  # Use stack name as project for Pulumi

# AFTER (correct)
project = manifest.get("project", deployment_id)  # Use deployment project name
```

### Update destroy_stack_cmd.py

**Line 97 - Change:**
```python
# BEFORE (wrong)
project = stack_name  # Use stack name as project for Pulumi

# AFTER (correct)
project = manifest.get("project", deployment_id)  # Use deployment project name
```

### Migration Considerations

**⚠️ Breaking Change Alert:**

Changing the Pulumi project will affect existing deployments that were created with individual stack commands:

1. **Existing stacks** are at: `andre-2112/network/DX6604E-network-dev`
2. **After fix** they should be at: `andre-2112/live-test-6/DX6604E-network-dev`

**Migration Options:**

**Option 1: Manual Migration (Recommended for Live Deployments)**
```bash
# For each existing stack
pulumi stack export --stack andre-2112/network/DX6604E-network-dev > stack-export.json
pulumi stack init andre-2112/live-test-6/DX6604E-network-dev
pulumi stack import --stack andre-2112/live-test-6/DX6604E-network-dev < stack-export.json
pulumi stack rm andre-2112/network/DX6604E-network-dev --yes
```

**Option 2: Fresh Deployments (Acceptable for Testing)**
- Destroy all test deployments created with old naming
- Redeploy with fixed naming convention
- No migration needed

**Option 3: Leave Existing, Fix Going Forward**
- Keep existing stacks in old location
- Fix code for new deployments only
- Accept mixed organization (not ideal but pragmatic)

---

## Implementation Verification

### Verify Pulumi Project Name in Stack

**Check existing stack location:**
```bash
cd cloud/stacks/network
pulumi stack ls
```

**Expected after fix:**
```
NAME                                      LAST UPDATE     RESOURCE COUNT  URL
andre-2112/live-test-6/DX6604E-network-dev  5 minutes ago   32             https://app.pulumi.com/...
```

**Not:**
```
andre-2112/network/DX6604E-network-dev  # ✗ Old/wrong
```

---

## Cross-References

### Code Locations

| File | Line | Status | Project Value |
|------|------|--------|---------------|
| `deploy_cmd.py` | 181 | ✓ Correct | `manifest.get("project", deployment_id)` |
| `deploy_stack_cmd.py` | 98 | ✗ Wrong | `stack_name` |
| `destroy_stack_cmd.py` | 97 | ✗ Wrong | `stack_name` |
| `destroy_cmd.py` | 105 | ✓ Correct | `manifest.get("project", deployment_id)` |

### Documentation References

- **Architecture:** `Multi_Stack_Architecture.4.1.md`, lines 2861-2888
- **Stack Code:** `cloud/stacks/network/index.ts`, line 560-561 (shows full path format)
- **Implementation:** `cloud/tools/core/cloud_core/pulumi/pulumi_wrapper.py`, line 120

---

## Resolution Status

**Status:** Identified, not yet fixed
**Priority:** Medium
**Recommendation:** Fix in next maintenance window, with appropriate migration plan

---

## Version History

- **v4.1 (2025-10-30):** Initial identification of discrepancy
