"""
AWS Query Resolver

Resolves runtime values by querying AWS.
Handles placeholders like: {{aws.vpc.default}}, {{aws.account.id}}
"""

from typing import Dict, Any, Optional
import boto3
from botocore.exceptions import ClientError, BotoCoreError

from ..utils.logger import get_logger

logger = get_logger(__name__)


class AWSQueryResolver:
    """Resolves values by querying AWS"""

    def __init__(self, region: str = "us-east-1"):
        """
        Initialize AWS query resolver

        Args:
            region: AWS region for queries
        """
        self.region = region
        self.cache: Dict[str, Any] = {}

        # AWS clients (lazy loaded)
        self._ec2_client = None
        self._sts_client = None

    @property
    def ec2_client(self):
        """Get EC2 client (lazy loaded)"""
        if self._ec2_client is None:
            self._ec2_client = boto3.client("ec2", region_name=self.region)
        return self._ec2_client

    @property
    def sts_client(self):
        """Get STS client (lazy loaded)"""
        if self._sts_client is None:
            self._sts_client = boto3.client("sts")
        return self._sts_client

    def resolve(self, placeholder: str) -> Optional[Any]:
        """
        Resolve AWS query placeholder

        Args:
            placeholder: Placeholder in format "aws.{service}.{query}"
                        E.g., "aws.vpc.default", "aws.account.id"

        Returns:
            Resolved value, or None if not found
        """
        # Check cache first
        # Handle None or non-string input
        if placeholder is None or not isinstance(placeholder, str):
            return None

        if placeholder in self.cache:
            logger.debug(f"Resolved {placeholder} from cache")
            return self.cache[placeholder]

        # Parse placeholder
        if not placeholder.startswith("aws."):
            return None

        parts = placeholder.split(".", 2)

        if len(parts) < 3:
            logger.warning(f"Invalid AWS query format: {placeholder}")
            return None

        service = parts[1]
        query = parts[2]

        # Route to appropriate query handler
        value = None

        if service == "vpc":
            value = self._query_vpc(query)
        elif service == "account":
            value = self._query_account(query)
        elif service == "region":
            value = self._query_region(query)
        else:
            logger.warning(f"Unsupported AWS service in query: {service}")

        if value is not None:
            # Cache the result
            self.cache[placeholder] = value
            logger.debug(f"Resolved {placeholder} = {value}")

        return value

    def _query_vpc(self, query: str) -> Optional[str]:
        """
        Query VPC information

        Supported queries:
        - default: Get default VPC ID

        Args:
            query: Query type

        Returns:
            Query result, or None
        """
        try:
            if query == "default":
                # Get default VPC
                response = self.ec2_client.describe_vpcs(
                    Filters=[{"Name": "isDefault", "Values": ["true"]}]
                )

                vpcs = response.get("Vpcs", [])
                if vpcs:
                    return vpcs[0]["VpcId"]
                else:
                    logger.warning("No default VPC found")
                    return None

            else:
                logger.warning(f"Unsupported VPC query: {query}")
                return None

        except (ClientError, BotoCoreError) as e:
            logger.error(f"Error querying VPC: {e}")
            return None

    def _query_account(self, query: str) -> Optional[str]:
        """
        Query account information

        Supported queries:
        - id: Get current AWS account ID

        Args:
            query: Query type

        Returns:
            Query result, or None
        """
        try:
            if query == "id":
                # Get account ID from STS
                response = self.sts_client.get_caller_identity()
                return response.get("Account")

            else:
                logger.warning(f"Unsupported account query: {query}")
                return None

        except (ClientError, BotoCoreError) as e:
            logger.error(f"Error querying account: {e}")
            return None

    def _query_region(self, query: str) -> Optional[str]:
        """
        Query region information

        Supported queries:
        - current: Get current region

        Args:
            query: Query type

        Returns:
            Query result, or None
        """
        if query == "current":
            return self.region
        else:
            logger.warning(f"Unsupported region query: {query}")
            return None

    def clear_cache(self) -> None:
        """Clear the resolution cache"""
        self.cache.clear()
        logger.debug("Cleared AWS query cache")

    def list_available_queries(self) -> Dict[str, list]:
        """
        List available AWS queries

        Returns:
            Dictionary of service -> [available queries]
        """
        return {
            "vpc": ["default"],
            "account": ["id"],
            "region": ["current"],
        }

    def is_aws_query(self, placeholder: str) -> bool:
        """
        Check if placeholder is an AWS query

        Args:
            placeholder: Placeholder to check

        Returns:
            True if AWS query format
        """
        return placeholder.startswith("aws.") and len(placeholder.split(".")) >= 3

    def test_aws_credentials(self) -> bool:
        """
        Test if AWS credentials are configured and valid

        Returns:
            True if credentials valid, False otherwise
        """
        try:
            self.sts_client.get_caller_identity()
            return True
        except Exception as e:
            logger.error(f"AWS credentials test failed: {e}")
            return False

    def get_current_account_id(self) -> Optional[str]:
        """
        Get current AWS account ID

        Returns:
            Account ID, or None if error
        """
        return self.resolve("aws.account.id")

    def get_default_vpc_id(self) -> Optional[str]:
        """
        Get default VPC ID in current region

        Returns:
            VPC ID, or None if not found
        """
        return self.resolve("aws.vpc.default")
