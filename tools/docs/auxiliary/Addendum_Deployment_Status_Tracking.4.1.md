# Deployment Status Tracking - Addendum v4.1

**Version:** 4.1
**Date:** 2025-10-30
**Status:** Implementation Detail Clarification

---

## Purpose

This addendum clarifies the distinction between **deployment-level status** and **stack-level status** in the platform, addressing common confusion when using individual stack deployment commands versus full deployment orchestration.

---

## Status Hierarchy

The platform tracks status at two distinct levels:

### 1. Deployment-Level Status

**Location:** `.deployment-metadata.yaml` → `status` field

**Represents:** Overall state of the entire deployment

**Values:**
- `initialized` - Deployment created, configuration generated
- `deploying` - Full orchestration in progress (`cloud deploy` command)
- `deployed` - Full deployment completed successfully via `cloud deploy`
- `partial` - Some stacks succeeded, some failed during full deployment
- `destroying` - Full destroy operation in progress
- `destroyed` - All stacks destroyed via `cloud destroy`
- `failed` - Full deployment operation failed
- `unknown` - Status cannot be determined

**Updated by:**
- `cloud init` → Sets to `initialized`
- `cloud deploy <deployment-id>` → Sets to `deploying` then `deployed`/`partial`/`failed`
- `cloud destroy <deployment-id>` → Sets to `destroying` then `destroyed`/`failed`

**NOT updated by:**
- `cloud deploy-stack` (individual stack deployment)
- `cloud destroy-stack` (individual stack destruction)

### 2. Stack-Level Status

**Location:** `.deployment-state.yaml` → `stacks.<stack-name>-<env>.status` field

**Represents:** State of individual stacks within the deployment

**Values:**
- `not_deployed` - Stack exists in manifest but not deployed
- `deploying` - Stack deployment in progress
- `deployed` - Stack successfully deployed
- `failed` - Stack deployment failed
- `destroying` - Stack destruction in progress
- `destroyed` - Stack successfully destroyed

**Updated by:**
- `cloud deploy-stack <deployment-id> <stack-name>` → Updates individual stack status
- `cloud destroy-stack <deployment-id> <stack-name>` → Updates individual stack status
- `cloud deploy <deployment-id>` → Updates all enabled stack statuses
- `cloud destroy <deployment-id>` → Updates all stack statuses

---

## Status Display Behavior

### `cloud list` Command

Shows **deployment-level status** from `.deployment-metadata.yaml`:

```
Deployments
+-------------------------------------------------------------------------+
| Deployment ID | Organization | Project     | Status      | Created    |
|---------------+--------------+-------------+-------------+------------|
| DX6604E       | LiveTestOrg  | live-test-6 | initialized | 2025-10-30 |
| DX4NGF1       | LiveTestOrg  | live-test-4 | initialized | 2025-10-30 |
| DTEST03       | DemoOrg      | demo-v41    | deployed    | 2025-10-29 |
+-------------------------------------------------------------------------+
```

### `cloud status <deployment-id>` Command

Shows **stack-level status** from `.deployment-state.yaml`:

```
Deployment: DX6604E
Status: initialized  ← Deployment-level status

Stack Status
+--------------------------------------------+
| Stack    | Status       | Enabled |
|----------+--------------+---------|
| network  | deployed     | Yes     |  ← Stack-level status
| security | not_deployed | No      |
+--------------------------------------------+
```

---

## Common Scenarios

### Scenario 1: Individual Stack Deployment

```bash
cloud init --org MyOrg --project my-app --domain myapp.com --account-dev 123456
# Deployment status: initialized

cloud deploy-stack DX6604E network --environment dev
# Deployment status: STILL initialized (unchanged)
# Stack status: deployed

cloud list
# Shows: DX6604E | initialized  ← Not "deployed"!
```

**Why?** Individual stack commands (`deploy-stack`, `destroy-stack`) only update **stack-level status**, not **deployment-level status**.

### Scenario 2: Full Deployment Orchestration

```bash
cloud init --org MyOrg --project my-app --domain myapp.com --account-dev 123456
# Deployment status: initialized

cloud deploy DX6604E --environment dev
# Deployment status: deploying → deployed (on success)
# All enabled stack statuses: deployed

cloud list
# Shows: DX6604E | deployed  ← Correctly shows "deployed"
```

**Why?** The `cloud deploy` command orchestrates all enabled stacks and updates both **deployment-level** and **stack-level** statuses.

### Scenario 3: Partial Deployment

```bash
cloud deploy DX6604E --environment dev
# network stack: deployed
# security stack: failed
# Deployment status: partial  ← Indicates mixed results
```

---

## Design Rationale

### Why Two Status Levels?

1. **Operational Distinction:**
   - Deployment status tracks **orchestrated operations** that process all enabled stacks
   - Stack status tracks **individual stack state** regardless of how it was deployed

2. **Audit Trail:**
   - Deployment status indicates whether the deployment has undergone full orchestration
   - Stack status shows actual infrastructure state per stack

3. **Workflow Clarity:**
   - `initialized` = "I created this deployment but haven't run full orchestration yet"
   - `deployed` = "I ran full deployment orchestration and it completed"
   - Individual stack deployment is considered **ad-hoc manual operation**, not full deployment

### Why Keep Deployment Status as "initialized"?

When using `cloud deploy-stack`, the deployment status remains `initialized` because:

1. **No orchestration occurred** - Stacks were deployed manually, not via orchestrated plan
2. **Dependency order unknown** - Individual deployment doesn't validate/respect dependencies
3. **Incomplete deployment** - Only some stacks may be deployed, not the full manifest
4. **Manual intervention** - Indicates the deployment requires manual management

---

## Recommendations

### For Production Deployments

**Use full orchestration:**
```bash
cloud deploy <deployment-id> --environment prod
```

This ensures:
- Correct dependency order
- Proper validation
- Complete deployment
- Accurate status tracking

### For Development/Testing

**Individual stack deployment is acceptable:**
```bash
cloud deploy-stack <deployment-id> <stack-name> --environment dev
```

But understand:
- Deployment status stays "initialized"
- You're responsible for dependency order
- `cloud status` shows actual stack states

### Status Interpretation

- **Deployment status = "initialized"** → Check `cloud status` to see what's actually deployed
- **Deployment status = "deployed"** → Full orchestration completed successfully
- **Deployment status = "partial"** → Some stacks failed, check logs
- **Stack status = "deployed"** → That specific stack is deployed and healthy

---

## File Structure Reference

### .deployment-metadata.yaml
```yaml
created_at: '2025-10-30T00:46:48.258878Z'
deployment_id: DX6604E
organization: LiveTestOrg
project: live-test-6
status: initialized  ← Deployment-level status
template: default
```

### .deployment-state.yaml
```yaml
current_operation: null
deployment_status: initialized  ← Also stored here for state tracking
last_updated: '2025-10-30T00:50:57.262933Z'
stacks:
  network-dev:
    environment: dev
    last_updated: '2025-10-30T00:50:57.262921Z'
    stack_name: network
    status: deployed  ← Stack-level status
  security-dev:
    environment: dev
    last_updated: '2025-10-30T00:45:00.000000Z'
    stack_name: security
    status: not_deployed  ← Stack-level status
```

---

## Related Commands

| Command | Updates Deployment Status | Updates Stack Status |
|---------|---------------------------|----------------------|
| `cloud init` | ✓ (initialized) | ✗ |
| `cloud deploy <id>` | ✓ (deploying→deployed/partial/failed) | ✓ (all enabled stacks) |
| `cloud deploy-stack <id> <stack>` | ✗ | ✓ (specific stack) |
| `cloud destroy <id>` | ✓ (destroying→destroyed/failed) | ✓ (all stacks) |
| `cloud destroy-stack <id> <stack>` | ✗ | ✓ (specific stack) |
| `cloud list` | Displays | ✗ |
| `cloud status <id>` | Displays | Displays |

---

## Version History

- **v4.1 (2025-10-30):** Initial documentation of status tracking behavior
