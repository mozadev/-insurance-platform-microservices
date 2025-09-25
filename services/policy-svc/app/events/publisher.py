"""Event publisher for policy service using outbox pattern."""

import json
import uuid
from datetime import datetime
from typing import Dict, Any

from ...shared.aws import get_dynamodb_client, get_sns_client
from ...shared.config import Settings
from ...shared.events import EventValidator, EventPublisher, OutboxEvent
from ...shared.logging import LoggerMixin


class PolicyEventPublisher(LoggerMixin):
    """Publishes policy events using outbox pattern."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.dynamodb = get_dynamodb_client(settings)
        self.sns = get_sns_client(settings)
        self.validator = EventValidator()
        self.publisher = EventPublisher(self.sns, self.validator)
    
    def publish_policy_created(self, policy: Dict[str, Any]) -> bool:
        """Publish PolicyCreated event."""
        try:
            # Create outbox event
            outbox_event = OutboxEvent(
                event_id=str(uuid.uuid4()),
                event_type="PolicyCreated",
                event_data={"policy": policy},
                topic_arn=self.settings.policies_topic_arn
            )
            
            # Store in outbox table
            self._store_outbox_event(outbox_event)
            
            # Publish to SNS
            success = self.publisher.publish_event(
                event_type="PolicyCreated",
                data={"policy": policy},
                topic_arn=self.settings.policies_topic_arn
            )
            
            if success:
                self._mark_outbox_event_published(outbox_event.event_id)
            
            return success
            
        except Exception as e:
            self.logger.error("Failed to publish PolicyCreated event", error=str(e))
            return False
    
    def publish_policy_updated(self, policy: Dict[str, Any], updated_fields: list[str]) -> bool:
        """Publish PolicyUpdated event."""
        try:
            # Add updated fields to policy data
            policy_with_updates = policy.copy()
            policy_with_updates["updatedFields"] = updated_fields
            
            # Create outbox event
            outbox_event = OutboxEvent(
                event_id=str(uuid.uuid4()),
                event_type="PolicyUpdated",
                event_data={"policy": policy_with_updates},
                topic_arn=self.settings.policies_topic_arn
            )
            
            # Store in outbox table
            self._store_outbox_event(outbox_event)
            
            # Publish to SNS
            success = self.publisher.publish_event(
                event_type="PolicyUpdated",
                data={"policy": policy_with_updates},
                topic_arn=self.settings.policies_topic_arn
            )
            
            if success:
                self._mark_outbox_event_published(outbox_event.event_id)
            
            return success
            
        except Exception as e:
            self.logger.error("Failed to publish PolicyUpdated event", error=str(e))
            return False
    
    def _store_outbox_event(self, outbox_event: OutboxEvent) -> None:
        """Store event in outbox table."""
        try:
            self.dynamodb.put_item(
                TableName=f"{self.settings.service_name}_outbox",
                Item={
                    'eventId': {'S': outbox_event.event_id},
                    'eventType': {'S': outbox_event.event_type},
                    'eventData': {'S': json.dumps(outbox_event.event_data)},
                    'topicArn': {'S': outbox_event.topic_arn},
                    'createdAt': {'S': outbox_event.created_at.isoformat()},
                    'published': {'BOOL': False},
                    'ttl': {'N': str(outbox_event.to_dict()['ttl'])}
                }
            )
        except Exception as e:
            self.logger.error("Failed to store outbox event", error=str(e))
            raise
    
    def _mark_outbox_event_published(self, event_id: str) -> None:
        """Mark outbox event as published."""
        try:
            self.dynamodb.update_item(
                TableName=f"{self.settings.service_name}_outbox",
                Key={'eventId': {'S': event_id}},
                UpdateExpression="SET published = :published, publishedAt = :published_at",
                ExpressionAttributeValues={
                    ':published': {'BOOL': True},
                    ':published_at': {'S': datetime.utcnow().isoformat()}
                }
            )
        except Exception as e:
            self.logger.warning("Failed to mark outbox event as published", error=str(e))
    
    def process_outbox_events(self) -> int:
        """Process unpublished outbox events (for background job)."""
        try:
            # Query unpublished events
            response = self.dynamodb.scan(
                TableName=f"{self.settings.service_name}_outbox",
                FilterExpression="published = :published",
                ExpressionAttributeValues={':published': {'BOOL': False}},
                Limit=10
            )
            
            processed_count = 0
            for item in response.get('Items', []):
                try:
                    event_id = item['eventId']['S']
                    event_type = item['eventType']['S']
                    event_data = json.loads(item['eventData']['S'])
                    topic_arn = item['topicArn']['S']
                    
                    # Publish event
                    success = self.publisher.publish_event(
                        event_type=event_type,
                        data=event_data,
                        topic_arn=topic_arn
                    )
                    
                    if success:
                        self._mark_outbox_event_published(event_id)
                        processed_count += 1
                        self.logger.info("Processed outbox event", event_id=event_id, event_type=event_type)
                    
                except Exception as e:
                    self.logger.error("Failed to process outbox event", error=str(e), event_id=event_id)
                    continue
            
            return processed_count
            
        except Exception as e:
            self.logger.error("Failed to process outbox events", error=str(e))
            return 0
