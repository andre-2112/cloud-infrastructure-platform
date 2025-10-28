"""Tests for AWSQueryResolver"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError
from cloud_core.runtime.aws_query_resolver import AWSQueryResolver


def test_aws_query_resolver_init():
    """Test AWSQueryResolver initialization"""
    resolver = AWSQueryResolver(region="us-west-2")
    assert resolver.region == "us-west-2"
    assert resolver.cache == {}
    assert resolver._ec2_client is None
    assert resolver._sts_client is None


def test_lazy_client_loading():
    """Test that AWS clients are lazy loaded"""
    resolver = AWSQueryResolver()

    # Clients should not be created initially
    assert resolver._ec2_client is None
    assert resolver._sts_client is None

    # Access should trigger creation
    with patch('boto3.client') as mock_boto:
        mock_boto.return_value = Mock()

        _ = resolver.ec2_client
        assert mock_boto.called

        _ = resolver.sts_client
        assert mock_boto.call_count == 2


@patch('boto3.client')
def test_resolve_vpc_default(mock_boto_client):
    """Test resolving default VPC"""
    resolver = AWSQueryResolver()

    # Mock EC2 client
    mock_ec2 = Mock()
    mock_ec2.describe_vpcs.return_value = {
        "Vpcs": [{"VpcId": "vpc-12345"}]
    }
    mock_boto_client.return_value = mock_ec2

    result = resolver.resolve("aws.vpc.default")

    assert result == "vpc-12345"
    mock_ec2.describe_vpcs.assert_called_once()


@patch('boto3.client')
def test_resolve_vpc_default_not_found(mock_boto_client):
    """Test resolving default VPC when none exists"""
    resolver = AWSQueryResolver()

    # Mock EC2 client with empty response
    mock_ec2 = Mock()
    mock_ec2.describe_vpcs.return_value = {"Vpcs": []}
    mock_boto_client.return_value = mock_ec2

    result = resolver.resolve("aws.vpc.default")

    assert result is None


@patch('boto3.client')
def test_resolve_account_id(mock_boto_client):
    """Test resolving AWS account ID"""
    resolver = AWSQueryResolver()

    # Mock STS client
    mock_sts = Mock()
    mock_sts.get_caller_identity.return_value = {
        "Account": "123456789012"
    }
    mock_boto_client.return_value = mock_sts

    result = resolver.resolve("aws.account.id")

    assert result == "123456789012"
    mock_sts.get_caller_identity.assert_called_once()


@patch('boto3.client')
def test_resolve_region_current(mock_boto_client):
    """Test resolving current region"""
    resolver = AWSQueryResolver(region="us-east-1")

    result = resolver.resolve("aws.region.current")

    assert result == "us-east-1"


def test_resolve_invalid_format():
    """Test resolving with invalid format"""
    resolver = AWSQueryResolver()

    result = resolver.resolve("invalid.format")

    assert result is None


def test_resolve_invalid_aws_format():
    """Test resolving with invalid AWS query format"""
    resolver = AWSQueryResolver()

    result = resolver.resolve("aws.invalid")

    assert result is None


def test_resolve_unsupported_service():
    """Test resolving unsupported AWS service"""
    resolver = AWSQueryResolver()

    result = resolver.resolve("aws.unsupported.query")

    assert result is None


def test_resolve_unsupported_vpc_query():
    """Test resolving unsupported VPC query"""
    resolver = AWSQueryResolver()

    result = resolver.resolve("aws.vpc.unsupported")

    assert result is None


def test_resolve_unsupported_account_query():
    """Test resolving unsupported account query"""
    resolver = AWSQueryResolver()

    result = resolver.resolve("aws.account.unsupported")

    assert result is None


def test_resolve_unsupported_region_query():
    """Test resolving unsupported region query"""
    resolver = AWSQueryResolver()

    result = resolver.resolve("aws.region.unsupported")

    assert result is None


@patch('boto3.client')
def test_caching(mock_boto_client):
    """Test that resolved values are cached"""
    resolver = AWSQueryResolver()

    mock_sts = Mock()
    mock_sts.get_caller_identity.return_value = {
        "Account": "123456789012"
    }
    mock_boto_client.return_value = mock_sts

    # First call
    result1 = resolver.resolve("aws.account.id")

    # Second call should use cache
    result2 = resolver.resolve("aws.account.id")

    assert result1 == result2
    # Should only call AWS once due to caching
    mock_sts.get_caller_identity.assert_called_once()


def test_clear_cache():
    """Test clearing cache"""
    resolver = AWSQueryResolver()
    resolver.cache["test.key"] = "test.value"

    assert len(resolver.cache) > 0

    resolver.clear_cache()

    assert len(resolver.cache) == 0


def test_list_available_queries():
    """Test listing available queries"""
    resolver = AWSQueryResolver()

    queries = resolver.list_available_queries()

    assert "vpc" in queries
    assert "account" in queries
    assert "region" in queries
    assert "default" in queries["vpc"]
    assert "id" in queries["account"]
    assert "current" in queries["region"]


def test_is_aws_query():
    """Test checking if placeholder is AWS query"""
    resolver = AWSQueryResolver()

    assert resolver.is_aws_query("aws.vpc.default")
    assert resolver.is_aws_query("aws.account.id")
    assert not resolver.is_aws_query("deployment.id")
    assert not resolver.is_aws_query("aws.invalid")


@patch('boto3.client')
def test_test_aws_credentials_success(mock_boto_client):
    """Test testing AWS credentials successfully"""
    resolver = AWSQueryResolver()

    mock_sts = Mock()
    mock_sts.get_caller_identity.return_value = {"Account": "123"}
    mock_boto_client.return_value = mock_sts

    result = resolver.test_aws_credentials()

    assert result is True


@patch('boto3.client')
def test_test_aws_credentials_failure(mock_boto_client):
    """Test testing AWS credentials with failure"""
    resolver = AWSQueryResolver()

    mock_sts = Mock()
    mock_sts.get_caller_identity.side_effect = ClientError(
        {"Error": {"Code": "AccessDenied", "Message": "Access denied"}},
        "GetCallerIdentity"
    )
    mock_boto_client.return_value = mock_sts

    result = resolver.test_aws_credentials()

    assert result is False


@patch('boto3.client')
def test_get_current_account_id(mock_boto_client):
    """Test convenience method for getting account ID"""
    resolver = AWSQueryResolver()

    mock_sts = Mock()
    mock_sts.get_caller_identity.return_value = {
        "Account": "123456789012"
    }
    mock_boto_client.return_value = mock_sts

    account_id = resolver.get_current_account_id()

    assert account_id == "123456789012"


@patch('boto3.client')
def test_get_default_vpc_id(mock_boto_client):
    """Test convenience method for getting default VPC ID"""
    resolver = AWSQueryResolver()

    mock_ec2 = Mock()
    mock_ec2.describe_vpcs.return_value = {
        "Vpcs": [{"VpcId": "vpc-12345"}]
    }
    mock_boto_client.return_value = mock_ec2

    vpc_id = resolver.get_default_vpc_id()

    assert vpc_id == "vpc-12345"


@patch('boto3.client')
def test_aws_error_handling(mock_boto_client):
    """Test handling AWS API errors"""
    resolver = AWSQueryResolver()

    mock_ec2 = Mock()
    mock_ec2.describe_vpcs.side_effect = ClientError(
        {"Error": {"Code": "UnauthorizedOperation", "Message": "Not authorized"}},
        "DescribeVpcs"
    )
    mock_boto_client.return_value = mock_ec2

    result = resolver.resolve("aws.vpc.default")

    assert result is None


@patch('boto3.client')
def test_multiple_regions(mock_boto_client):
    """Test using different regions"""
    resolver1 = AWSQueryResolver(region="us-east-1")
    resolver2 = AWSQueryResolver(region="us-west-2")

    assert resolver1.resolve("aws.region.current") == "us-east-1"
    assert resolver2.resolve("aws.region.current") == "us-west-2"


def test_cache_isolation():
    """Test that cache is isolated per instance"""
    resolver1 = AWSQueryResolver()
    resolver2 = AWSQueryResolver()

    resolver1.cache["test"] = "value1"
    resolver2.cache["test"] = "value2"

    assert resolver1.cache["test"] == "value1"
    assert resolver2.cache["test"] == "value2"


@patch('boto3.client')
def test_resolve_non_string_placeholder(mock_boto_client):
    """Test resolving non-string placeholder"""
    resolver = AWSQueryResolver()

    # Should handle gracefully
    result = resolver.resolve(None)
    assert result is None


@patch('boto3.client')
def test_vpc_query_with_filters(mock_boto_client):
    """Test VPC query uses correct filters"""
    resolver = AWSQueryResolver()

    mock_ec2 = Mock()
    mock_ec2.describe_vpcs.return_value = {
        "Vpcs": [{"VpcId": "vpc-12345"}]
    }
    mock_boto_client.return_value = mock_ec2

    resolver.resolve("aws.vpc.default")

    # Verify correct filter was used
    mock_ec2.describe_vpcs.assert_called_once_with(
        Filters=[{"Name": "isDefault", "Values": ["true"]}]
    )
