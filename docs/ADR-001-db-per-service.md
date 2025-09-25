# ADR-001: Database-per-Service Pattern

## Status
Accepted

## Context
We need to decide on a data management strategy for our microservices architecture. The main options are:

1. **Shared Database**: All services share a single database
2. **Database-per-Service**: Each service has its own database
3. **Saga Pattern**: Distributed transactions across services

## Decision
We will implement the **Database-per-Service** pattern.

## Rationale

### Advantages
- **Service Independence**: Each service can evolve its data model independently
- **Technology Freedom**: Services can use different database technologies
- **Fault Isolation**: Database issues don't cascade across services
- **Team Autonomy**: Teams can manage their own data without coordination
- **Scalability**: Each service can scale its database independently

### Trade-offs
- **Data Consistency**: No ACID transactions across services
- **Complexity**: Need to handle eventual consistency
- **Data Duplication**: Some data may be replicated across services
- **Query Complexity**: Cross-service queries require API calls

## Implementation

### Data Ownership
- **Policy Service**: Owns policy data in DynamoDB
- **Claim Service**: Owns claim data in DynamoDB
- **Search Service**: Owns search indices in OpenSearch
- **Auth Service**: Owns user data in Redis/DynamoDB

### Data Synchronization
- **Events**: Use SNS/SQS for data synchronization
- **Outbox Pattern**: Ensure reliable event publishing
- **Eventual Consistency**: Accept eventual consistency for non-critical data

### Cross-Service Queries
- **API Composition**: Gateway BFF composes data from multiple services
- **CQRS**: Separate read models for complex queries
- **Search Service**: Centralized search across all data

## Consequences

### Positive
- Services can be developed and deployed independently
- Each service can optimize its data model for its use case
- Clear data ownership boundaries
- Better fault isolation

### Negative
- Increased complexity for cross-service operations
- Need to handle eventual consistency
- More complex testing scenarios
- Potential data duplication

## Monitoring
- Track data consistency across services
- Monitor event processing lag
- Alert on data synchronization failures
- Regular consistency checks

## Future Considerations
- Consider CQRS for complex read scenarios
- Implement data versioning for schema evolution
- Add data lineage tracking for compliance
