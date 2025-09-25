"""Shared configuration management for microservices."""

from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Base settings for all microservices."""

    # Environment
    environment: str = Field(default="local", env="ENVIRONMENT")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    # AWS Configuration
    aws_region: str = Field(default="us-east-1", env="AWS_REGION")
    aws_endpoint_url: Optional[str] = Field(default=None, env="AWS_ENDPOINT_URL")
    aws_access_key_id: str = Field(default="test", env="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str = Field(default="test", env="AWS_SECRET_ACCESS_KEY")

    # Service Configuration
    service_name: str = Field(..., env="SERVICE_NAME")
    service_port: int = Field(..., env="SERVICE_PORT")

    # Database Configuration
    dynamodb_endpoint_url: Optional[str] = Field(
        default=None, env="DYNAMODB_ENDPOINT_URL"
    )
    dynamodb_region: str = Field(default="us-east-1", env="DYNAMODB_REGION")

    # OpenSearch Configuration
    opensearch_endpoint: str = Field(
        default="http://localhost:9200", env="OPENSEARCH_ENDPOINT"
    )
    opensearch_username: str = Field(default="admin", env="OPENSEARCH_USERNAME")
    opensearch_password: str = Field(default="admin", env="OPENSEARCH_PASSWORD")
    opensearch_index_prefix: str = Field(default="ins", env="OPENSEARCH_INDEX_PREFIX")

    # Redis Configuration
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    redis_db: int = Field(default=0, env="REDIS_DB")

    # S3 Configuration
    s3_bronze_bucket: str = Field(default="ins-bronze", env="S3_BRONZE_BUCKET")
    s3_silver_bucket: str = Field(default="ins-silver", env="S3_SILVER_BUCKET")
    s3_endpoint_url: Optional[str] = Field(default=None, env="S3_ENDPOINT_URL")

    # Event Configuration
    policies_topic_arn: str = Field(..., env="POLICIES_TOPIC_ARN")
    claims_topic_arn: str = Field(..., env="CLAIMS_TOPIC_ARN")
    policies_queue_url: str = Field(..., env="POLICIES_QUEUE_URL")
    claims_queue_url: str = Field(..., env="CLAIMS_QUEUE_URL")

    # JWT Configuration
    jwt_secret_key: str = Field(default="your-secret-key-here", env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expiration_hours: int = Field(default=24, env="JWT_EXPIRATION_HOURS")

    # Observability
    otel_service_name: str = Field(
        default="insurance-platform", env="OTEL_SERVICE_NAME"
    )
    otel_exporter_otlp_endpoint: Optional[str] = Field(
        default=None, env="OTEL_EXPORTER_OTLP_ENDPOINT"
    )
    otel_resource_attributes: str = Field(
        default="service.name=insurance-platform,service.version=1.0.0",
        env="OTEL_RESOURCE_ATTRIBUTES",
    )

    # Circuit Breaker
    circuit_breaker_failure_threshold: int = Field(
        default=5, env="CIRCUIT_BREAKER_FAILURE_THRESHOLD"
    )
    circuit_breaker_recovery_timeout: int = Field(
        default=60, env="CIRCUIT_BREAKER_RECOVERY_TIMEOUT"
    )

    # Rate Limiting
    rate_limit_requests_per_minute: int = Field(
        default=100, env="RATE_LIMIT_REQUESTS_PER_MINUTE"
    )
    rate_limit_burst: int = Field(default=10, env="RATE_LIMIT_BURST")

    class Config:
        env_file = ".env"
        case_sensitive = False


def get_settings() -> Settings:
    """Get application settings."""
    return Settings()
