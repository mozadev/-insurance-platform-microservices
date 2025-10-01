"""AWS client configuration and utilities."""

import boto3
from botocore.config import Config
from urllib.parse import urlparse

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


def get_elasticsearch_client(settings: Settings):
    """Get Elasticsearch client using requests to bypass distribution check.

    For AWS Elasticsearch with authentication.
    """
    import requests
    from requests.auth import HTTPBasicAuth
    
    class AWSESClient:
        def __init__(self, endpoint, username, password):
            self.base_url = f"https://{endpoint}"
            self.auth = HTTPBasicAuth(username, password)
            self.session = requests.Session()
            self.session.auth = self.auth
            self.session.headers.update({"Content-Type": "application/json"})
        
        def index(self, index, id=None, body=None, timeout=30):
            url = f"{self.base_url}/{index}/_doc"
            if id:
                url += f"/{id}"
            
            response = self.session.put(url, json=body, timeout=timeout)
            response.raise_for_status()
            return response.json()
    
    return AWSESClient(
        settings.elasticsearch_endpoint,
        settings.elasticsearch_username,
        settings.elasticsearch_password
    )
