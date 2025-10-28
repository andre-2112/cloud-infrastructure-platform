"""
Deployment ID generation utility

Generates unique deployment IDs in format: D<timestamp-based-code>
Example: D1BRV40
"""

import random
import string
from datetime import datetime


def generate_deployment_id() -> str:
    """
    Generate a unique deployment ID

    Format: D + 6 character alphanumeric code
    Example: D1BRV40

    The ID is generated from:
    - Current timestamp (compressed to base 36)
    - Random component for uniqueness

    Returns:
        str: Deployment ID (e.g., "D1BRV40")
    """
    # Get current timestamp
    timestamp = int(datetime.now().timestamp())

    # Convert to base 36 (0-9, A-Z) and take last 4 chars
    base36_chars = string.digits + string.ascii_uppercase
    timestamp_str = ""
    temp = timestamp
    while temp > 0:
        timestamp_str = base36_chars[temp % 36] + timestamp_str
        temp //= 36

    # Take last 4 characters
    timestamp_part = timestamp_str[-4:]

    # Add 2 random characters for uniqueness
    random_part = "".join(random.choices(string.ascii_uppercase + string.digits, k=2))

    # Combine with D prefix
    deployment_id = f"D{timestamp_part}{random_part}"

    return deployment_id


def validate_deployment_id(deployment_id: str) -> bool:
    """
    Validate deployment ID format

    Args:
        deployment_id: Deployment ID to validate

    Returns:
        bool: True if valid format, False otherwise
    """
    if not deployment_id:
        return False

    # Must start with D
    if not deployment_id.startswith("D"):
        return False

    # Must be exactly 7 characters (D + 6 alphanumeric)
    if len(deployment_id) != 7:
        return False

    # Remaining 6 characters must be alphanumeric
    code = deployment_id[1:]
    if not code.isalnum():
        return False

    return True
