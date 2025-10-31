# Dynamic Pulumi.yaml Implementation - Addendum v4.1

**Version:** 4.1
**Date:** 2025-10-30
**Status:** Implementation Plan
**Priority:** High - Required for v4.1 Architecture Compliance

---

## Problem Statement

### The Fundamental Conflict

After implementing the v4.1 Pulumi stack naming convention as documented in `Multi_Stack_Architecture.4.1.md`, we discovered a fundamental incompatibility between the architecture's intent and Pulumi's design constraints:

**Architecture Specification (lines 2861-2888):**
```
Format: {pulumiOrg}/{project}/{deployment-id}-{stack-name}-{environment}
Example: andre-2112/live-test-1/DX8BBG5-network-dev

Where:
- {pulumiOrg} = Pulumi Cloud organization (from manifest pulumiOrg field)
- {project} = Deployment project name (from manifest project field)
- {stack-name} = deployment-id-stack-name-environment
```

**Pulumi's Requirement:**
Each Pulumi stack directory (e.g., `cloud/stacks/network/`) contains a `Pulumi.yaml` file with a hardcoded `name:` field. Pulumi validates that all stack operations use a project name matching this file.

**Current Conflict:**
```yaml
# cloud/stacks/network/Pulumi.yaml
name: network  # ← Fixed to "network"
```

When we try to create stack: `andre-2112/live-test-1/DX8BBG5-network-dev`
Pulumi rejects it: "provided project name 'live-test-1' doesn't match Pulumi.yaml"

### Why This Matters

**Architecture Intent:**
All stacks for a deployment should be grouped under **one Pulumi project** named after the business project:

```
Pulumi Organization: andre-2112
└── Project: ecommerce  # ← Single deployment project
    ├── Stack: D1BRV40-network-dev
    ├── Stack: D1BRV40-security-dev
    ├── Stack: D1BRV40-database-rds-dev
    └── ... (all stacks for this deployment together)
```

**Benefits:**
1. **Logical grouping** - All infrastructure for one project in one place
2. **Easy discovery** - Navigate Pulumi Cloud by business project
3. **Access control** - Grant permissions at project level
4. **Deployment isolation** - Different deployments use different Pulumi projects

**Without dynamic Pulumi.yaml (current broken state):**
```
Pulumi Organization: andre-2112
├── Project: network  # ← Scattered by stack type
│   ├── Stack: D1BRV40-network-dev
│   ├── Stack: D2ABC45-network-dev  # Different deployment!
│   └── Stack: D3XYZ78-network-dev  # Another deployment!
├── Project: security
│   ├── Stack: D1BRV40-security-dev
│   └── ...
└── Project: database-rds
    └── ...
```

This breaks the architectural goal of deployment isolation and logical grouping.

---

## Solution: Dynamic Pulumi.yaml Generation

### High-Level Approach

Generate a deployment-specific `Pulumi.yaml` at deployment time, placing it in the stack directory before running Pulumi commands. Each deployment gets its own Pulumi project configuration.

### Implementation Strategy

**Option 1: Temporary Pulumi.yaml (Chosen)**
- Keep original `Pulumi.yaml` as template
- Generate deployment-specific version during stack operations
- Restore original after operation
- Pros: Non-destructive, supports multiple concurrent deployments
- Cons: Requires careful cleanup, possible race conditions

**Option 2: Copy Stack Directory**
- Copy entire stack directory per deployment
- Modify Pulumi.yaml in copy
- Pros: True isolation, no conflicts
- Cons: Disk space, complexity, node_modules duplication

**Option 3: Symlinks + Separate Pulumi.yaml**
- Complex, OS-dependent, not chosen

**Decision: Use Option 1** - Temporary generation with proper locking and cleanup.

---

## Detailed Implementation Plan

### Phase 1: PulumiWrapper Enhancement

**File:** `cloud/tools/core/cloud_core/pulumi/pulumi_wrapper.py`

#### Changes Required:

1. **Add Pulumi.yaml Management Methods**

```python
def _backup_pulumi_yaml(self, stack_dir: Path) -> Optional[Path]:
    """
    Backup original Pulumi.yaml

    Args:
        stack_dir: Stack directory containing Pulumi.yaml

    Returns:
        Path to backup file, or None if no backup needed
    """
    pulumi_yaml = stack_dir / "Pulumi.yaml"
    if not pulumi_yaml.exists():
        return None

    backup_path = stack_dir / f"Pulumi.yaml.backup.{self.project}"
    shutil.copy2(pulumi_yaml, backup_path)
    logger.debug(f"Backed up Pulumi.yaml to {backup_path}")
    return backup_path

def _restore_pulumi_yaml(self, stack_dir: Path, backup_path: Optional[Path]) -> None:
    """
    Restore original Pulumi.yaml from backup

    Args:
        stack_dir: Stack directory
        backup_path: Path to backup file
    """
    if not backup_path or not backup_path.exists():
        return

    pulumi_yaml = stack_dir / "Pulumi.yaml"
    shutil.move(str(backup_path), str(pulumi_yaml))
    logger.debug(f"Restored Pulumi.yaml from backup")

def _generate_pulumi_yaml(self, stack_dir: Path, stack_name: str) -> None:
    """
    Generate deployment-specific Pulumi.yaml

    Args:
        stack_dir: Stack directory
        stack_name: Base stack name (e.g., "network")
    """
    pulumi_yaml = stack_dir / "Pulumi.yaml"

    # Read original to preserve runtime and description
    original_content = {}
    if pulumi_yaml.exists():
        import yaml
        with open(pulumi_yaml, 'r') as f:
            original_content = yaml.safe_load(f) or {}

    # Generate new content with deployment project name
    new_content = {
        'name': self.project,  # ← Use deployment project name
        'runtime': original_content.get('runtime', 'nodejs'),
        'description': original_content.get('description', f'{stack_name} stack'),
    }

    # Write deployment-specific Pulumi.yaml
    import yaml
    with open(pulumi_yaml, 'w') as f:
        yaml.safe_dump(new_content, f)

    logger.info(f"Generated Pulumi.yaml with project: {self.project}")
```

2. **Add Context Manager for Safe Operations**

```python
from contextlib import contextmanager

@contextmanager
def deployment_context(self, stack_dir: Path, stack_name: str):
    """
    Context manager for deployment-specific Pulumi.yaml

    Usage:
        with pulumi_wrapper.deployment_context(stack_dir, "network"):
            # Pulumi operations here
            pulumi_wrapper.select_stack(...)
            pulumi_wrapper.up(...)

    Args:
        stack_dir: Stack directory path
        stack_name: Base stack name

    Yields:
        None - Context for operations
    """
    backup_path = None
    try:
        # Backup and generate
        backup_path = self._backup_pulumi_yaml(stack_dir)
        self._generate_pulumi_yaml(stack_dir, stack_name)

        yield

    finally:
        # Always restore original
        self._restore_pulumi_yaml(stack_dir, backup_path)
```

3. **Update select_stack to Use Context**

```python
def select_stack(
    self, stack_name: str, create: bool = True, cwd: Optional[Path] = None
) -> None:
    """
    Select (and optionally create) a Pulumi stack

    NOTE: Must be called within deployment_context() to ensure
    correct Pulumi.yaml is present.

    Args:
        stack_name: Stack name in format: deployment-id-stack-name-environment
        create: Whether to create if doesn't exist
        cwd: Working directory (stack directory)
    """
    full_stack_name = f"{self.organization}/{self.project}/{stack_name}"

    # Validation: Ensure we're in a context (optional but recommended)
    if cwd:
        pulumi_yaml = Path(cwd) / "Pulumi.yaml"
        if pulumi_yaml.exists():
            import yaml
            with open(pulumi_yaml) as f:
                content = yaml.safe_load(f)
                if content.get('name') != self.project:
                    logger.warning(
                        f"Pulumi.yaml project '{content.get('name')}' "
                        f"doesn't match expected '{self.project}'. "
                        f"Did you forget deployment_context()?"
                    )

    # Rest of select_stack implementation unchanged
    # ...
```

### Phase 2: Command Integration

**Files to Update:**
- `cloud/tools/cli/src/cloud_cli/commands/deploy_stack_cmd.py`
- `cloud/tools/cli/src/cloud_cli/commands/destroy_stack_cmd.py`
- `cloud/tools/cli/src/cloud_cli/commands/deploy_cmd.py`
- `cloud/tools/cli/src/cloud_cli/commands/destroy_cmd.py`

#### deploy_stack_cmd.py Changes:

**Current code (lines 103-147):**
```python
# Get Pulumi organization and project from manifest
pulumi_org = manifest.get("pulumiOrg", manifest.get("organization", ""))
project = manifest.get("project", deployment_id)  # Use deployment project name

pulumi_wrapper = PulumiWrapper(organization=pulumi_org, project=project)
stack_ops = StackOperations(pulumi_wrapper)

try:
    # Get stack directory
    stack_dir = get_stacks_dir() / stack_name

    # Deploy
    success, error = stack_ops.deploy_stack(
        deployment_id=deployment_id,
        stack_name=stack_name,
        environment=environment,
        stack_dir=stack_dir,
        config_file=config_file,
        preview=preview,
    )
    # ...
```

**New code:**
```python
# Get Pulumi organization and project from manifest
pulumi_org = manifest.get("pulumiOrg", manifest.get("organization", ""))
project = manifest.get("project", deployment_id)  # Use deployment project name

pulumi_wrapper = PulumiWrapper(organization=pulumi_org, project=project)
stack_ops = StackOperations(pulumi_wrapper)

try:
    # Get stack directory
    stack_dir = get_stacks_dir() / stack_name

    # Use deployment context for Pulumi.yaml management
    with pulumi_wrapper.deployment_context(stack_dir, stack_name):
        # Deploy within context
        success, error = stack_ops.deploy_stack(
            deployment_id=deployment_id,
            stack_name=stack_name,
            environment=environment,
            stack_dir=stack_dir,
            config_file=config_file,
            preview=preview,
        )
    # Pulumi.yaml automatically restored here

    # Rest of error handling...
```

**Same pattern for destroy_stack_cmd.py**

#### deploy_cmd.py Changes:

**Current orchestration loop (around line 230):**
```python
for stack_info in execution_plan:
    # Deploy each stack
    stack_name = stack_info["stack"]
    layer = stack_info["layer"]

    # ... deployment logic
```

**New code with context:**
```python
for stack_info in execution_plan:
    stack_name = stack_info["stack"]
    layer = stack_info["layer"]

    stack_dir = get_stacks_dir() / stack_name

    # Use deployment context for each stack
    with pulumi_wrapper.deployment_context(stack_dir, stack_name):
        # ... existing deployment logic inside context
        success, error = stack_ops.deploy_stack(...)
    # Pulumi.yaml restored automatically
```

### Phase 3: StackOperations Verification

**File:** `cloud/tools/core/cloud_core/pulumi/stack_operations.py`

Verify that all Pulumi operations receive the `cwd` parameter correctly so they operate in the right directory with the deployment-specific Pulumi.yaml.

No changes needed if PulumiWrapper is used correctly, but add assertions:

```python
def deploy_stack(self, ..., stack_dir: Path, ...):
    """Deploy a stack"""

    # Validate Pulumi.yaml exists
    pulumi_yaml = stack_dir / "Pulumi.yaml"
    if not pulumi_yaml.exists():
        raise PulumiError(
            f"Pulumi.yaml not found in {stack_dir}. "
            f"Ensure deployment_context() is used."
        )

    # Rest of implementation...
```

---

## Edge Cases and Error Handling

### 1. Concurrent Deployments

**Problem:** Two deployments using same stack type simultaneously

**Solution:** Backup file naming includes project name:
```python
backup_path = stack_dir / f"Pulumi.yaml.backup.{self.project}"
# Example: Pulumi.yaml.backup.ecommerce
#          Pulumi.yaml.backup.mobile-app
```

Each deployment's backup is separate, preventing conflicts.

### 2. Cleanup on Error

**Problem:** Exception during deployment leaves modified Pulumi.yaml

**Solution:** Context manager's `finally` block ensures restoration:
```python
@contextmanager
def deployment_context(...):
    backup_path = None
    try:
        backup_path = self._backup_pulumi_yaml(stack_dir)
        self._generate_pulumi_yaml(stack_dir, stack_name)
        yield
    finally:
        # ALWAYS runs, even on exception
        self._restore_pulumi_yaml(stack_dir, backup_path)
```

### 3. Missing Original Pulumi.yaml

**Problem:** Stack directory has no Pulumi.yaml

**Solution:** Generate minimal valid one:
```python
def _generate_pulumi_yaml(self, stack_dir: Path, stack_name: str):
    pulumi_yaml = stack_dir / "Pulumi.yaml"

    original_content = {}
    if pulumi_yaml.exists():
        # Read original
        with open(pulumi_yaml, 'r') as f:
            original_content = yaml.safe_load(f) or {}

    new_content = {
        'name': self.project,
        'runtime': original_content.get('runtime', 'nodejs'),  # ← Default
        'description': original_content.get('description', f'{stack_name} stack'),
    }
    # ...
```

### 4. Pulumi.yaml Locked by Process

**Problem:** Another process has file open

**Solution:** Retry with exponential backoff:
```python
import time

def _backup_pulumi_yaml(self, stack_dir: Path) -> Optional[Path]:
    pulumi_yaml = stack_dir / "Pulumi.yaml"
    if not pulumi_yaml.exists():
        return None

    backup_path = stack_dir / f"Pulumi.yaml.backup.{self.project}"

    # Retry up to 3 times with exponential backoff
    for attempt in range(3):
        try:
            shutil.copy2(pulumi_yaml, backup_path)
            logger.debug(f"Backed up Pulumi.yaml to {backup_path}")
            return backup_path
        except (PermissionError, IOError) as e:
            if attempt < 2:
                wait_time = 2 ** attempt  # 1s, 2s, 4s
                logger.warning(f"Backup failed, retrying in {wait_time}s: {e}")
                time.sleep(wait_time)
            else:
                raise PulumiError(f"Cannot backup Pulumi.yaml after 3 attempts: {e}")
```

### 5. Leftover Backup Files

**Problem:** Previous deployment crashed, left backup file

**Solution:** Check for existing backups before starting:
```python
def deployment_context(self, stack_dir: Path, stack_name: str):
    backup_path = stack_dir / f"Pulumi.yaml.backup.{self.project}"

    # Clean up stale backup from previous run
    if backup_path.exists():
        logger.warning(f"Found stale backup {backup_path}, removing")
        backup_path.unlink()

    # Continue with normal backup/restore flow
    # ...
```

---

## Testing Strategy

### Unit Tests

**File:** `cloud/tools/core/tests/test_pulumi_wrapper_dynamic_yaml.py`

```python
def test_backup_restore_pulumi_yaml():
    """Test backup and restore of Pulumi.yaml"""
    # Setup: Create mock Pulumi.yaml
    # Test: Backup
    # Assert: Backup file exists
    # Test: Restore
    # Assert: Original restored, backup removed

def test_generate_pulumi_yaml():
    """Test generation of deployment-specific Pulumi.yaml"""
    # Setup: Create stack dir
    # Test: Generate with project="ecommerce"
    # Assert: Pulumi.yaml has name: ecommerce

def test_deployment_context_cleanup_on_error():
    """Test that context restores even on exception"""
    # Setup: Create Pulumi.yaml
    # Test: Enter context, raise exception
    # Assert: Original Pulumi.yaml restored

def test_concurrent_deployments():
    """Test multiple deployments don't conflict"""
    # Setup: Two PulumiWrappers with different projects
    # Test: Both create contexts simultaneously
    # Assert: Each has correct Pulumi.yaml
    # Assert: No backup file conflicts
```

### Integration Tests

**Manual Test Plan:**

1. **Single Deployment Test**
   ```bash
   cloud init --org TestOrg --project test-proj-1
   cloud deploy-stack <id> network --environment dev
   # Verify: Stack created at andre-2112/test-proj-1/XXX-network-dev
   ```

2. **Multiple Deployment Test**
   ```bash
   cloud init --org TestOrg --project test-proj-1
   cloud init --org TestOrg --project test-proj-2
   cloud deploy-stack <id1> network --environment dev
   cloud deploy-stack <id2> network --environment dev
   # Verify: Both stacks under different projects in Pulumi Cloud
   # Verify: Original Pulumi.yaml unchanged
   ```

3. **Full Orchestration Test**
   ```bash
   cloud deploy <id> --environment dev
   # Verify: All stacks grouped under same project
   ```

4. **Error Recovery Test**
   ```bash
   # Kill deployment mid-operation (Ctrl+C)
   # Verify: Pulumi.yaml restored to original
   # Verify: No leftover backup files
   ```

---

## Migration Plan

### Existing Deployments

**Status:** All test deployments destroyed in preparation for this change

**No migration needed:** Fresh start with new naming convention

### Pulumi Cloud Organization

**Current state (old broken naming):**
```
andre-2112/
├── network/
│   ├── DTEST03-network-dev (0 resources, destroyed)
│   ├── DWXE7BR-network-dev (0 resources, destroyed)
│   └── ... (all destroyed)
├── security/
└── ...
```

**After implementation:**
```
andre-2112/
├── test-proj-1/  # ← Deployment project
│   ├── D1ABC45-network-dev
│   ├── D1ABC45-security-dev
│   └── D1ABC45-storage-dev
├── test-proj-2/  # ← Different deployment
│   ├── D2XYZ78-network-dev
│   └── ...
└── ... (old empty projects can be ignored)
```

---

## Performance Considerations

### File I/O Overhead

**Operations per deployment:**
- 1x backup (copy Pulumi.yaml)
- 1x generate (write new Pulumi.yaml)
- 1x restore (move backup back)

**Total:** ~3 file operations per stack deployment

**Impact:** Negligible (<10ms) compared to Pulumi operations (minutes)

### Disk Space

**Backup file size:** ~100 bytes (Pulumi.yaml is tiny)

**Concurrent deployments:** Max 1 backup file per deployment

**Cleanup:** Automatic via context manager

**Impact:** Negligible

---

## Alternative Approaches Considered

### 1. Pulumi Backend Configuration

**Idea:** Use Pulumi's project name override in backend URL

**Research:** Pulumi requires project name match Pulumi.yaml, no override option

**Conclusion:** Not possible without Pulumi.yaml modification

### 2. Multiple Stack Directories

**Idea:** Create `stacks/{project}/{stack}/` hierarchy

**Pros:** Clean separation, no dynamic generation

**Cons:**
- Massive refactor of directory structure
- Duplicate code across projects
- Complex path resolution
- Breaks existing tooling

**Conclusion:** Too invasive for current architecture

### 3. Pulumi Automation API

**Idea:** Use Automation API to programmatically set project

**Research:** Automation API also respects Pulumi.yaml, no bypass

**Conclusion:** Still requires Pulumi.yaml modification

### 4. Symlinks

**Idea:** Symlink stack code, separate Pulumi.yaml per project

**Pros:** True isolation

**Cons:**
- Windows symlink requires admin or Developer Mode
- Complex to maintain
- Breaks on some CI/CD systems
- node_modules handling issues

**Conclusion:** Too platform-dependent

---

## Success Criteria

### Implementation Complete When:

1. ✅ PulumiWrapper has deployment_context() implemented
2. ✅ All 4 command files use deployment_context()
3. ✅ Unit tests pass for backup/restore/generate
4. ✅ Manual testing shows correct Pulumi Cloud organization
5. ✅ Original Pulumi.yaml files unchanged after operations
6. ✅ No leftover backup files after successful operations
7. ✅ Error scenarios properly restore original files

### Verification Commands:

```bash
# 1. Check Pulumi Cloud organization
pulumi stack ls --all
# Should show: andre-2112/test-proj-1/... and andre-2112/test-proj-2/...

# 2. Verify original Pulumi.yaml
cat cloud/stacks/network/Pulumi.yaml
# Should show: name: network (original unchanged)

# 3. Check for leftover backups
ls cloud/stacks/*/Pulumi.yaml.backup.*
# Should return: no files found

# 4. Verify deployment grouping
cloud list
# Both deployments should show correct project names
```

---

## Implementation Order

1. **Phase 1:** PulumiWrapper enhancement (backup, restore, generate, context)
2. **Phase 2:** Update deploy_stack_cmd.py and destroy_stack_cmd.py
3. **Test:** Single stack deployment
4. **Phase 3:** Update deploy_cmd.py and destroy_cmd.py (orchestration)
5. **Test:** Full deployment orchestration
6. **Phase 4:** Template updates (TestOrg/TestProj defaults)
7. **Final Test:** Create 2 test deployments, verify Pulumi Cloud organization

---

## Documentation Updates Required

### 1. Update Multi_Stack_Architecture.4.1.md

Add section explaining dynamic Pulumi.yaml generation:

```markdown
#### Pulumi.yaml Dynamic Generation (v4.1.1)

Due to Pulumi's requirement that project names match the `Pulumi.yaml` file
in each stack directory, the platform dynamically generates deployment-specific
Pulumi.yaml files during stack operations.

**Process:**
1. Backup original `cloud/stacks/{stack}/Pulumi.yaml`
2. Generate temporary Pulumi.yaml with `name: {deployment-project}`
3. Execute Pulumi operations
4. Restore original Pulumi.yaml

This ensures the architecture's intent (grouping by deployment project) is
preserved while maintaining compatibility with Pulumi's design.
```

### 2. Update Addendum_Pulumi_Stack_Naming_Discrepancy.4.1.md

Add resolution section:

```markdown
## Resolution: Dynamic Pulumi.yaml Generation

**Status:** Implemented in v4.1.1
**Date:** 2025-10-30

The naming discrepancy has been resolved by implementing dynamic Pulumi.yaml
generation. See `Addendum_Dynamic_Pulumi_YAML_Implementation.4.1.md` for
complete implementation details.

The fixes to deploy_stack_cmd.py and destroy_stack_cmd.py are retained,
and now work correctly with the dynamic Pulumi.yaml generation system.
```

### 3. Create this document

`Addendum_Dynamic_Pulumi_YAML_Implementation.4.1.md` (this file)

---

## Version History

- **v4.1 (2025-10-30):** Initial implementation plan for dynamic Pulumi.yaml generation

---

## References

- **Architecture:** Multi_Stack_Architecture.4.1.md, lines 2861-2888
- **Original Issue:** Addendum_Pulumi_Stack_Naming_Discrepancy.4.1.md
- **Pulumi Docs:** https://www.pulumi.com/docs/intro/concepts/project/
- **Related Code:**
  - pulumi_wrapper.py
  - deploy_stack_cmd.py
  - destroy_stack_cmd.py
  - deploy_cmd.py
  - destroy_cmd.py
