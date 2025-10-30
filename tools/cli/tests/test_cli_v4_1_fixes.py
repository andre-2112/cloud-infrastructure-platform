"""
CLI v4.1 Fixes Smoke Tests

Tests that verify the specific fixes applied in Task 1.2 for deploy_cmd and destroy_cmd.
These tests focus on the critical issues fixed:
1. StackStatus import and usage
2. PulumiWrapper initialization with correct parameters
3. Correct organization field usage (pulumiOrg)

NOTE: This is a targeted test suite. For comprehensive CLI testing, see test_cli_smoke.py (future).
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, ANY
from pathlib import Path
from typer.testing import CliRunner
import yaml

# Import CLI main app
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from cloud_cli.main import app
from cloud_core.deployment import StackStatus

runner = CliRunner()


@pytest.fixture
def mock_deployment_manifest(tmp_path):
    """Create a mock deployment structure with v4.1 manifest"""
    deployment_dir = tmp_path / "deployments" / "DTEST01"
    deployment_dir.mkdir(parents=True)

    # Create v4.1 flat format manifest
    manifest_content = {
        "version": "4.1",
        "deployment_id": "DTEST01",
        "organization": "TestOrg",  # Deployment organization
        "pulumiOrg": "test-pulumi-org",  # Pulumi Cloud organization (CRITICAL)
        "project": "TestProject",
        "domain": "test.example.com",
        "environments": {
            "dev": {
                "enabled": True,
                "region": "us-east-1",
                "account_id": "123456789012"
            }
        },
        "stacks": {
            "network": {
                "enabled": True,
                "layer": 1,
                "dependencies": [],
                "config": {}
            }
        }
    }

    manifest_path = deployment_dir / "deployment-manifest.yaml"
    with open(manifest_path, 'w') as f:
        yaml.dump(manifest_content, f)

    # Create state directory
    (deployment_dir / ".state").mkdir()

    return deployment_dir, manifest_content


class TestDeployCmdFixes:
    """Test deploy_cmd.py fixes"""

    @patch('cloud_cli.commands.deploy_cmd.DeploymentManager')
    @patch('cloud_cli.commands.deploy_cmd.ManifestValidator')
    @patch('cloud_cli.commands.deploy_cmd.DependencyValidator')
    @patch('cloud_cli.commands.deploy_cmd.Orchestrator')
    @patch('cloud_cli.commands.deploy_cmd.StateManager')
    @patch('cloud_cli.commands.deploy_cmd.PulumiWrapper')
    @patch('cloud_cli.commands.deploy_cmd.StackOperations')
    @patch('cloud_cli.commands.deploy_cmd.ConfigGenerator')
    @patch('cloud_cli.commands.deploy_cmd.asyncio.run')
    @patch('cloud_cli.commands.deploy_cmd.typer.confirm')
    def test_deploy_uses_pulumi_org_not_organization(
        self, mock_confirm, mock_asyncio, mock_config_gen, mock_stack_ops,
        mock_pulumi, mock_sm, mock_orch, mock_dep_val, mock_manifest_val,
        mock_dm, mock_deployment_manifest
    ):
        """
        CRITICAL TEST: Verify deploy_cmd uses pulumiOrg field, NOT organization field

        This was Issue #2 in deploy_cmd.py audit:
        - WRONG: org = manifest["organization"]  # "TestOrg"
        - RIGHT: pulumi_org = manifest.get("pulumiOrg", ...)  # "test-pulumi-org"
        """
        deployment_dir, manifest_content = mock_deployment_manifest

        # Setup mocks
        mock_dm_instance = Mock()
        mock_dm_instance.get_deployment_dir.return_value = deployment_dir
        mock_dm_instance.load_manifest.return_value = manifest_content
        mock_dm.return_value = mock_dm_instance

        mock_manifest_val_instance = Mock()
        mock_manifest_val_instance.validate_file.return_value = True
        mock_manifest_val_instance.get_errors.return_value = []
        mock_manifest_val.return_value = mock_manifest_val_instance

        mock_dep_val_instance = Mock()
        mock_dep_val_instance.validate.return_value = True
        mock_dep_val_instance.get_errors.return_value = []
        mock_dep_val.return_value = mock_dep_val_instance

        mock_orch_instance = Mock()
        mock_orch_instance.create_plan.return_value = Mock()
        mock_orch_instance.print_plan.return_value = "Plan"
        mock_orch.return_value = mock_orch_instance

        mock_sm_instance = Mock()
        mock_sm.return_value = mock_sm_instance

        mock_pulumi_instance = Mock()
        mock_pulumi.return_value = mock_pulumi_instance

        mock_config_gen_instance = Mock()
        mock_config_gen.return_value = mock_config_gen_instance

        mock_confirm.return_value = True  # Confirm deployment
        mock_asyncio.return_value = None  # Async execution succeeds

        # Run deploy command
        result = runner.invoke(app, [
            "deploy", "DTEST01",
            "--environment", "dev"
        ])

        # CRITICAL ASSERTION: PulumiWrapper called with pulumiOrg, NOT organization
        mock_pulumi.assert_called_once()
        call_kwargs = mock_pulumi.call_args[1]

        assert "organization" in call_kwargs, "PulumiWrapper must have organization parameter"
        assert call_kwargs["organization"] == "test-pulumi-org", \
            f"CRITICAL: Must use pulumiOrg ('test-pulumi-org'), not organization ('TestOrg'). Got: {call_kwargs['organization']}"

        # Verify it did NOT use the wrong organization field
        assert call_kwargs["organization"] != "TestOrg", \
            "CRITICAL: Must NOT use manifest['organization'] field for Pulumi"

    @patch('cloud_cli.commands.deploy_cmd.DeploymentManager')
    @patch('cloud_cli.commands.deploy_cmd.ManifestValidator')
    @patch('cloud_cli.commands.deploy_cmd.DependencyValidator')
    @patch('cloud_cli.commands.deploy_cmd.Orchestrator')
    @patch('cloud_cli.commands.deploy_cmd.StateManager')
    @patch('cloud_cli.commands.deploy_cmd.PulumiWrapper')
    @patch('cloud_cli.commands.deploy_cmd.StackOperations')
    @patch('cloud_cli.commands.deploy_cmd.ConfigGenerator')
    @patch('cloud_cli.commands.deploy_cmd.asyncio.run')
    @patch('cloud_cli.commands.deploy_cmd.typer.confirm')
    def test_deploy_uses_named_parameters_for_pulumi_wrapper(
        self, mock_confirm, mock_asyncio, mock_config_gen, mock_stack_ops,
        mock_pulumi, mock_sm, mock_orch, mock_dep_val, mock_manifest_val,
        mock_dm, mock_deployment_manifest
    ):
        """
        CRITICAL TEST: Verify PulumiWrapper called with named parameters

        This was Issue #3 in deploy_cmd.py audit:
        - WRONG: PulumiWrapper(org, project)
        - RIGHT: PulumiWrapper(organization=pulumi_org, project=project)
        """
        deployment_dir, manifest_content = mock_deployment_manifest

        # Setup mocks (same as previous test)
        mock_dm_instance = Mock()
        mock_dm_instance.get_deployment_dir.return_value = deployment_dir
        mock_dm_instance.load_manifest.return_value = manifest_content
        mock_dm.return_value = mock_dm_instance

        mock_manifest_val_instance = Mock()
        mock_manifest_val_instance.validate_file.return_value = True
        mock_manifest_val_instance.get_errors.return_value = []
        mock_manifest_val.return_value = mock_manifest_val_instance

        mock_dep_val_instance = Mock()
        mock_dep_val_instance.validate.return_value = True
        mock_dep_val_instance.get_errors.return_value = []
        mock_dep_val.return_value = mock_dep_val_instance

        mock_orch_instance = Mock()
        mock_orch_instance.create_plan.return_value = Mock()
        mock_orch_instance.print_plan.return_value = "Plan"
        mock_orch.return_value = mock_orch_instance

        mock_sm_instance = Mock()
        mock_sm.return_value = mock_sm_instance

        mock_pulumi_instance = Mock()
        mock_pulumi.return_value = mock_pulumi_instance

        mock_config_gen_instance = Mock()
        mock_config_gen.return_value = mock_config_gen_instance

        mock_confirm.return_value = True
        mock_asyncio.return_value = None

        # Run deploy command
        result = runner.invoke(app, [
            "deploy", "DTEST01",
            "--environment", "dev"
        ])

        # CRITICAL ASSERTION: Verify named parameters used
        mock_pulumi.assert_called_once()

        # Check that call used keyword arguments
        call_kwargs = mock_pulumi.call_args[1]
        assert "organization" in call_kwargs, "Must use named parameter 'organization'"
        assert "project" in call_kwargs, "Must use named parameter 'project'"

        # Verify values
        assert call_kwargs["organization"] == "test-pulumi-org"
        assert call_kwargs["project"] == "TestProject" or call_kwargs["project"] == "DTEST01"


class TestDestroyCmdFixes:
    """Test destroy_cmd.py fixes"""

    @patch('cloud_cli.commands.destroy_cmd.DeploymentManager')
    @patch('cloud_cli.commands.destroy_cmd.ManifestValidator')
    @patch('cloud_cli.commands.destroy_cmd.Orchestrator')
    @patch('cloud_cli.commands.destroy_cmd.StateManager')
    @patch('cloud_cli.commands.destroy_cmd.PulumiWrapper')
    @patch('cloud_cli.commands.destroy_cmd.asyncio.run')
    def test_destroy_initializes_pulumi_wrapper_with_parameters(
        self, mock_asyncio, mock_pulumi, mock_sm, mock_orch,
        mock_manifest_val, mock_dm, mock_deployment_manifest
    ):
        """
        CRITICAL TEST: Verify destroy_cmd creates PulumiWrapper with required parameters

        This was Issue #1 in destroy_cmd.py audit:
        - WRONG: PulumiWrapper()  # NO PARAMETERS!
        - RIGHT: PulumiWrapper(organization=pulumi_org, project=project)
        """
        deployment_dir, manifest_content = mock_deployment_manifest

        # Setup mocks
        mock_dm_instance = Mock()
        mock_dm_instance.get_deployment_dir.return_value = deployment_dir
        mock_dm.return_value = mock_dm_instance

        mock_manifest_val_instance = Mock()
        mock_manifest_val_instance.validate.return_value = True
        mock_manifest_val_instance.errors = []
        mock_manifest_val_instance.manifest = manifest_content
        mock_manifest_val.return_value = mock_manifest_val_instance

        mock_orch_instance = Mock()
        mock_plan = Mock()
        mock_plan.layers = [Mock()]  # Non-empty layers
        mock_plan.total_stacks = 1
        mock_orch_instance.create_destroy_plan.return_value = mock_plan
        mock_orch_instance.execute_destroy = Mock()
        mock_orch.return_value = mock_orch_instance

        mock_sm_instance = Mock()
        mock_sm.return_value = mock_sm_instance

        mock_pulumi_instance = Mock()
        mock_pulumi.return_value = mock_pulumi_instance

        mock_asyncio.return_value = None

        # Run destroy command with --yes flag
        result = runner.invoke(app, [
            "destroy", "DTEST01",
            "--environment", "dev",
            "--yes"
        ])

        # CRITICAL ASSERTION: PulumiWrapper called with required parameters
        mock_pulumi.assert_called_once()

        # Verify it was NOT called with empty parameters
        call_args = mock_pulumi.call_args
        assert call_args is not None, "PulumiWrapper should be called"

        # Verify named parameters provided
        call_kwargs = call_args[1]
        assert "organization" in call_kwargs, "CRITICAL: Must pass organization parameter"
        assert "project" in call_kwargs, "CRITICAL: Must pass project parameter"

        # Verify correct values from manifest
        assert call_kwargs["organization"] == "test-pulumi-org", \
            f"Must use pulumiOrg field. Got: {call_kwargs['organization']}"

    @patch('cloud_cli.commands.destroy_cmd.DeploymentManager')
    @patch('cloud_cli.commands.destroy_cmd.ManifestValidator')
    @patch('cloud_cli.commands.destroy_cmd.Orchestrator')
    @patch('cloud_cli.commands.destroy_cmd.StateManager')
    @patch('cloud_cli.commands.destroy_cmd.PulumiWrapper')
    @patch('cloud_cli.commands.destroy_cmd.asyncio.run')
    def test_destroy_uses_pulumi_org_not_organization(
        self, mock_asyncio, mock_pulumi, mock_sm, mock_orch,
        mock_manifest_val, mock_dm, mock_deployment_manifest
    ):
        """
        CRITICAL TEST: Verify destroy_cmd uses pulumiOrg field

        Same pattern as deploy_cmd fix - must use pulumiOrg for Pulumi Cloud.
        """
        deployment_dir, manifest_content = mock_deployment_manifest

        # Setup mocks (same as previous test)
        mock_dm_instance = Mock()
        mock_dm_instance.get_deployment_dir.return_value = deployment_dir
        mock_dm.return_value = mock_dm_instance

        mock_manifest_val_instance = Mock()
        mock_manifest_val_instance.validate.return_value = True
        mock_manifest_val_instance.errors = []
        mock_manifest_val_instance.manifest = manifest_content
        mock_manifest_val.return_value = mock_manifest_val_instance

        mock_orch_instance = Mock()
        mock_plan = Mock()
        mock_plan.layers = [Mock()]
        mock_plan.total_stacks = 1
        mock_orch_instance.create_destroy_plan.return_value = mock_plan
        mock_orch.return_value = mock_orch_instance

        mock_sm_instance = Mock()
        mock_sm.return_value = mock_sm_instance

        mock_pulumi_instance = Mock()
        mock_pulumi.return_value = mock_pulumi_instance

        mock_asyncio.return_value = None

        # Run destroy command
        result = runner.invoke(app, [
            "destroy", "DTEST01",
            "--environment", "dev",
            "--yes"
        ])

        # CRITICAL ASSERTION: Uses pulumiOrg, NOT organization
        mock_pulumi.assert_called_once()
        call_kwargs = mock_pulumi.call_args[1]

        assert call_kwargs["organization"] == "test-pulumi-org", \
            "CRITICAL: Must use pulumiOrg ('test-pulumi-org'), not organization ('TestOrg')"

        # Verify did NOT use wrong field
        assert call_kwargs["organization"] != "TestOrg", \
            "Must NOT use manifest['organization'] for Pulumi"


class TestStackStatusImport:
    """Test StackStatus enum import and usage"""

    def test_stack_status_enum_importable(self):
        """Verify StackStatus can be imported from cloud_core.deployment"""
        from cloud_core.deployment import StackStatus

        # Verify enum values exist
        assert hasattr(StackStatus, 'DEPLOYING')
        assert hasattr(StackStatus, 'DEPLOYED')
        assert hasattr(StackStatus, 'DESTROYING')
        assert hasattr(StackStatus, 'DESTROYED')
        assert hasattr(StackStatus, 'FAILED')

    def test_deploy_cmd_imports_stack_status(self):
        """Verify deploy_cmd.py imports StackStatus"""
        import cloud_cli.commands.deploy_cmd as deploy_cmd

        # Verify StackStatus is imported
        assert hasattr(deploy_cmd, 'StackStatus'), \
            "deploy_cmd.py must import StackStatus from cloud_core.deployment"

        # Verify it's the correct enum
        assert deploy_cmd.StackStatus.DEPLOYED.value == "deployed"
        assert deploy_cmd.StackStatus.FAILED.value == "failed"


class TestRegressionPrevention:
    """Tests to prevent regression of Test 2 fixes"""

    def test_deploy_stack_cmd_has_stack_status_import(self):
        """Verify deploy_stack_cmd.py still has StackStatus import (Test 2 fix)"""
        import cloud_cli.commands.deploy_stack_cmd as deploy_stack_cmd

        assert hasattr(deploy_stack_cmd, 'StackStatus'), \
            "deploy_stack_cmd.py must import StackStatus (Test 2 fix)"

    def test_destroy_stack_cmd_has_stack_status_import(self):
        """Verify destroy_stack_cmd.py still has StackStatus import (Test 2 fix)"""
        import cloud_cli.commands.destroy_stack_cmd as destroy_stack_cmd

        assert hasattr(destroy_stack_cmd, 'StackStatus'), \
            "destroy_stack_cmd.py must import StackStatus (Test 2 fix)"


# Run tests with pytest
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
