"""
Name Sanitizer

Sanitizes organization and project names for use in filesystem paths,
Pulumi Cloud, and AWS resources.
"""

import re


def sanitize_name(name: str) -> str:
    """
    Sanitize a name by replacing consecutive spaces and special characters with underscores.

    Rules:
    - Replace any sequence of spaces and/or special characters with a single underscore
    - Keep alphanumeric characters as-is
    - Trim leading/trailing underscores

    Examples:
        "My Company!" -> "My_Company"
        "Test   Project  123" -> "Test_Project_123"
        "Org @ Company & Co." -> "Org_Company_Co"
        "  Spaces  " -> "Spaces"

    Args:
        name: Original name string

    Returns:
        Sanitized name string
    """
    if not name:
        return ""

    # Replace consecutive non-alphanumeric characters (including spaces) with single underscore
    sanitized = re.sub(r'[^a-zA-Z0-9]+', '_', name)

    # Remove leading/trailing underscores
    sanitized = sanitized.strip('_')

    return sanitized


def sanitize_org_and_project(organization: str, project: str) -> tuple[str, str]:
    """
    Sanitize both organization and project names.

    Args:
        organization: Original organization name
        project: Original project name

    Returns:
        Tuple of (sanitized_org, sanitized_project)
    """
    return sanitize_name(organization), sanitize_name(project)
