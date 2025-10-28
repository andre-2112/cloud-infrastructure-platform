"""Tests for deployment_id utility"""

import pytest
from cloud_core.utils.deployment_id import generate_deployment_id, validate_deployment_id


def test_generate_deployment_id():
    """Test generating deployment ID"""
    deployment_id = generate_deployment_id()

    # Should start with D
    assert deployment_id.startswith("D")

    # Should be exactly 7 characters
    assert len(deployment_id) == 7

    # Should be alphanumeric
    assert deployment_id[1:].isalnum()


def test_generate_deployment_id_uniqueness():
    """Test that generated IDs are unique"""
    ids = set()
    for _ in range(100):
        deployment_id = generate_deployment_id()
        ids.add(deployment_id)

    # Should have generated 100 unique IDs
    # (With 2 random chars, collision is extremely unlikely)
    assert len(ids) >= 95  # Allow small chance of collision


def test_validate_deployment_id_valid():
    """Test validating valid deployment ID"""
    assert validate_deployment_id("D1BRV40") is True
    assert validate_deployment_id("DABC123") is True
    assert validate_deployment_id("D000000") is True


def test_validate_deployment_id_empty():
    """Test validating empty string"""
    assert validate_deployment_id("") is False


def test_validate_deployment_id_none():
    """Test validating None"""
    assert validate_deployment_id(None) is False


def test_validate_deployment_id_wrong_prefix():
    """Test validation with wrong prefix"""
    assert validate_deployment_id("X1BRV40") is False
    assert validate_deployment_id("1BRV40") is False


def test_validate_deployment_id_wrong_length():
    """Test validation with wrong length"""
    assert validate_deployment_id("D1BRV") is False  # Too short
    assert validate_deployment_id("D1BRV400") is False  # Too long
    assert validate_deployment_id("D") is False


def test_validate_deployment_id_non_alphanumeric():
    """Test validation with non-alphanumeric characters"""
    assert validate_deployment_id("D1BRV-0") is False
    assert validate_deployment_id("D1BRV_0") is False
    assert validate_deployment_id("D1BRV!0") is False


def test_generate_and_validate():
    """Test that generated IDs are valid"""
    for _ in range(10):
        deployment_id = generate_deployment_id()
        assert validate_deployment_id(deployment_id) is True
