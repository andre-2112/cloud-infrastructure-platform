"""Pytest configuration and fixtures for core tests"""

import pytest


@pytest.fixture
def sample_manifest():
    """Sample deployment manifest for testing"""
    return {
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
                "config": {
                    "vpcCidr": "10.0.0.0/16",
                },
            },
            "security": {
                "enabled": True,
                "dependencies": ["network"],
                "priority": 200,
                "config": {},
            },
        },
    }


@pytest.fixture
def sample_dependency_graph():
    """Sample dependency graph for testing"""
    return {
        "network": [],
        "security": ["network"],
        "database": ["network", "security"],
        "app": ["database"],
    }
