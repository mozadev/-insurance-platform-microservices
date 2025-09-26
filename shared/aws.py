"""AWS client configuration and utilities."""

import boto3
from botocore.config import Config

from .config import Settings


def get_dynamodb_client(settings: Settings):
    """Get DynamoDB client with proper configuration."""
    config = Config(
        region_name=settings.dynamodb_region,
        retries={"max_attempts": 3, "mode": "adaptive"},
    )

    return boto3.client(
        "dynamodb",
        endpoint_url=settings.dynamodb_endpoint_url,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
        config=config,
    )


def get_sns_client(settings: Settings):
    """Get SNS client with proper configuration."""
    config = Config(
        region_name=settings.aws_region, retries={"max_attempts": 3, "mode": "adaptive"}
    )

    return boto3.client(
        "sns",
        endpoint_url=settings.aws_endpoint_url,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
        config=config,
    )


def get_sqs_client(settings: Settings):
    """Get SQS client with proper configuration."""
    config = Config(
        region_name=settings.aws_region, retries={"max_attempts": 3, "mode": "adaptive"}
    )

    return boto3.client(
        "sqs",
        endpoint_url=settings.aws_endpoint_url,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
        config=config,
    )


def get_s3_client(settings: Settings):
    """Get S3 client with proper configuration."""
    config = Config(
        region_name=settings.aws_region, retries={"max_attempts": 3, "mode": "adaptive"}
    )

    # Always use IAM role in Lambda (no explicit credentials)
    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url,
        config=config,
    )


def get_opensearch_client(settings: Settings):
    """Get OpenSearch client with proper configuration."""
    from opensearchpy import OpenSearch

    return OpenSearch(
        hosts=[settings.opensearch_endpoint],
        http_auth=(settings.opensearch_username, settings.opensearch_password),
        use_ssl=False,
        verify_certs=False,
        ssl_assert_hostname=False,
        ssl_show_warn=False,
    )
