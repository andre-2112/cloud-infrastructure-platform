"""
AWS Error Handler

Detects and provides user-friendly messages for AWS service limit errors.
"""

import re
from typing import Optional, Dict, Tuple
from pathlib import Path
from datetime import datetime


class AWSLimitError:
    """Represents an AWS service limit error with remediation guidance"""

    def __init__(
        self,
        service: str,
        resource: str,
        limit_type: str,
        message: str,
        remediation: str,
        aws_docs_url: Optional[str] = None
    ):
        self.service = service
        self.resource = resource
        self.limit_type = limit_type
        self.message = message
        self.remediation = remediation
        self.aws_docs_url = aws_docs_url

    def format_error(self) -> str:
        """Format a user-friendly error message"""
        lines = [
            "",
            "=" * 80,
            f"AWS LIMIT EXCEEDED: {self.service} - {self.resource}",
            "=" * 80,
            "",
            f"Error: {self.message}",
            "",
            "What this means:",
            f"  Your AWS account has reached the limit for {self.limit_type}.",
            "",
            "How to fix this:",
        ]

        for line in self.remediation.split('\n'):
            lines.append(f"  {line}")

        if self.aws_docs_url:
            lines.extend([
                "",
                "AWS Documentation:",
                f"  {self.aws_docs_url}"
            ])

        lines.extend([
            "",
            "=" * 80,
            ""
        ])

        return '\n'.join(lines)


# AWS limit error patterns and remediation guidance
AWS_LIMIT_PATTERNS: Dict[str, Dict] = {
    "VpcLimitExceeded": {
        "service": "VPC",
        "resource": "Virtual Private Clouds",
        "limit_type": "VPCs per region",
        "pattern": r"VpcLimitExceeded|maximum number of VPCs has been reached",
        "remediation": """1. Delete unused VPCs in your AWS account
   - Go to AWS Console > VPC > Your VPCs
   - Identify VPCs that are no longer needed
   - Delete them (ensure no resources are attached)

2. Request a limit increase from AWS
   - Go to AWS Service Quotas console
   - Search for "VPC"
   - Request an increase for "VPCs per Region"
   - Default limit: 5 VPCs per region

3. Use existing VPCs for new deployments
   - Consider reusing VPCs across deployments
   - Update your deployment configuration""",
        "docs": "https://docs.aws.amazon.com/vpc/latest/userguide/amazon-vpc-limits.html"
    },

    "AddressLimitExceeded": {
        "service": "EC2",
        "resource": "Elastic IP Addresses",
        "limit_type": "Elastic IPs per region",
        "pattern": r"AddressLimitExceeded|maximum number of addresses has been reached",
        "remediation": """1. Release unused Elastic IPs
   - Go to AWS Console > EC2 > Elastic IPs
   - Identify IPs not associated with running instances
   - Release them

2. Request a limit increase from AWS
   - Go to AWS Service Quotas console
   - Search for "Elastic IP"
   - Request an increase for "EC2-VPC Elastic IPs"
   - Default limit: 5 EIPs per region

3. Optimize NAT Gateway usage
   - Consider using fewer NAT Gateways
   - Share NAT Gateways across availability zones""",
        "docs": "https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/elastic-ip-addresses-eip.html"
    },

    "NatGatewayLimitExceeded": {
        "service": "VPC",
        "resource": "NAT Gateways",
        "limit_type": "NAT Gateways per availability zone",
        "pattern": r"NatGatewayLimitExceeded|maximum number of NAT gateways",
        "remediation": """1. Delete unused NAT Gateways
   - Go to AWS Console > VPC > NAT Gateways
   - Identify NAT Gateways not in use
   - Delete them

2. Consolidate NAT Gateways
   - Use one NAT Gateway per AZ instead of multiple
   - Share NAT Gateways across private subnets

3. Request a limit increase from AWS
   - Go to AWS Service Quotas console
   - Search for "NAT Gateway"
   - Request an increase
   - Default limit: 5 NAT Gateways per AZ""",
        "docs": "https://docs.aws.amazon.com/vpc/latest/userguide/vpc-nat-gateway.html"
    },

    "SecurityGroupLimitExceeded": {
        "service": "EC2",
        "resource": "Security Groups",
        "limit_type": "Security Groups per VPC",
        "pattern": r"SecurityGroupLimitExceeded|maximum number of security groups",
        "remediation": """1. Clean up unused Security Groups
   - Go to AWS Console > EC2 > Security Groups
   - Identify Security Groups with no attached resources
   - Delete them

2. Consolidate Security Group rules
   - Combine similar Security Groups
   - Use fewer, more general Security Groups where appropriate

3. Request a limit increase from AWS
   - Go to AWS Service Quotas console
   - Search for "Security Groups"
   - Request an increase for "Security groups per VPC"
   - Default limit: 2,500 per VPC""",
        "docs": "https://docs.aws.amazon.com/vpc/latest/userguide/amazon-vpc-limits.html"
    },

    "RulesPerSecurityGroupLimitExceeded": {
        "service": "EC2",
        "resource": "Security Group Rules",
        "limit_type": "Rules per Security Group",
        "pattern": r"RulesPerSecurityGroupLimitExceeded|maximum number of rules",
        "remediation": """1. Reduce rules in Security Groups
   - Review and remove unnecessary rules
   - Use CIDR blocks instead of individual IPs

2. Split rules across multiple Security Groups
   - Attach multiple Security Groups to resources
   - Each can have its own set of rules

3. Request a limit increase from AWS
   - Go to AWS Service Quotas console
   - Search for "Security Group Rules"
   - Request an increase
   - Default limit: 60 inbound + 60 outbound rules""",
        "docs": "https://docs.aws.amazon.com/vpc/latest/userguide/amazon-vpc-limits.html"
    },

    "DBInstanceLimitExceeded": {
        "service": "RDS",
        "resource": "Database Instances",
        "limit_type": "DB Instances per region",
        "pattern": r"DBInstanceLimitExceeded|maximum number of DB instances",
        "remediation": """1. Delete unused RDS instances
   - Go to AWS Console > RDS > Databases
   - Identify unused database instances
   - Take final snapshots if needed, then delete

2. Consolidate databases
   - Use multi-database instances where possible
   - Consider database per schema instead of per instance

3. Request a limit increase from AWS
   - Go to AWS Service Quotas console
   - Search for "RDS"
   - Request an increase for "DB instances"
   - Default limit: 40 instances per region""",
        "docs": "https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_Limits.html"
    },

    "RepositoryLimitExceeded": {
        "service": "ECR",
        "resource": "Container Repositories",
        "limit_type": "Repositories per region",
        "pattern": r"RepositoryLimitExceeded|maximum number of repositories",
        "remediation": """1. Delete unused ECR repositories
   - Go to AWS Console > ECR > Repositories
   - Identify repositories no longer in use
   - Delete them

2. Consolidate images
   - Use fewer repositories with more images per repository
   - Consider using image tags instead of separate repos

3. Request a limit increase from AWS
   - Go to AWS Service Quotas console
   - Search for "ECR"
   - Request an increase for "Repositories"
   - Default limit: 10,000 per region""",
        "docs": "https://docs.aws.amazon.com/AmazonECR/latest/userguide/service-quotas.html"
    },

    "LimitExceededException": {
        "service": "Lambda",
        "resource": "Lambda Functions",
        "limit_type": "Lambda service limits",
        "pattern": r"LimitExceededException.*Lambda",
        "remediation": """1. Review Lambda function limits
   - Check concurrent execution limit
   - Review function storage usage
   - Check unreserved concurrent executions

2. Clean up unused Lambda functions
   - Go to AWS Console > Lambda > Functions
   - Delete functions no longer in use

3. Request a limit increase from AWS
   - Go to AWS Service Quotas console
   - Search for "Lambda"
   - Request appropriate limit increase""",
        "docs": "https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html"
    },

    "ClusterQuotaExceeded": {
        "service": "ECS",
        "resource": "ECS Clusters/Services",
        "limit_type": "ECS service limits",
        "pattern": r"ClusterQuotaExceeded|ECS.*LimitExceeded",
        "remediation": """1. Clean up unused ECS resources
   - Go to AWS Console > ECS
   - Stop unused services
   - Delete empty clusters

2. Consolidate ECS services
   - Use fewer services with more tasks
   - Share clusters across applications

3. Request a limit increase from AWS
   - Go to AWS Service Quotas console
   - Search for "ECS"
   - Request appropriate limit increase""",
        "docs": "https://docs.aws.amazon.com/AmazonECS/latest/developerguide/service-quotas.html"
    }
}


class AWSErrorHandler:
    """Handles AWS error detection and formatting"""

    @staticmethod
    def detect_aws_limit_error(error_message: str) -> Optional[AWSLimitError]:
        """
        Detect if an error message indicates an AWS limit was exceeded

        Args:
            error_message: The error message to analyze

        Returns:
            AWSLimitError if a limit error was detected, None otherwise
        """
        error_lower = error_message.lower()

        for error_type, config in AWS_LIMIT_PATTERNS.items():
            if re.search(config["pattern"], error_message, re.IGNORECASE):
                return AWSLimitError(
                    service=config["service"],
                    resource=config["resource"],
                    limit_type=config["limit_type"],
                    message=error_message,
                    remediation=config["remediation"],
                    aws_docs_url=config.get("docs")
                )

        # Generic AWS limit error detection
        if any(pattern in error_lower for pattern in [
            "limit exceeded", "limitexceeded", "quota exceeded",
            "maximum number", "too many", "insufficient capacity"
        ]):
            return AWSLimitError(
                service="AWS",
                resource="Unknown Resource",
                limit_type="service limit",
                message=error_message,
                remediation="""1. Review the error message for specific service and resource
2. Check AWS Service Quotas console for current limits
3. Delete unused resources or request a limit increase
4. Contact AWS Support for assistance""",
                aws_docs_url="https://docs.aws.amazon.com/general/latest/gr/aws_service_limits.html"
            )

        return None

    @staticmethod
    def format_deployment_error(
        error_message: str,
        deployment_id: str,
        stack_name: Optional[str] = None,
        environment: Optional[str] = None
    ) -> str:
        """
        Format a deployment error with context

        Args:
            error_message: The error message
            deployment_id: Deployment ID
            stack_name: Stack name (optional)
            environment: Environment (optional)

        Returns:
            Formatted error message
        """
        # Check if it's an AWS limit error
        aws_error = AWSErrorHandler.detect_aws_limit_error(error_message)

        if aws_error:
            return aws_error.format_error()

        # Generic error formatting
        context_parts = [f"Deployment: {deployment_id}"]
        if stack_name:
            context_parts.append(f"Stack: {stack_name}")
        if environment:
            context_parts.append(f"Environment: {environment}")

        context = " | ".join(context_parts)

        return f"""
{"=" * 80}
DEPLOYMENT ERROR
{"=" * 80}

Context: {context}

Error: {error_message}

{"=" * 80}
"""

    @staticmethod
    def log_error_to_deployment(
        error_message: str,
        deployment_dir: Path,
        deployment_id: str,
        stack_name: Optional[str] = None,
        environment: Optional[str] = None,
        operation: str = "deploy"
    ) -> None:
        """
        Log an error to the deployment directory

        Args:
            error_message: The error message
            deployment_dir: Path to deployment directory
            deployment_id: Deployment ID
            stack_name: Stack name (optional)
            environment: Environment (optional)
            operation: Operation type (deploy, destroy, etc.)
        """
        # Create logs directory if it doesn't exist
        logs_dir = deployment_dir / "logs"
        logs_dir.mkdir(exist_ok=True)

        # Create error log file with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = logs_dir / f"error_{operation}_{timestamp}.log"

        # Format the error
        formatted_error = AWSErrorHandler.format_deployment_error(
            error_message, deployment_id, stack_name, environment
        )

        # Write to log file
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            f.write(f"Operation: {operation}\n")
            f.write(f"Deployment ID: {deployment_id}\n")
            if stack_name:
                f.write(f"Stack: {stack_name}\n")
            if environment:
                f.write(f"Environment: {environment}\n")
            f.write("\n")
            f.write(formatted_error)
            f.write("\n")
            f.write("Full Error Message:\n")
            f.write(error_message)
