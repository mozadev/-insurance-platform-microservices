"""DynamoDB-based idempotency implementation."""

import hashlib
import json
from datetime import datetime, timedelta
from typing import Any

from botocore.exceptions import ClientError

from ...shared.logging import LoggerMixin


class IdempotencyManager(LoggerMixin):
    """Manages idempotency using DynamoDB."""

    def __init__(self, dynamodb_client, table_name: str, ttl_hours: int = 24):
        self.dynamodb = dynamodb_client
        self.table_name = table_name
        self.ttl_hours = ttl_hours

    def generate_key(self, idempotency_key: str, request_data: dict[str, Any]) -> str:
        """Generate a unique key for idempotency check."""
        # Combine idempotency key with request data hash for uniqueness
        request_hash = hashlib.sha256(
            json.dumps(request_data, sort_keys=True).encode()
        ).hexdigest()[:16]

        return f"IDEM#{idempotency_key}#{request_hash}"

    def put_if_absent(
        self,
        idempotency_key: str,
        request_data: dict[str, Any],
        response_data: dict[str, Any],
    ) -> bool:
        """Store idempotency key if it doesn't exist."""
        key = self.generate_key(idempotency_key, request_data)
        ttl = int((datetime.utcnow() + timedelta(hours=self.ttl_hours)).timestamp())

        try:
            self.dynamodb.put_item(
                TableName=self.table_name,
                Item={
                    "PK": {"S": key},
                    "SK": {"S": "IDEM"},
                    "IdempotencyKey": {"S": idempotency_key},
                    "RequestData": {"S": json.dumps(request_data)},
                    "ResponseData": {"S": json.dumps(response_data)},
                    "CreatedAt": {"S": datetime.utcnow().isoformat()},
                    "TTL": {"N": str(ttl)},
                },
                ConditionExpression="attribute_not_exists(PK)",
            )

            self.logger.info("Idempotency key stored", key=key)
            return True

        except ClientError as e:
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                self.logger.info("Idempotency key already exists", key=key)
                return False
            else:
                self.logger.error(
                    "Failed to store idempotency key", error=str(e), key=key
                )
                raise RuntimeError(f"Failed to store idempotency key: {str(e)}")

    def get_response(
        self, idempotency_key: str, request_data: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Get cached response for idempotency key."""
        key = self.generate_key(idempotency_key, request_data)

        try:
            response = self.dynamodb.get_item(
                TableName=self.table_name, Key={"PK": {"S": key}, "SK": {"S": "IDEM"}}
            )

            if "Item" not in response:
                return None

            item = response["Item"]
            return json.loads(item["ResponseData"]["S"])

        except (ClientError, KeyError, json.JSONDecodeError) as e:
            self.logger.error(
                "Failed to get idempotency response", error=str(e), key=key
            )
            return None

    def check_and_store(
        self,
        idempotency_key: str,
        request_data: dict[str, Any],
        response_data: dict[str, Any],
    ) -> tuple[bool, dict[str, Any] | None]:
        """Check if key exists and store if not."""
        # First check if we have a cached response
        cached_response = self.get_response(idempotency_key, request_data)
        if cached_response:
            return True, cached_response

        # Try to store the new response
        stored = self.put_if_absent(idempotency_key, request_data, response_data)
        if stored:
            return False, None  # New request, no cached response
        else:
            # Key already exists, get the cached response
            cached_response = self.get_response(idempotency_key, request_data)
            return True, cached_response
