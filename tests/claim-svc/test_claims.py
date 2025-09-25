"""Tests for claim service."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from services.claim_svc.app.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_dynamodb():
    """Mock DynamoDB client."""
    with patch('services.claim_svc.app.repositories.dynamodb.get_dynamodb_client') as mock:
        mock_client = Mock()
        mock_client.put_item.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}
        mock_client.get_item.return_value = {'Item': {}}
        mock_client.query.return_value = {'Items': []}
        mock.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_sns():
    """Mock SNS client."""
    with patch('services.claim_svc.app.events.publisher.get_sns_client') as mock:
        mock_client = Mock()
        mock_client.publish.return_value = {'MessageId': 'test-message-id'}
        mock.return_value = mock_client
        yield mock_client


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_create_claim(client, mock_dynamodb, mock_sns):
    """Test claim creation."""
    claim_data = {
        "policyId": "POL-12345678",
        "customerId": "CUST-TEST01",
        "status": "open",
        "amount": 2500.0,
        "occurredAt": "2024-01-15T10:30:00Z",
        "description": "Car accident",
        "category": "auto",
        "idempotencyKey": "test-key-123"
    }
    
    # Mock JWT verification
    with patch('services.claim_svc.app.routers.claims.get_current_customer') as mock_auth:
        mock_auth.return_value = "CUST-TEST01"
        
        response = client.post("/claims/", json=claim_data)
        assert response.status_code == 201
        assert "claimId" in response.json()


def test_idempotency(client, mock_dynamodb, mock_sns):
    """Test idempotency for claim creation."""
    claim_data = {
        "policyId": "POL-12345678",
        "customerId": "CUST-TEST01",
        "status": "open",
        "amount": 2500.0,
        "occurredAt": "2024-01-15T10:30:00Z",
        "description": "Car accident",
        "category": "auto",
        "idempotencyKey": "test-key-123"
    }
    
    # Mock idempotency check - first call returns None, second returns cached response
    with patch('services.claim_svc.app.idempotency.dynamodb.IdempotencyManager.get_response') as mock_idem:
        mock_idem.side_effect = [None, {"claimId": "CLAIM-12345678", "status": "open"}]
        
        with patch('services.claim_svc.app.routers.claims.get_current_customer') as mock_auth:
            mock_auth.return_value = "CUST-TEST01"
            
            # First call should create claim
            response1 = client.post("/claims/", json=claim_data)
            assert response1.status_code == 201
            
            # Second call should return cached response
            response2 = client.post("/claims/", json=claim_data)
            assert response2.status_code == 201
            assert response2.json()["claimId"] == "CLAIM-12345678"
