"""Tests for AWSValidator"""

import pytest
from unittest.mock import Mock, patch
from botocore.exceptions import NoCredentialsError, ClientError
from cloud_core.validation.aws_validator import AWSValidator


@pytest.fixture
def aws_validator():
    """Create AWSValidator instance"""
    return AWSValidator()


def test_aws_validator_init():
    """Test AWSValidator initialization"""
    validator = AWSValidator()
    assert validator is not None
    assert validator.errors == []
    assert validator.warnings == []


@patch('boto3.client')
def test_validate_success(mock_boto_client, aws_validator):
    """Test successful validation"""
    # Mock STS client for credentials
    mock_sts = Mock()
    mock_sts.get_caller_identity.return_value = {
        "Account": "123456789012",
        "Arn": "arn:aws:iam::123456789012:user/testuser"
    }

    # Mock S3 client for permissions
    mock_s3 = Mock()
    mock_s3.list_buckets.return_value = {"Buckets": []}

    def client_side_effect(service, **kwargs):
        if service == "sts":
            return mock_sts
        elif service == "s3":
            return mock_s3
        return Mock()

    mock_boto_client.side_effect = client_side_effect

    result = aws_validator.validate()

    assert result is True
    assert len(aws_validator.get_errors()) == 0


@patch('boto3.client')
def test_validate_no_credentials(mock_boto_client, aws_validator):
    """Test validation with no credentials"""
    mock_sts = Mock()
    mock_sts.get_caller_identity.side_effect = NoCredentialsError()
    mock_boto_client.return_value = mock_sts

    result = aws_validator.validate()

    assert result is False
    errors = aws_validator.get_errors()
    assert len(errors) > 0
    assert "credentials not configured" in errors[0]


@patch('boto3.client')
def test_validate_credential_error(mock_boto_client, aws_validator):
    """Test validation with credential error"""
    mock_sts = Mock()
    mock_sts.get_caller_identity.side_effect = ClientError(
        {"Error": {"Code": "InvalidClientTokenId", "Message": "Invalid token"}},
        "GetCallerIdentity"
    )
    mock_boto_client.return_value = mock_sts

    result = aws_validator.validate()

    assert result is False
    errors = aws_validator.get_errors()
    assert len(errors) > 0


@patch('boto3.client')
def test_validate_limited_permissions(mock_boto_client, aws_validator):
    """Test validation with limited permissions"""
    mock_sts = Mock()
    mock_sts.get_caller_identity.return_value = {
        "Account": "123456789012",
        "Arn": "arn:aws:iam::123456789012:user/testuser"
    }

    mock_s3 = Mock()
    mock_s3.list_buckets.side_effect = ClientError(
        {"Error": {"Code": "AccessDenied", "Message": "Access denied"}},
        "ListBuckets"
    )

    def client_side_effect(service, **kwargs):
        if service == "sts":
            return mock_sts
        elif service == "s3":
            return mock_s3
        return Mock()

    mock_boto_client.side_effect = client_side_effect

    result = aws_validator.validate()

    # Should still pass with warnings
    assert result is True
    warnings = aws_validator.get_warnings()
    assert len(warnings) > 0


def test_get_errors(aws_validator):
    """Test getting validation errors"""
    assert aws_validator.get_errors() == []

    aws_validator.errors.append("Test error")

    errors = aws_validator.get_errors()
    assert len(errors) == 1
    assert "Test error" in errors


def test_get_warnings(aws_validator):
    """Test getting validation warnings"""
    assert aws_validator.get_warnings() == []

    aws_validator.warnings.append("Test warning")

    warnings = aws_validator.get_warnings()
    assert len(warnings) == 1
    assert "Test warning" in warnings


@patch('boto3.client')
def test_get_account_id(mock_boto_client, aws_validator):
    """Test getting AWS account ID"""
    mock_sts = Mock()
    mock_sts.get_caller_identity.return_value = {
        "Account": "123456789012"
    }
    mock_boto_client.return_value = mock_sts

    account_id = aws_validator.get_account_id()

    assert account_id == "123456789012"


@patch('boto3.client')
def test_get_account_id_error(mock_boto_client, aws_validator):
    """Test getting account ID with error"""
    mock_sts = Mock()
    mock_sts.get_caller_identity.side_effect = ClientError(
        {"Error": {"Code": "InvalidClientTokenId"}},
        "GetCallerIdentity"
    )
    mock_boto_client.return_value = mock_sts

    account_id = aws_validator.get_account_id()

    assert account_id == ""


@patch('boto3.client')
def test_validate_with_unexpected_error(mock_boto_client, aws_validator):
    """Test validation with unexpected error"""
    mock_sts = Mock()
    mock_sts.get_caller_identity.side_effect = Exception("Unexpected error")
    mock_boto_client.return_value = mock_sts

    result = aws_validator.validate()

    assert result is False
    errors = aws_validator.get_errors()
    assert len(errors) > 0
    assert "Unexpected" in errors[0]


@patch('boto3.client')
def test_validate_permission_check_error(mock_boto_client, aws_validator):
    """Test validation with permission check error"""
    mock_sts = Mock()
    mock_sts.get_caller_identity.return_value = {
        "Account": "123456789012",
        "Arn": "arn:aws:iam::123456789012:user/testuser"
    }

    mock_s3 = Mock()
    mock_s3.list_buckets.side_effect = Exception("Unexpected S3 error")

    def client_side_effect(service, **kwargs):
        if service == "sts":
            return mock_sts
        elif service == "s3":
            return mock_s3
        return Mock()

    mock_boto_client.side_effect = client_side_effect

    result = aws_validator.validate()

    # Should pass with warning
    assert result is True
    warnings = aws_validator.get_warnings()
    assert len(warnings) > 0


@patch('boto3.client')
def test_validate_clears_previous_errors(mock_boto_client, aws_validator):
    """Test that validate clears previous errors"""
    # Add some old errors
    aws_validator.errors.append("Old error")

    mock_sts = Mock()
    mock_sts.get_caller_identity.return_value = {
        "Account": "123456789012",
        "Arn": "arn:aws:iam::123456789012:user/testuser"
    }

    mock_s3 = Mock()
    mock_s3.list_buckets.return_value = {"Buckets": []}

    def client_side_effect(service, **kwargs):
        if service == "sts":
            return mock_sts
        elif service == "s3":
            return mock_s3
        return Mock()

    mock_boto_client.side_effect = client_side_effect

    result = aws_validator.validate()

    assert result is True
    # Old errors should be cleared
    assert "Old error" not in aws_validator.get_errors()
