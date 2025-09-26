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
    """Get OpenSearch client with proper configuration.

    For OpenSearch Serverless, use SigV4 authentication with the Lambda's IAM role.
    """
    from urllib.parse import urlparse
    from opensearchpy import AWSV4SignerAuth, RequestsHttpConnection

    session = boto3.Session()
    credentials = session.get_credentials()
    auth = AWSV4SignerAuth(credentials, settings.aws_region)

    # settings.opensearch_endpoint is a full https URL for Serverless
    parsed = urlparse(str(settings.opensearch_endpoint))
    host = parsed.hostname or str(settings.opensearch_endpoint)

    return OpenSearch(
        hosts=[{"host": host, "port": 443}],
        http_auth=auth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
    )
