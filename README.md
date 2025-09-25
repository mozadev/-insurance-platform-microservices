# Insurance Data Platform - Microservices

A production-ready microservices platform for insurance data management with policy and claims processing, built on AWS with event-driven architecture.

## 🏗️ Architecture Overview

- **Edge**: API Gateway/ALB with public REST APIs
- **Services**: policy-svc, claim-svc, search-svc, ingest-svc, auth-svc, gateway-bff
- **Events**: PolicyCreated, PolicyUpdated, ClaimCreated, ClaimUpdated via SNS→SQS
- **Data Lake**: S3 + Parquet (bronze/silver), OpenSearch for search, DynamoDB per service
- **Orchestration**: Step Functions for claims pipeline, EventBridge for triggers

## 🚀 Quick Start

```bash
# Setup development environment
make setup

# Start local development stack
make compose:up

# Bootstrap AWS resources in LocalStack
make bootstrap

# Run demo with sample data
make demo

# Run tests and quality checks
make lint type test
```

## 📋 Services

### policy-svc (Port 8001)
- `POST /policies` - Create policy
- `GET /policies/{policyId}` - Get policy by ID
- `GET /customers/{customerId}/policies` - Get customer policies

### claim-svc (Port 8002)
- `POST /claims` - Create claim (with idempotency)
- `GET /claims/{claimId}` - Get claim by ID
- `GET /policies/{policyId}/claims` - Get policy claims

### search-svc (Port 8005)
- `GET /search?q=...` - Search across policies and claims

### gateway-bff (Port 8000)
- Consolidated API gateway with rate limiting

### auth-svc (Port 8003)
- `POST /auth/token` - Generate JWT token

## 🛠️ Local Development

The local environment uses:
- **LocalStack**: AWS services simulation
- **OpenSearch**: Search engine
- **Redis**: Caching and circuit breaker
- **Docker Compose**: Service orchestration

### Prerequisites
- Docker and Docker Compose
- Python 3.12+
- Make

### Development Commands

```bash
# Start all services
make compose:up

# View logs
make logs

# Stop services
make compose:down

# Restart specific service
make restart

# Check service status
make status
```

## 🔧 API Usage Examples

### Authentication
```bash
# Get JWT token
curl -X POST http://localhost:8003/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username": "demo", "password": "demo"}'
```

### Policy Management
```bash
# Create policy
curl -X POST http://localhost:8001/policies \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "customerId": "CUST-TEST01",
    "status": "active",
    "premium": 1200.0,
    "effectiveDate": "2024-01-01",
    "expirationDate": "2024-12-31",
    "coverageType": "auto",
    "deductible": 500.0,
    "coverageLimit": 50000.0
  }'

# Get customer policies
curl -X GET http://localhost:8001/customers/CUST-TEST01/policies \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Claim Management
```bash
# Create claim with idempotency
curl -X POST http://localhost:8002/claims \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "policyId": "POL-12345678",
    "customerId": "CUST-TEST01",
    "status": "open",
    "amount": 2500.0,
    "occurredAt": "2024-01-15T10:30:00Z",
    "description": "Car accident",
    "category": "auto",
    "idempotencyKey": "unique-key-123"
  }'
```

### Search
```bash
# Search across all data
curl -X GET "http://localhost:8005/search/?q=POL-12345678" \
  -H "Authorization: Bearer demo-token"
```

### Gateway BFF
```bash
# Get customer dashboard
curl -X GET http://localhost:8000/api/dashboard \
  -H "Authorization: Bearer demo-token"

# Unified search
curl -X GET "http://localhost:8000/api/search?q=accident" \
  -H "Authorization: Bearer demo-token"
```

## 🏗️ Infrastructure

Terraform modules for AWS deployment:
- S3 data lake buckets
- DynamoDB tables (database-per-service)
- SNS topics and SQS queues
- OpenSearch cluster
- Step Functions workflows
- Lambda functions for ETL

## 📊 Event Contracts

Events are versioned and validated using JSON Schema:
- `ClaimCreated v1`
- `PolicyCreated v1`
- `ClaimUpdated v1`
- `PolicyUpdated v1`

## 🔒 Security

- JWT authentication (stub for local, Cognito-ready)
- IAM least-privilege policies
- Secrets management via AWS Secrets Manager
- Input validation and sanitization

## 📈 Observability

- OpenTelemetry tracing (W3C Trace Context)
- Structured JSON logging
- Custom metrics for business KPIs
- Health checks and readiness probes

## 🧪 Testing

```bash
# Run all tests
make test

# Run specific service tests
make test-policy
make test-claim
make test-search

# Run with coverage
pytest tests/ -v --cov=services --cov-report=html
```

## 🚀 CI/CD

GitHub Actions pipeline:
1. Lint and type checking
2. Unit and integration tests
3. Security scanning
4. Docker image building
5. Terraform plan/apply

## 📚 Documentation

- [Architecture Overview](docs/architecture.md)
- [ADR-001: Database-per-Service](docs/ADR-001-db-per-service.md)
- [ADR-002: Outbox Pattern](docs/ADR-002-outbox-events.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

## 🆘 Troubleshooting

### Common Issues

1. **Services not starting**: Check Docker logs with `make logs`
2. **LocalStack not ready**: Wait a few minutes after `make compose:up`
3. **OpenSearch connection issues**: Ensure OpenSearch is healthy
4. **Port conflicts**: Check if ports 8000-8005 are available

### Debug Commands

```bash
# Check service health
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8005/health

# View service logs
docker-compose -f local/docker-compose.yml logs policy-svc
docker-compose -f local/docker-compose.yml logs claim-svc
docker-compose -f local/docker-compose.yml logs search-svc

# Check LocalStack resources
aws --endpoint-url=http://localhost:4566 dynamodb list-tables
aws --endpoint-url=http://localhost:4566 sns list-topics
aws --endpoint-url=http://localhost:4566 sqs list-queues
```
