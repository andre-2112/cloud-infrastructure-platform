"""Tests for manifest validator"""

import pytest
from pathlib import Path
from cloud_cli.validation.manifest_validator import ManifestValidator, DeploymentManifest
from pydantic import ValidationError


class TestManifestValidator:
    """Test manifest validation"""

    def test_valid_manifest_structure(self):
        """Test validation of valid manifest structure"""
        valid_manifest = {
            "version": "3.1",
            "deployment_id": "D1BRV40",
            "organization": "Company-A",
            "project": "ecommerce",
            "domain": "ecommerce.companyA.com",
            "template": "default",
            "environments": {
                "dev": {
                    "enabled": True,
                    "region": "us-east-1",
                    "account_id": "111111111111",
                }
            },
            "stacks": {
                "network": {
                    "enabled": True,
                    "layer": 1,
                    "dependencies": [],
                    "config": {},
                },
                "security": {
                    "enabled": True,
                    "layer": 2,
                    "dependencies": ["network"],
                    "config": {},
                },
            },
        }

        # Should not raise exception
        manifest = DeploymentManifest(**valid_manifest)
        assert manifest.deployment_id == "D1BRV40"
        assert manifest.organization == "Company-A"

    def test_invalid_deployment_id_format(self):
        """Test validation fails for invalid deployment ID"""
        invalid_manifest = {
            "version": "3.1",
            "deployment_id": "INVALID",  # Invalid format
            "organization": "Company-A",
            "project": "ecommerce",
            "domain": "ecommerce.companyA.com",
            "template": "default",
            "environments": {
                "dev": {
                    "enabled": True,
                    "region": "us-east-1",
                    "account_id": "111111111111",
                }
            },
            "stacks": {},
        }

        with pytest.raises(ValidationError):
            DeploymentManifest(**invalid_manifest)

    def test_invalid_account_id_format(self):
        """Test validation fails for invalid AWS account ID"""
        invalid_manifest = {
            "version": "3.1",
            "deployment_id": "D1BRV40",
            "organization": "Company-A",
            "project": "ecommerce",
            "domain": "ecommerce.companyA.com",
            "template": "default",
            "environments": {
                "dev": {
                    "enabled": True,
                    "region": "us-east-1",
                    "account_id": "12345",  # Too short
                }
            },
            "stacks": {},
        }

        with pytest.raises(ValidationError):
            DeploymentManifest(**invalid_manifest)

    def test_invalid_layer_value(self):
        """Test validation fails for invalid layer value"""
        invalid_manifest = {
            "version": "3.1",
            "deployment_id": "D1BRV40",
            "organization": "Company-A",
            "project": "ecommerce",
            "domain": "ecommerce.companyA.com",
            "template": "default",
            "environments": {
                "dev": {
                    "enabled": True,
                    "region": "us-east-1",
                    "account_id": "111111111111",
                }
            },
            "stacks": {
                "network": {
                    "enabled": True,
                    "layer": 15,  # Out of range (1-10)
                    "dependencies": [],
                    "config": {},
                }
            },
        }

        with pytest.raises(ValidationError):
            DeploymentManifest(**invalid_manifest)

    def test_validator_dependency_check(self):
        """Test validator checks for unknown dependencies"""
        validator = ManifestValidator()

        manifest_data = {
            "version": "3.1",
            "deployment_id": "D1BRV40",
            "organization": "Company-A",
            "project": "ecommerce",
            "domain": "ecommerce.companyA.com",
            "template": "default",
            "environments": {
                "dev": {
                    "enabled": True,
                    "region": "us-east-1",
                    "account_id": "111111111111",
                }
            },
            "stacks": {
                "security": {
                    "enabled": True,
                    "layer": 2,
                    "dependencies": ["network"],  # network doesn't exist
                    "config": {},
                }
            },
        }

        # Use validator's internal method
        validator._validate_dependencies(manifest_data)
        assert len(validator.errors) > 0
        assert "unknown stack" in validator.errors[0].lower()
