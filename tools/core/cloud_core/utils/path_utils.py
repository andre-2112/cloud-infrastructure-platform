"""
Path utilities for finding the cloud root directory from anywhere.

Provides functions to locate the cloud root regardless of current working directory.
"""

import os
from pathlib import Path
from typing import Optional


def find_cloud_root() -> Path:
    """
    Find the cloud root directory by searching for marker directories.

    Searches upward from current directory, then checks common locations.

    Returns:
        Path to cloud root directory

    Raises:
        RuntimeError: If cloud root cannot be found
    """
    # First check if CLOUD_ROOT environment variable is set
    cloud_root_env = os.environ.get('CLOUD_ROOT')
    if cloud_root_env:
        cloud_root = Path(cloud_root_env)
        if _is_cloud_root(cloud_root):
            return cloud_root

    # Check current directory and parents
    current = Path.cwd()
    for parent in [current] + list(current.parents):
        if _is_cloud_root(parent):
            return parent
        # Also check if we're in a subdirectory like tools/cli
        cloud_candidate = parent / "cloud"
        if cloud_candidate.exists() and _is_cloud_root(cloud_candidate):
            return cloud_candidate

    # Check common workspace locations
    workspace_paths = [
        Path.cwd(),
        Path.home() / "Documents" / "Workspace" / "cloud",
        Path("/c/Users/Admin/Documents/Workspace/cloud"),  # Windows Git Bash
        Path("C:/Users/Admin/Documents/Workspace/cloud"),  # Windows
        Path.home() / "workspace" / "cloud",
        Path.home() / "cloud",
    ]

    for path in workspace_paths:
        if path.exists() and _is_cloud_root(path):
            return path

    raise RuntimeError(
        "Could not find cloud root directory. "
        "Please run from within the cloud directory or set CLOUD_ROOT environment variable."
    )


def _is_cloud_root(path: Path) -> bool:
    """
    Check if a directory is the cloud root.

    Args:
        path: Directory to check

    Returns:
        True if this is the cloud root directory
    """
    # Check for marker directories that should exist in cloud root
    markers = ["stacks", "deploy", "tools"]
    return all((path / marker).exists() for marker in markers)


def get_tools_dir() -> Path:
    """Get the tools directory path."""
    return find_cloud_root() / "tools"


def get_templates_dir() -> Path:
    """Get the templates directory path."""
    return get_tools_dir() / "templates"


def get_stacks_dir() -> Path:
    """Get the stacks directory path."""
    return find_cloud_root() / "stacks"


def get_deploy_dir() -> Path:
    """Get the deploy directory path."""
    return find_cloud_root() / "deploy"
