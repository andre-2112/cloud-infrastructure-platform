# CLI v4.1 Integration Fix - Implementation Plan

**Date:** 2025-10-29
**Based On:** Network_Stack_Test_2_Report_v4.1.md
**Architecture Version:** 4.1
**Status:** 📋 PLANNED

---

## Context

This plan implements all recommendations from Test 2, which discovered critical CLI-Core integration gaps despite 99.8% core library test coverage. While `deploy-stack` and `destroy-stack` commands were fixed during Test 2, **12 of 14 CLI commands remain untested** and likely contain similar issues.

### Key Documents Referenced
- `cloud/tools/docs/Network_Stack_Test_2_Report_v4.1.md` - Source of recommendations
- `cloud/tools/docs/Implementation_Status_Report_v4.1.md` - Core library compliance status
- `cloud/tools/docs/Deployment_Manifest_Specification.4.1.md` - v4.1 manifest format
- `cloud/tools/core/cloud_core/deployment/state_manager.py` - Actual StateManager API
- `cloud/tools/core/cloud_core/pulumi/stack_operations.py` - Actual StackOperations API
- `cloud/tools/core/cloud_core/pulumi/wrapper.py` - Actual PulumiWrapper API

### Issues Fixed in Test 2
✅ `destroy_stack_cmd.py` - Fixed 4 critical issues
✅ `deploy_stack_cmd.py` - Fixed 4 critical issues
✅ `manifest_validator.py` - Updated to v4.1 format

### Known Issue Patterns from Test 2
1. **Method Name Mismatches** - CLI calls non-existent methods
2. **Parameter Signature Mismatches** - Wrong parameter names/types/order
3. **Return Type Mismatches** - CLI expects dicts, core returns tuples
4. **Missing Imports** - StackStatus enum not imported
5. **Wrong Organization Field** - Using `organization` instead of `pulumiOrg`

---

## Phase 1: IMMEDIATE (CRITICAL) - CLI Audit & Testing

### Task 1.1: Audit All CLI Commands

**Objective:** Systematically check all 14 CLI command files for same issues found in Test 2.

**Files to Audit:**
```
cloud/tools/cli/src/cloud_cli/commands/
├── ✅ deploy_stack_cmd.py      (FIXED - Test 2)
├── ✅ destroy_stack_cmd.py     (FIXED - Test 2)
├── ❓ deploy_cmd.py            (AUDIT NEEDED - likely broken)
├── ❓ destroy_cmd.py           (AUDIT NEEDED - likely broken)
├── ❓ rollback_cmd.py          (AUDIT NEEDED - likely broken)
├── ❓ status_cmd.py            (AUDIT NEEDED)
├── ❓ validate_cmd.py          (AUDIT NEEDED)
├── ❓ init_cmd.py              (AUDIT NEEDED)
├── ❓ list_cmd.py              (AUDIT NEEDED)
└── ❓ [other commands]         (AUDIT NEEDED)
```

**Audit Checklist per Command:**

For each command file, verify:

1. **StateManager Usage:**
   - [ ] Imports `StackStatus` enum from `cloud_core.deployment`
   - [ ] Calls `set_stack_status(stack_name, StackStatus.ENUM, environment)`
   - [ ] NOT calling `update_stack_state()` (doesn't exist)
   - [ ] Parameter order: stack_name, status, environment

2. **PulumiWrapper Initialization:**
   - [ ] Passes required parameters: `organization` and `project`
   - [ ] Uses `pulumiOrg` from manifest (e.g., "andre-2112")
   - [ ] NOT using `organization` field for Pulumi org
   - [ ] Uses stack_name as project or manifest project field

3. **StackOperations Method Calls:**
   - [ ] Calls `deploy_stack()` not `deploy()` or `up()`
   - [ ] Calls `destroy_stack()` not `destroy()` or `down()`
   - [ ] Uses `stack_dir` parameter (Path type)
   - [ ] Handles tuple return: `success, error = ...`
   - [ ] NOT expecting dict return: `result["success"]`

4. **ManifestValidator Usage:**
   - [ ] Validates v4.1 flat format (deployment_id, organization at root)
   - [ ] NOT checking for v3.1 nested format (deployment: { id, ... })

**Audit Process:**

1. Read each command file
2. Search for patterns:
   - `update_stack_state` (wrong method)
   - `PulumiWrapper()` with no args (missing params)
   - `.destroy(` or `.up(` (wrong method names)
   - `result[` after stack_ops call (wrong return handling)
   - `["success"]` (expecting dict return)
3. Compare against actual core library APIs
4. Document all issues found
5. Create fix list

**Success Criteria:**
- All 14 commands audited
- All issues documented
- Fix priority assigned (Critical/High/Medium)

**Time Estimate:** 2-3 hours

---

### Task 1.2: Fix All CLI Command Issues

**Objective:** Apply fixes to all broken commands using patterns from Test 2.

**Fix Template (based on Test 2 fixes):**

```python
# 1. Import Fix
from cloud_core.deployment import DeploymentManager, StateManager, StackStatus  # Add StackStatus

# 2. PulumiWrapper Initialization Fix
pulumi_org = manifest.get("pulumiOrg", manifest.get("organization", ""))
project = stack_name  # or manifest.get("project", stack_name)
pulumi_wrapper = PulumiWrapper(organization=pulumi_org, project=project)

# 3. StateManager Method Fix
# WRONG:
state_manager.update_stack_state(stack_name, environment, "deploying")

# RIGHT:
state_manager.set_stack_status(stack_name, StackStatus.DEPLOYING, environment)

# 4. StackOperations Deploy Fix
# WRONG:
result = stack_ops.deploy(deployment_id=..., work_dir=str(stack_dir))
if result["success"]:

# RIGHT:
success, error = stack_ops.deploy_stack(
    deployment_id=deployment_id,
    stack_name=stack_name,
    environment=environment,
    stack_dir=stack_dir,
    preview=preview,
)
if success:
    # ...
else:
    console.print(f"Failed: {error}")

# 5. StackOperations Destroy Fix
# WRONG:
result = stack_ops.destroy(work_dir=str(stack_dir))

# RIGHT:
success, error = stack_ops.destroy_stack(
    deployment_id=deployment_id,
    stack_name=stack_name,
    environment=environment,
    stack_dir=stack_dir,
)
```

**Process:**
1. Apply fixes to each broken command
2. Follow exact patterns from fixed commands
3. Test each fix (see Task 1.3)
4. Document changes made

**Success Criteria:**
- All CLI commands use correct method signatures
- All commands handle return types correctly
- No runtime errors from method/attribute mismatches

**Time Estimate:** 3-4 hours

---

### Task 1.3: Add CLI Smoke Tests

**Objective:** Create basic tests to catch CLI-Core integration issues before deployment.

**Test File:** `cloud/tools/cli/tests/test_cli_smoke.py`

**Test Coverage:**

```python
"""
CLI Smoke Tests

Tests that CLI commands can be invoked and use correct core library APIs.
Does NOT test actual deployment (uses mocks).
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from typer.testing import CliRunner

from cloud_cli.main import app
from cloud_core.deployment import StackStatus

runner = CliRunner()


class TestCLICommandInvocation:
    """Test that commands can be invoked without errors"""

    def test_help_commands(self):
        """Test all commands have help text"""
        commands = [
            "deploy-stack", "destroy-stack", "deploy", "destroy",
            "rollback", "status", "validate", "init", "list"
        ]
        for cmd in commands:
            result = runner.invoke(app, [cmd, "--help"])
            assert result.exit_code == 0, f"{cmd} --help failed"
            assert "help" in result.stdout.lower()

    def test_version_display(self):
        """Test version shows v4.1"""
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "4.1" in result.stdout or "4" in result.stdout


class TestStateManagerIntegration:
    """Test CLI correctly uses StateManager API"""

    @patch('cloud_cli.commands.deploy_stack_cmd.StateManager')
    @patch('cloud_cli.commands.deploy_stack_cmd.DeploymentManager')
    @patch('cloud_cli.commands.deploy_stack_cmd.ManifestValidator')
    @patch('cloud_cli.commands.deploy_stack_cmd.PulumiWrapper')
    @patch('cloud_cli.commands.deploy_stack_cmd.StackOperations')
    def test_deploy_stack_uses_set_stack_status(self, mock_ops, mock_pulumi,
                                                 mock_validator, mock_dm, mock_sm):
        """Test deploy-stack calls set_stack_status with StackStatus enum"""
        # Setup mocks
        mock_dm_instance = Mock()
        mock_dm_instance.get_deployment_dir.return_value = Path("/fake/deployment")
        mock_dm.return_value = mock_dm_instance

        mock_validator_instance = Mock()
        mock_validator_instance.validate.return_value = True
        mock_validator_instance.manifest = {
            "pulumiOrg": "test-org",
            "stacks": {"network": {"enabled": True, "layer": 1}},
            "environments": {"dev": {"enabled": True}}
        }
        mock_validator.return_value = mock_validator_instance

        mock_sm_instance = Mock()
        mock_sm.return_value = mock_sm_instance

        mock_ops_instance = Mock()
        mock_ops_instance.deploy_stack.return_value = (True, None)
        mock_ops.return_value = mock_ops_instance

        # Run command
        result = runner.invoke(app, ["deploy-stack", "TEST01", "network"])

        # Verify set_stack_status called with StackStatus enum
        calls = mock_sm_instance.set_stack_status.call_args_list
        assert len(calls) >= 2, "Should call set_stack_status at least twice"

        # Check first call uses StackStatus.DEPLOYING
        first_call = calls[0]
        assert first_call[0][0] == "network"  # stack_name
        assert isinstance(first_call[0][1], StackStatus) or first_call[0][1] == StackStatus.DEPLOYING

        # Verify NOT called with strings
        for call in calls:
            assert not isinstance(call[0][1], str), "Status should be StackStatus enum, not string"

    @patch('cloud_cli.commands.destroy_stack_cmd.StateManager')
    @patch('cloud_cli.commands.destroy_stack_cmd.DeploymentManager')
    @patch('cloud_cli.commands.destroy_stack_cmd.ManifestValidator')
    @patch('cloud_cli.commands.destroy_stack_cmd.PulumiWrapper')
    @patch('cloud_cli.commands.destroy_stack_cmd.StackOperations')
    def test_destroy_stack_uses_set_stack_status(self, mock_ops, mock_pulumi,
                                                  mock_validator, mock_dm, mock_sm):
        """Test destroy-stack calls set_stack_status with StackStatus enum"""
        # Setup mocks (similar to deploy test)
        mock_dm_instance = Mock()
        mock_dm_instance.get_deployment_dir.return_value = Path("/fake/deployment")
        mock_dm.return_value = mock_dm_instance

        mock_validator_instance = Mock()
        mock_validator_instance.validate.return_value = True
        mock_validator_instance.manifest = {
            "pulumiOrg": "test-org",
            "stacks": {"network": {"enabled": True}},
        }
        mock_validator.return_value = mock_validator_instance

        mock_sm_instance = Mock()
        mock_sm.return_value = mock_sm_instance

        mock_ops_instance = Mock()
        mock_ops_instance.destroy_stack.return_value = (True, None)
        mock_ops.return_value = mock_ops_instance

        # Run command with --yes to skip confirmation
        result = runner.invoke(app, ["destroy-stack", "TEST01", "network", "--yes"])

        # Verify calls
        calls = mock_sm_instance.set_stack_status.call_args_list
        assert len(calls) >= 2

        # Verify StackStatus enum used
        for call in calls:
            assert isinstance(call[0][1], StackStatus), "Must use StackStatus enum"


class TestPulumiWrapperIntegration:
    """Test CLI correctly initializes PulumiWrapper"""

    @patch('cloud_cli.commands.deploy_stack_cmd.PulumiWrapper')
    @patch('cloud_cli.commands.deploy_stack_cmd.DeploymentManager')
    @patch('cloud_cli.commands.deploy_stack_cmd.ManifestValidator')
    @patch('cloud_cli.commands.deploy_stack_cmd.StackOperations')
    def test_pulumi_wrapper_initialized_with_required_params(self, mock_ops,
                                                             mock_validator, mock_dm,
                                                             mock_pulumi):
        """Test PulumiWrapper called with organization and project"""
        # Setup
        mock_dm_instance = Mock()
        mock_dm_instance.get_deployment_dir.return_value = Path("/fake")
        mock_dm.return_value = mock_dm_instance

        mock_validator_instance = Mock()
        mock_validator_instance.validate.return_value = True
        mock_validator_instance.manifest = {
            "pulumiOrg": "andre-2112",
            "organization": "TestOrg",
            "stacks": {"network": {"enabled": True, "layer": 1}},
            "environments": {"dev": {"enabled": True}}
        }
        mock_validator.return_value = mock_validator_instance

        mock_ops_instance = Mock()
        mock_ops_instance.deploy_stack.return_value = (True, None)
        mock_ops.return_value = mock_ops_instance

        # Run
        runner.invoke(app, ["deploy-stack", "TEST01", "network"])

        # Verify PulumiWrapper called with correct params
        mock_pulumi.assert_called_once()
        call_kwargs = mock_pulumi.call_args[1]

        assert "organization" in call_kwargs, "Must pass organization parameter"
        assert "project" in call_kwargs, "Must pass project parameter"

        # Verify uses pulumiOrg, NOT organization field
        assert call_kwargs["organization"] == "andre-2112", "Must use pulumiOrg field"
        assert call_kwargs["organization"] != "TestOrg", "Must NOT use organization field"


class TestStackOperationsIntegration:
    """Test CLI correctly calls StackOperations methods"""

    @patch('cloud_cli.commands.deploy_stack_cmd.StackOperations')
    @patch('cloud_cli.commands.deploy_stack_cmd.PulumiWrapper')
    @patch('cloud_cli.commands.deploy_stack_cmd.DeploymentManager')
    @patch('cloud_cli.commands.deploy_stack_cmd.ManifestValidator')
    @patch('cloud_cli.commands.deploy_stack_cmd.StateManager')
    def test_deploy_calls_deploy_stack_not_deploy(self, mock_sm, mock_validator,
                                                   mock_dm, mock_pulumi, mock_ops):
        """Test deploy-stack calls deploy_stack() not deploy()"""
        # Setup
        mock_dm_instance = Mock()
        mock_dm_instance.get_deployment_dir.return_value = Path("/fake")
        mock_dm.return_value = mock_dm_instance

        mock_validator_instance = Mock()
        mock_validator_instance.validate.return_value = True
        mock_validator_instance.manifest = {
            "pulumiOrg": "test-org",
            "stacks": {"network": {"enabled": True, "layer": 1}},
            "environments": {"dev": {"enabled": True}}
        }
        mock_validator.return_value = mock_validator_instance

        mock_ops_instance = Mock()
        mock_ops_instance.deploy_stack.return_value = (True, None)
        mock_ops.return_value = mock_ops_instance

        # Run
        runner.invoke(app, ["deploy-stack", "TEST01", "network"])

        # Verify deploy_stack called (not deploy or up)
        mock_ops_instance.deploy_stack.assert_called_once()

        # Verify correct parameters
        call_kwargs = mock_ops_instance.deploy_stack.call_args[1]
        assert "deployment_id" in call_kwargs
        assert "stack_name" in call_kwargs
        assert "environment" in call_kwargs
        assert "stack_dir" in call_kwargs
        assert isinstance(call_kwargs["stack_dir"], Path), "stack_dir must be Path, not string"

    @patch('cloud_cli.commands.destroy_stack_cmd.StackOperations')
    @patch('cloud_cli.commands.destroy_stack_cmd.PulumiWrapper')
    @patch('cloud_cli.commands.destroy_stack_cmd.DeploymentManager')
    @patch('cloud_cli.commands.destroy_stack_cmd.ManifestValidator')
    @patch('cloud_cli.commands.destroy_stack_cmd.StateManager')
    def test_destroy_calls_destroy_stack_not_destroy(self, mock_sm, mock_validator,
                                                      mock_dm, mock_pulumi, mock_ops):
        """Test destroy-stack calls destroy_stack() not destroy()"""
        # Setup
        mock_dm_instance = Mock()
        mock_dm_instance.get_deployment_dir.return_value = Path("/fake")
        mock_dm.return_value = mock_dm_instance

        mock_validator_instance = Mock()
        mock_validator_instance.validate.return_value = True
        mock_validator_instance.manifest = {
            "pulumiOrg": "test-org",
            "stacks": {"network": {"enabled": True}},
        }
        mock_validator.return_value = mock_validator_instance

        mock_ops_instance = Mock()
        mock_ops_instance.destroy_stack.return_value = (True, None)
        mock_ops.return_value = mock_ops_instance

        # Run
        runner.invoke(app, ["destroy-stack", "TEST01", "network", "--yes"])

        # Verify destroy_stack called
        mock_ops_instance.destroy_stack.assert_called_once()

        # Verify return handled as tuple
        call_kwargs = mock_ops_instance.destroy_stack.call_args[1]
        assert "stack_dir" in call_kwargs
        assert isinstance(call_kwargs["stack_dir"], Path)

    def test_return_type_handling(self):
        """Test commands handle tuple returns from stack operations"""
        # This is validated through the mocks above
        # Actual return is (bool, Optional[str]), not dict
        pass


class TestManifestValidator:
    """Test ManifestValidator works with v4.1 format"""

    def test_validates_v4_1_flat_format(self, tmp_path):
        """Test validator accepts v4.1 flat format"""
        manifest_path = tmp_path / "deployment-manifest.yaml"
        manifest_path.write_text("""
version: "4.1"
deployment_id: "DTEST01"
organization: "TestOrg"
project: "TestProject"
domain: "test.example.com"
pulumiOrg: "andre-2112"

environments:
  dev:
    enabled: true
    region: us-east-1
    account_id: "123456789012"

stacks:
  network:
    enabled: true
    layer: 1
    dependencies: []
    config: {}
""")

        from cloud_core.validation import ManifestValidator
        validator = ManifestValidator()

        # Should validate successfully
        is_valid = validator.validate(str(manifest_path))

        if not is_valid:
            print("Validation errors:", validator.errors)

        assert is_valid, f"v4.1 manifest should be valid. Errors: {validator.errors}"

    def test_rejects_v3_1_nested_format(self, tmp_path):
        """Test validator rejects v3.1 nested format"""
        manifest_path = tmp_path / "deployment-manifest-old.yaml"
        manifest_path.write_text("""
version: "3.1"
deployment:
  id: "DTEST01"
  org: "TestOrg"
  project: "TestProject"
  domain: "test.example.com"
  region: us-east-1
""")

        from cloud_core.validation import ManifestValidator
        validator = ManifestValidator()

        # Should fail validation
        is_valid = validator.validate(str(manifest_path))
        assert not is_valid, "v3.1 manifest should be rejected"
        assert len(validator.errors) > 0


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

**Running Tests:**
```bash
cd cloud/tools/cli
python -m pytest tests/test_cli_smoke.py -v
```

**Success Criteria:**
- All smoke tests pass
- Tests catch method signature issues
- Tests verify correct API usage
- Can run in CI/CD pipeline

**Time Estimate:** 4-5 hours

---

### Task 1.4: Add Integration Tests

**Objective:** Create integration test suite to test CLI→Core interactions.

**Test File:** `cloud/tools/cli/tests/integration/test_cli_core_integration.py`

**Test Structure:**

```python
"""
Integration Tests: CLI ↔ Core Library

Tests actual interaction between CLI commands and core library.
Uses real core library classes with mocked Pulumi/AWS calls.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, Mock
from typer.testing import CliRunner

from cloud_cli.main import app
from cloud_core.deployment import DeploymentManager, StateManager
from cloud_core.pulumi import PulumiWrapper, StackOperations

runner = CliRunner()


@pytest.fixture
def mock_deployment(tmp_path):
    """Create a temporary deployment structure"""
    deployment_dir = tmp_path / "deployments" / "DTEST01"
    deployment_dir.mkdir(parents=True)

    manifest_path = deployment_dir / "deployment-manifest.yaml"
    manifest_path.write_text("""
version: "4.1"
deployment_id: "DTEST01"
organization: "TestOrg"
project: "TestProject"
domain: "test.example.com"
pulumiOrg: "andre-2112"

environments:
  dev:
    enabled: true
    region: us-east-1
    account_id: "123456789012"

stacks:
  network:
    enabled: true
    layer: 1
    dependencies: []
    config: {}
""")

    state_dir = deployment_dir / ".state"
    state_dir.mkdir()

    return deployment_dir


class TestDeployStackIntegration:
    """Integration tests for deploy-stack command"""

    @patch('cloud_core.pulumi.wrapper.subprocess.run')
    def test_deploy_stack_full_flow(self, mock_subprocess, mock_deployment, tmp_path):
        """Test complete deploy-stack flow with real core library"""
        # Mock Pulumi CLI calls
        mock_subprocess.return_value = Mock(
            returncode=0,
            stdout="Stack deployed successfully",
            stderr=""
        )

        # Setup stack directory
        stack_dir = tmp_path / "stacks" / "network"
        stack_dir.mkdir(parents=True)

        # Create minimal Pulumi.yaml
        (stack_dir / "Pulumi.yaml").write_text("name: network\nruntime: python\n")

        with patch('cloud_core.deployment.deployment_manager.Path.home') as mock_home:
            mock_home.return_value = tmp_path

            # Run deploy-stack command
            result = runner.invoke(app, [
                "deploy-stack", "DTEST01", "network",
                "--environment", "dev"
            ])

            # Verify command succeeded
            assert result.exit_code == 0 or "deployed" in result.stdout.lower()

            # Verify state was updated using actual StateManager
            state_manager = StateManager(mock_deployment)
            state = state_manager.get_stack_state("network", "dev")

            # State should show deployment attempt
            assert state is not None


class TestDestroyStackIntegration:
    """Integration tests for destroy-stack command"""

    @patch('cloud_core.pulumi.wrapper.subprocess.run')
    def test_destroy_stack_full_flow(self, mock_subprocess, mock_deployment, tmp_path):
        """Test complete destroy-stack flow with real core library"""
        # Mock Pulumi CLI calls
        mock_subprocess.return_value = Mock(
            returncode=0,
            stdout="Stack destroyed successfully",
            stderr=""
        )

        # Setup
        stack_dir = tmp_path / "stacks" / "network"
        stack_dir.mkdir(parents=True)
        (stack_dir / "Pulumi.yaml").write_text("name: network\nruntime: python\n")

        with patch('cloud_core.deployment.deployment_manager.Path.home') as mock_home:
            mock_home.return_value = tmp_path

            # Run destroy-stack command with --yes
            result = runner.invoke(app, [
                "destroy-stack", "DTEST01", "network",
                "--environment", "dev",
                "--yes"
            ])

            # Should complete without errors
            assert result.exit_code == 0 or "destroyed" in result.stdout.lower()
```

**Success Criteria:**
- Integration tests pass with real core library
- Tests verify actual CLI→Core interactions
- Pulumi/AWS calls properly mocked
- Can run in CI/CD

**Time Estimate:** 3-4 hours

---

## Phase 2: SHORT-TERM (IMPORTANT) - Documentation & Alignment

### Task 2.1: Update CLI Documentation

**Objective:** Ensure all CLI documentation reflects v4.1 architecture and correct usage.

**Files to Update:**

1. **CLI README** (`cloud/tools/cli/README.md`):
   - Update installation instructions
   - Show `cloud` command usage (not `python -m cloud_cli.main`)
   - Update example commands with v4.1 manifest format
   - Document all 14 commands
   - Add troubleshooting section

2. **CLI User Guide** (create if doesn't exist):
   - Command reference for all commands
   - v4.1 manifest format examples
   - Common workflows (init, deploy, status, destroy)
   - Error messages and solutions

3. **Core Library API Docs** (`cloud/tools/core/README.md`):
   - Document StateManager API (set_stack_status method)
   - Document PulumiWrapper initialization requirements
   - Document StackOperations return types
   - Add usage examples

**Documentation Template:**

```markdown
# Cloud CLI v4.1 User Guide

## Installation

```bash
# Install from source
cd cloud/tools/cli
pip install -e .

# Verify installation
cloud --version  # Should show 4.1.x
```

## Quick Start

```bash
# Initialize deployment
cloud init --template fullstack

# Deploy a single stack
cloud deploy-stack DTEST01 network --environment dev

# Check status
cloud status DTEST01 --environment dev

# Destroy stack
cloud destroy-stack DTEST01 network --environment dev --yes
```

## Commands Reference

### deploy-stack
Deploy a single stack.

**Usage:**
```bash
cloud deploy-stack <deployment-id> <stack-name> [OPTIONS]
```

**Options:**
- `--environment, -e` - Environment (dev/stage/prod) [default: dev]
- `--skip-dependencies` - Skip dependency checks
- `--preview` - Preview changes without deploying

**Example:**
```bash
cloud deploy-stack DTEST01 network --environment prod
```

[... document all 14 commands ...]

## Manifest Format (v4.1)

The CLI uses v4.1 flat manifest format:

```yaml
version: "4.1"
deployment_id: "DTEST01"
organization: "YourOrg"
project: "YourProject"
domain: "example.com"
pulumiOrg: "your-pulumi-org"

environments:
  dev:
    enabled: true
    region: us-east-1
    account_id: "123456789012"

stacks:
  network:
    enabled: true
    layer: 1
    dependencies: []
```

## Troubleshooting

### "Missing required field: deployment"
Your manifest is using v3.1 format. Update to v4.1 flat format.

### "PulumiWrapper missing arguments"
Ensure your manifest has `pulumiOrg` field for Pulumi Cloud organization.
```

**Success Criteria:**
- All documentation uses v4.1 format
- Installation process documented
- All commands documented with examples
- Troubleshooting section covers common errors

**Time Estimate:** 3-4 hours

---

### Task 2.2: Version Alignment

**Objective:** Ensure all version references are consistent with v4.1.

**Files to Check:**

```bash
# Search for version references
grep -r "3\.1" cloud/tools/cli/
grep -r "3\." cloud/tools/cli/ | grep -i version
grep -r "version" cloud/tools/cli/ | grep -E "(3\.|4\.)"
```

**Update Locations:**

1. **Setup.py** (`cloud/tools/cli/setup.py`):
   ```python
   version="0.7.0",  # CLI version
   # Ensure description mentions v4.1 architecture
   ```

2. **Main CLI** (`cloud/tools/cli/src/cloud_cli/main.py`):
   ```python
   app = typer.Typer(
       help="Cloud Infrastructure CLI - Architecture 4.1",  # Update if needed
   )
   ```

3. **Command Help Text:**
   - Review all command docstrings
   - Ensure no references to v3.1
   - Update examples to v4.1 format

4. **Test Files:**
   - Update test fixtures to use v4.1 manifests
   - Remove v3.1 test cases (or mark as legacy)

**Verification:**
```bash
# No v3.1 references should remain
grep -r "3\.1" cloud/tools/cli/ | grep -v ".pyc" | grep -v "__pycache__"

# Should return empty or only in comments about migration
```

**Success Criteria:**
- No v3.1 references in production code
- All examples use v4.1 format
- Version strings show 4.1
- Help text references v4.1

**Time Estimate:** 1-2 hours

---

## Phase 3: LONG-TERM (QUALITY) - Type Safety & Contracts

### Task 3.1: Enable Type Checking

**Objective:** Add mypy type checking to CLI to catch signature mismatches at development time.

**Setup mypy:**

1. **Install mypy:**
   ```bash
   pip install mypy
   ```

2. **Create mypy config** (`cloud/tools/cli/mypy.ini`):
   ```ini
   [mypy]
   python_version = 3.10
   warn_return_any = True
   warn_unused_configs = True
   disallow_untyped_defs = True
   disallow_any_unimported = True
   no_implicit_optional = True
   warn_redundant_casts = True
   warn_unused_ignores = True
   warn_no_return = True

   [mypy-typer.*]
   ignore_missing_imports = True

   [mypy-rich.*]
   ignore_missing_imports = True
   ```

3. **Add type hints to CLI commands:**
   ```python
   from typing import Optional
   from pathlib import Path

   def deploy_stack_command(
       deployment_id: str,
       stack_name: str,
       environment: str = "dev",
       skip_dependencies: bool = False,
       preview: bool = False,
   ) -> None:
       """Deploy a single stack"""
       # Type hints ensure correct usage
   ```

4. **Run mypy:**
   ```bash
   cd cloud/tools/cli
   mypy src/cloud_cli/
   ```

**Fix Type Errors:**
- Add return type annotations
- Add parameter type annotations
- Fix any type inconsistencies
- Use `Optional[T]` for nullable types

**Success Criteria:**
- mypy runs without errors
- All functions have type hints
- Type hints match core library APIs
- CI/CD runs mypy checks

**Time Estimate:** 4-5 hours

---

### Task 3.2: Define API Contracts

**Objective:** Create formal interfaces/protocols for core library APIs to detect breaking changes.

**Create Protocol Definitions:**

**File:** `cloud/tools/core/cloud_core/protocols.py`

```python
"""
API Protocols

Defines interfaces for core library components.
CLI and other consumers should code against these protocols.
"""

from typing import Protocol, Optional, Tuple
from pathlib import Path
from enum import Enum


class StackStatus(Enum):
    """Stack status enumeration"""
    PENDING = "pending"
    DEPLOYING = "deploying"
    DEPLOYED = "deployed"
    DESTROYING = "destroying"
    DESTROYED = "destroyed"
    FAILED = "failed"


class StateManagerProtocol(Protocol):
    """Interface for state management"""

    def set_stack_status(
        self,
        stack_name: str,
        status: StackStatus,
        environment: str = "dev"
    ) -> None:
        """Set stack status"""
        ...

    def get_stack_state(
        self,
        stack_name: str,
        environment: str = "dev"
    ) -> dict:
        """Get stack state"""
        ...


class StackOperationsProtocol(Protocol):
    """Interface for stack operations"""

    def deploy_stack(
        self,
        deployment_id: str,
        stack_name: str,
        environment: str,
        stack_dir: Path,
        preview: bool = False,
    ) -> Tuple[bool, Optional[str]]:
        """
        Deploy a stack

        Returns:
            (success: bool, error: Optional[str])
        """
        ...

    def destroy_stack(
        self,
        deployment_id: str,
        stack_name: str,
        environment: str,
        stack_dir: Path,
    ) -> Tuple[bool, Optional[str]]:
        """
        Destroy a stack

        Returns:
            (success: bool, error: Optional[str])
        """
        ...


class PulumiWrapperProtocol(Protocol):
    """Interface for Pulumi wrapper"""

    def __init__(
        self,
        organization: str,
        project: str,
        working_dir: Optional[Path] = None
    ) -> None:
        """Initialize Pulumi wrapper"""
        ...
```

**Use Protocols in CLI:**

```python
from cloud_core.protocols import StateManagerProtocol, StackOperationsProtocol

def deploy_stack_command(...) -> None:
    # Type checker will verify these match protocol
    state_manager: StateManagerProtocol = StateManager(deployment_dir)
    stack_ops: StackOperationsProtocol = StackOperations(pulumi_wrapper)

    # Will error if method signature doesn't match protocol
    state_manager.set_stack_status(stack_name, StackStatus.DEPLOYING, environment)
```

**Success Criteria:**
- Protocols defined for all core APIs
- CLI uses protocol types
- Breaking changes detected at type-check time
- Protocols documented

**Time Estimate:** 3-4 hours

---

## Execution Order

### Priority 1 (Week 1):
1. Task 1.1: Audit All CLI Commands (2-3 hours)
2. Task 1.2: Fix All CLI Command Issues (3-4 hours)
3. Task 1.3: Add CLI Smoke Tests (4-5 hours)

**Total:** 9-12 hours

### Priority 2 (Week 2):
4. Task 1.4: Add Integration Tests (3-4 hours)
5. Task 2.1: Update CLI Documentation (3-4 hours)
6. Task 2.2: Version Alignment (1-2 hours)

**Total:** 7-10 hours

### Priority 3 (Week 3):
7. Task 3.1: Enable Type Checking (4-5 hours)
8. Task 3.2: Define API Contracts (3-4 hours)

**Total:** 7-9 hours

**Grand Total:** 23-31 hours (approximately 1 month at 1 hour/day or 1 week full-time)

---

## Success Metrics

### Phase 1 Complete:
- ✅ All 14 CLI commands audited
- ✅ All CLI-Core integration bugs fixed
- ✅ Smoke tests passing (10+ tests)
- ✅ Integration tests passing (5+ tests)
- ✅ No method signature mismatches

### Phase 2 Complete:
- ✅ CLI documentation updated
- ✅ Installation process documented
- ✅ All version references show v4.1
- ✅ No v3.1 references remain
- ✅ Examples use v4.1 format

### Phase 3 Complete:
- ✅ mypy type checking enabled
- ✅ All CLI files have type hints
- ✅ mypy runs without errors
- ✅ API protocols defined
- ✅ CLI uses protocol types
- ✅ CI/CD includes type checks

### Overall Success:
- ✅ **0 CLI commands broken** (down from 12/14)
- ✅ **CLI test coverage > 80%**
- ✅ **Integration tests in CI/CD**
- ✅ **Type safety enforced**
- ✅ **API breaking changes detectable**
- ✅ **Production-ready CLI tool**

---

## Risk Mitigation

### Risk 1: More CLI Commands Broken Than Expected
**Mitigation:** Task 1.1 audit will reveal full scope. Adjust timeline if needed.

### Risk 2: Core Library API Changes During Implementation
**Mitigation:** Protocols (Task 3.2) will catch changes. Fix CLI immediately.

### Risk 3: Tests Reveal New Issues
**Mitigation:** Expected. Add new issues to fix list. Extend Phase 1 if needed.

### Risk 4: Breaking Existing Functionality
**Mitigation:**
- Run existing tests after each fix
- Test against Test 1 deployment manifest
- Keep original broken files as .backup until all tests pass

---

## Rollback Plan

If critical issues arise:

1. **Revert CLI Fixes:**
   ```bash
   git checkout HEAD~1 cloud/tools/cli/src/cloud_cli/commands/
   ```

2. **Use Direct Pulumi (Emergency Only):**
   ```bash
   cd deployments/DTEST01
   pulumi up --stack DTEST01-network-dev
   ```

3. **Restore from Backup:**
   ```bash
   cp cloud/tools/cli/src/cloud_cli/commands/*.backup *.py
   ```

**Note:** Rollback should be last resort. Fix issues instead (per Test 2 user directive).

---

## Appendix: Known Good API Signatures

### StateManager
```python
def set_stack_status(
    self,
    stack_name: str,
    status: StackStatus,  # Enum, not string
    environment: str = "dev"
) -> None
```

### StackOperations
```python
def deploy_stack(
    self,
    deployment_id: str,
    stack_name: str,
    environment: str,
    stack_dir: Path,  # Path, not string
    preview: bool = False,
) -> Tuple[bool, Optional[str]]  # Not dict

def destroy_stack(
    self,
    deployment_id: str,
    stack_name: str,
    environment: str,
    stack_dir: Path,  # Path, not string
) -> Tuple[bool, Optional[str]]  # Not dict
```

### PulumiWrapper
```python
def __init__(
    self,
    organization: str,  # Required - use pulumiOrg from manifest
    project: str,       # Required - typically stack_name
    working_dir: Optional[Path] = None
) -> None
```

---

**Plan Version:** 1.0
**Date:** 2025-10-29
**Status:** 📋 READY FOR EXECUTION
**Estimated Completion:** 3 weeks (1 hour/day) or 1 week (full-time)

**End of Plan**
