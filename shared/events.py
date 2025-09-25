"""Event publishing and validation utilities."""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import jsonschema
from opentelemetry import trace


class EventValidator:
    """Validates events against JSON Schema contracts."""

    def __init__(self, contracts_dir: str = "contracts/events"):
        self.contracts_dir = Path(contracts_dir)
        self._schemas: Dict[str, Dict[str, Any]] = {}
        self._load_schemas()

    def _load_schemas(self) -> None:
        """Load all event schemas from contracts directory."""
        if not self.contracts_dir.exists():
            return

        for schema_file in self.contracts_dir.glob("*.json"):
            with open(schema_file, "r") as f:
                schema = json.load(f)
                event_type = (
                    schema.get("properties", {}).get("eventType", {}).get("const")
                )
                if event_type:
                    self._schemas[event_type] = schema

    def validate_event(self, event: Dict[str, Any]) -> bool:
        """Validate an event against its schema."""
        event_type = event.get("eventType")
        if not event_type or event_type not in self._schemas:
            return False

        try:
            jsonschema.validate(event, self._schemas[event_type])
            return True
        except jsonschema.ValidationError:
            return False


class EventPublisher:
    """Publishes events to SNS with validation and tracing."""

    def __init__(self, sns_client, validator: EventValidator):
        self.sns_client = sns_client
        self.validator = validator

    def publish_event(
        self,
        event_type: str,
        data: Dict[str, Any],
        topic_arn: str,
        trace_id: Optional[str] = None,
    ) -> bool:
        """Publish an event to SNS topic."""
        # Create event envelope
        event = {
            "eventId": str(uuid.uuid4()),
            "eventType": event_type,
            "eventVersion": 1,
            "occurredAt": datetime.utcnow().isoformat() + "Z",
            "traceId": trace_id or self._get_current_trace_id(),
            **data,
        }

        # Validate event
        if not self.validator.validate_event(event):
            raise ValueError(f"Invalid event schema for {event_type}")

        try:
            # Publish to SNS
            response = self.sns_client.publish(
                TopicArn=topic_arn,
                Message=json.dumps(event),
                MessageAttributes={
                    "eventType": {"DataType": "String", "StringValue": event_type},
                    "eventVersion": {"DataType": "Number", "StringValue": "1"},
                },
            )

            return response.get("MessageId") is not None

        except Exception as e:
            raise RuntimeError(
                f"Failed to publish event {event_type}: {str(e)}"
            ) from e

    def _get_current_trace_id(self) -> Optional[str]:
        """Get current OpenTelemetry trace ID."""
        span = trace.get_current_span()
        if span and span.is_recording():
            return format(span.get_span_context().trace_id, "032x")
        return None


class OutboxEvent:
    """Represents an event in the outbox table."""

    def __init__(
        self,
        event_id: str,
        event_type: str,
        event_data: Dict[str, Any],
        topic_arn: str,
        created_at: Optional[datetime] = None,
    ):
        self.event_id = event_id
        self.event_type = event_type
        self.event_data = event_data
        self.topic_arn = topic_arn
        self.created_at = created_at or datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for DynamoDB storage."""
        return {
            "eventId": self.event_id,
            "eventType": self.event_type,
            "eventData": self.event_data,
            "topicArn": self.topic_arn,
            "createdAt": self.created_at.isoformat(),
            "ttl": int((self.created_at.timestamp() + 86400 * 7)),  # 7 days TTL
        }
