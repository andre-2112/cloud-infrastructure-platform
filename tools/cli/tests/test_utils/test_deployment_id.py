"""Tests for deployment ID utility"""

import pytest
from cloud_cli.utils.deployment_id import generate_deployment_id, validate_deployment_id


class TestDeploymentIdGeneration:
    """Test deployment ID generation"""

    def test_generate_deployment_id_format(self):
        """Test that generated ID has correct format"""
        deployment_id = generate_deployment_id()

        # Should start with D
        assert deployment_id.startswith("D")

        # Should be exactly 7 characters
        assert len(deployment_id) == 7

        # Should be alphanumeric
        assert deployment_id[1:].isalnum()

    def test_generate_deployment_id_uniqueness(self):
        """Test that generated IDs are unique"""
        ids = {generate_deployment_id() for _ in range(100)}

        # All IDs should be unique
        assert len(ids) == 100

    def test_validate_deployment_id_valid(self):
        """Test validation of valid deployment IDs"""
        valid_ids = [
            "D1BRV40",
            "DABC123",
            "D000000",
            "DZZZZZZ",
        ]

        for deployment_id in valid_ids:
            assert validate_deployment_id(deployment_id), f"{deployment_id} should be valid"

    def test_validate_deployment_id_invalid(self):
        """Test validation of invalid deployment IDs"""
        invalid_ids = [
            "",  # Empty
            "D",  # Too short
            "D1BRV4",  # Too short
            "D1BRV400",  # Too long
            "1BRV40",  # Missing D prefix
            "d1BRV40",  # Lowercase D
            "D1BRV4!",  # Special character
            "D 1BRV4",  # Space
            None,  # None
        ]

        for deployment_id in invalid_ids:
            assert not validate_deployment_id(deployment_id), f"{deployment_id} should be invalid"


class TestDeploymentIdValidation:
    """Test deployment ID validation"""

    def test_validate_generated_ids(self):
        """Test that all generated IDs are valid"""
        for _ in range(50):
            deployment_id = generate_deployment_id()
            assert validate_deployment_id(deployment_id)
