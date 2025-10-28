"""
AWS Validator

Validates AWS credentials and permissions.
"""

from typing import List
import boto3
from botocore.exceptions import ClientError, BotoCoreError, NoCredentialsError
from ..utils.logger import get_logger

logger = get_logger(__name__)


class AWSValidator:
    """Validates AWS configuration"""

    def __init__(self):
        """Initialize AWS validator"""
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate(self) -> bool:
        """
        Validate AWS credentials and basic permissions

        Returns:
            True if valid, False otherwise
        """
        self.errors = []
        self.warnings = []

        # Check credentials
        if not self._check_credentials():
            return False

        # Check basic permissions
        if not self._check_basic_permissions():
            return False

        return True

    def _check_credentials(self) -> bool:
        """Check if AWS credentials are configured"""
        try:
            sts = boto3.client("sts")
            identity = sts.get_caller_identity()

            account_id = identity.get("Account")
            user_arn = identity.get("Arn")

            logger.info(f"AWS credentials valid: Account {account_id}, User {user_arn}")
            return True

        except NoCredentialsError:
            self.errors.append("AWS credentials not configured")
            return False
        except ClientError as e:
            self.errors.append(f"AWS credential error: {e}")
            return False
        except Exception as e:
            self.errors.append(f"Unexpected AWS error: {e}")
            return False

    def _check_basic_permissions(self) -> bool:
        """Check basic AWS permissions"""
        try:
            # Try to list S3 buckets (basic permission check)
            s3 = boto3.client("s3")
            s3.list_buckets()

            logger.info("AWS permissions check passed")
            return True

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            if error_code == "AccessDenied":
                self.warnings.append("Limited AWS permissions detected")
                # Still return True - not a hard error
                return True
            else:
                self.errors.append(f"AWS permission error: {e}")
                return False
        except Exception as e:
            self.warnings.append(f"Could not verify AWS permissions: {e}")
            return True  # Warning only

    def get_errors(self) -> List[str]:
        """Get validation errors"""
        return self.errors

    def get_warnings(self) -> List[str]:
        """Get validation warnings"""
        return self.warnings

    def get_account_id(self) -> str:
        """
        Get current AWS account ID

        Returns:
            Account ID, or empty string if error
        """
        try:
            sts = boto3.client("sts")
            identity = sts.get_caller_identity()
            return identity.get("Account", "")
        except Exception:
            return ""
