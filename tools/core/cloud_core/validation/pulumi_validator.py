"""
Pulumi Validator

Validates Pulumi CLI and Cloud access.
"""

from typing import List
import subprocess
import os
from ..utils.logger import get_logger

logger = get_logger(__name__)


class PulumiValidator:
    """Validates Pulumi configuration"""

    def __init__(self):
        """Initialize Pulumi validator"""
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate(self) -> bool:
        """
        Validate Pulumi installation and configuration

        Returns:
            True if valid, False otherwise
        """
        self.errors = []
        self.warnings = []

        # Check CLI installed
        if not self._check_cli_installed():
            return False

        # Check access token
        if not self._check_access_token():
            return False

        return True

    def _check_cli_installed(self) -> bool:
        """Check if Pulumi CLI is installed"""
        try:
            result = subprocess.run(
                ["pulumi", "version"],
                capture_output=True,
                text=True,
                check=True,
            )

            version = result.stdout.strip()
            logger.info(f"Pulumi CLI installed: {version}")
            return True

        except FileNotFoundError:
            self.errors.append(
                "Pulumi CLI not found. Install from: https://www.pulumi.com/docs/get-started/install/"
            )
            return False
        except subprocess.CalledProcessError as e:
            self.errors.append(f"Pulumi CLI error: {e}")
            return False

    def _check_access_token(self) -> bool:
        """Check if Pulumi access token is configured"""
        # Check PULUMI_ACCESS_TOKEN environment variable
        access_token = os.getenv("PULUMI_ACCESS_TOKEN")

        if not access_token:
            self.errors.append(
                "PULUMI_ACCESS_TOKEN not set. Run: pulumi login"
            )
            return False

        logger.info("Pulumi access token configured")
        return True

    def get_errors(self) -> List[str]:
        """Get validation errors"""
        return self.errors

    def get_warnings(self) -> List[str]:
        """Get validation warnings"""
        return self.warnings
