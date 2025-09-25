# ADR-002: Outbox Pattern for Event Publishing

## Status
Accepted

## Context
We need to ensure reliable event publishing from our microservices. The challenge is maintaining data consistency between database updates and event publishing.

Options considered:
1. **Direct Publishing**: Publish events directly after database updates
2. **Outbox Pattern**: Store events in database, publish asynchronously
3. **Event Sourcing**: Store all changes as events

## Decision
We will implement the **Outbox Pattern** for reliable event publishing.

## Rationale

### Advantages
- **Reliability**: Events are guaranteed to be published (at least once)
- **Consistency**: Database and event publishing are atomic
- **Resilience**: Survives service restarts and failures
- **Ordering**: Events can be published in order
- **Audit Trail**: Complete history of events

### Trade-offs
- **Complexity**: Additional table and processing logic
- **Latency**: Slight delay in event publishing
- **Storage**: Additional storage for outbox events
- **Cleanup**: Need to clean up processed events

## Implementation

### Outbox Table Schema
```sql
CREATE TABLE service_outbox (
    eventId VARCHAR(255) PRIMARY KEY,
    eventType VARCHAR(100) NOT NULL,
    eventData JSON NOT NULL,
    topicArn VARCHAR(255) NOT NULL,
    createdAt TIMESTAMP NOT NULL,
    published BOOLEAN DEFAULT FALSE,
    publishedAt TIMESTAMP NULL,
    ttl BIGINT NOT NULL
);
```

### Process Flow
1. **Transaction Start**: Begin database transaction
2. **Business Logic**: Update business data
3. **Outbox Insert**: Insert event into outbox table
4. **Transaction Commit**: Commit both changes atomically
5. **Event Publishing**: Background process publishes events
6. **Cleanup**: Mark events as published and clean up

### Background Processing
- **Polling**: Regular polling of outbox table
- **Batch Processing**: Process multiple events in batches
- **Retry Logic**: Retry failed event publications
- **Dead Letter Queue**: Handle permanently failed events

## Code Example

```python
class OutboxEventPublisher:
    def publish_event(self, event_type: str, data: dict, topic_arn: str):
        # Store in outbox within transaction
        outbox_event = OutboxEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            event_data=data,
            topic_arn=topic_arn
        )
        
        # Store in outbox table
        self.store_outbox_event(outbox_event)
        
        # Publish to SNS
        self.publish_to_sns(outbox_event)
        
        # Mark as published
        self.mark_published(outbox_event.event_id)
```

## Monitoring

### Metrics
- **Outbox Size**: Number of unpublished events
- **Processing Lag**: Time between creation and publishing
- **Failure Rate**: Percentage of failed publications
- **Retry Count**: Number of retries per event

### Alerts
- **High Outbox Size**: Too many unpublished events
- **High Processing Lag**: Events taking too long to publish
- **High Failure Rate**: Many events failing to publish
- **Stuck Events**: Events that haven't been processed

## Cleanup Strategy

### TTL-based Cleanup
- Events have a TTL (Time To Live)
- Expired events are automatically deleted
- Prevents outbox table from growing indefinitely

### Published Event Cleanup
- Mark events as published after successful SNS delivery
- Periodically clean up published events
- Keep recent events for debugging

## Error Handling

### Retry Logic
- **Exponential Backoff**: Increasing delays between retries
- **Max Retries**: Limit number of retry attempts
- **Dead Letter Queue**: Move failed events to DLQ

### Failure Scenarios
- **SNS Unavailable**: Retry with backoff
- **Invalid Event Data**: Move to DLQ for manual review
- **Database Issues**: Retry database operations
- **Service Restart**: Resume processing from outbox

## Testing

### Unit Tests
- Test outbox event creation
- Test event publishing logic
- Test retry mechanisms
- Test cleanup processes

### Integration Tests
- Test end-to-end event flow
- Test failure scenarios
- Test recovery after service restart
- Test event ordering

## Future Considerations

### Event Ordering
- Implement sequence numbers for ordering
- Handle out-of-order event processing
- Consider event versioning

### Performance Optimization
- Batch event processing
- Parallel event publishing
- Optimize database queries

### Monitoring Enhancement
- Add event tracing
- Implement event replay
- Add event analytics
