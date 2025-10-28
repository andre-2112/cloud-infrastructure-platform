"""Tests for ManifestValidator"""

import pytest
import tempfile
import yaml
from pathlib import Path
from cloud_core.validation.manifest_validator import ManifestValidator


@pytest.fixture
def valid_manifest_file():
    """Create a valid manifest file"""
    manifest = {
        "deployment": {
            "id": "D1BRV40",
            "org": "TestOrg",
            "project": "test-project",
            "domain": "test.com",
            "region": "us-east-1",
        },
        "environments": ["dev", "stage", "prod"],
        "stacks": {
            "network": {
                "enabled": True,
                "dependencies": [],
                "priority": 100,
                "config": {},
            }
        },
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(manifest, f)
        return f.name


@pytest.fixture
def invalid_manifest_file():
    """Create an invalid manifest file"""
    manifest = {
        "deployment": {
            # Missing required fields
            "id": "D1BRV40",
        },
        # Missing stacks
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(manifest, f)
        return f.name


def test_manifest_validator_valid(valid_manifest_file):
    """Test validation of valid manifest"""
    validator = ManifestValidator()
    assert validator.validate(valid_manifest_file) is True
    assert len(validator.errors) == 0
    assert validator.manifest is not None


def test_manifest_validator_invalid(invalid_manifest_file):
    """Test validation of invalid manifest"""
    validator = ManifestValidator()
    assert validator.validate(invalid_manifest_file) is False
    assert len(validator.errors) > 0


def test_manifest_validator_file_not_found():
    """Test validation with non-existent file"""
    validator = ManifestValidator()
    assert validator.validate("/nonexistent/file.yaml") is False
    assert len(validator.errors) > 0


def test_manifest_validator_required_fields():
    """Test that required fields are checked"""
    manifest = {
        "deployment": {
            "id": "D1BRV40",
            # Missing org, project, domain, region
        },
        "stacks": {},
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(manifest, f)
        validator = ManifestValidator()
        assert validator.validate(f.name) is False


@pytest.fixture(scope="module", autouse=True)
def cleanup():
    """Cleanup temp files"""
    yield
    # Cleanup happens after tests
