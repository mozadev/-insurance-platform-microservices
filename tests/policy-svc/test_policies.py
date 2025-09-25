"""Tests for policy service."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from services.policy_svc.app.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_dynamodb():
    """Mock DynamoDB client."""
    with patch(
        "services.policy_svc.app.repositories.dynamodb.get_dynamodb_client"
    ) as mock:
        mock_client = Mock()
        mock_client.put_item.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": 200}
        }
        mock_client.get_item.return_value = {"Item": {}}
        mock_client.query.return_value = {"Items": []}
        mock.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_sns():
    """Mock SNS client."""
    with patch("services.policy_svc.app.events.publisher.get_sns_client") as mock:
        mock_client = Mock()
        mock_client.publish.return_value = {"MessageId": "test-message-id"}
        mock.return_value = mock_client
        yield mock_client


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_create_policy(client, mock_dynamodb, mock_sns):
    """Test policy creation."""
    policy_data = {
        "customerId": "CUST-TEST01",
        "status": "active",
        "premium": 1200.0,
        "effectiveDate": "2024-01-01",
        "expirationDate": "2024-12-31",
        "coverageType": "auto",
        "deductible": 500.0,
        "coverageLimit": 50000.0,
    }

    # Mock JWT verification
    with patch(
        "services.policy_svc.app.routers.policies.get_current_customer"
    ) as mock_auth:
        mock_auth.return_value = "CUST-TEST01"

        response = client.post("/policies/", json=policy_data)
        assert response.status_code == 201
        assert "policyId" in response.json()


def test_get_policy(client, mock_dynamodb):
    """Test get policy endpoint."""
    # Mock DynamoDB response
    mock_dynamodb.get_item.return_value = {
        "Item": {
            "PolicyId": {"S": "POL-12345678"},
            "CustomerId": {"S": "CUST-TEST01"},
            "Status": {"S": "active"},
            "Premium": {"N": "1200.0"},
            "EffectiveDate": {"S": "2024-01-01"},
            "ExpirationDate": {"S": "2024-12-31"},
            "CoverageType": {"S": "auto"},
            "Deductible": {"N": "500.0"},
            "CoverageLimit": {"N": "50000.0"},
            "CreatedAt": {"S": "2024-01-01T00:00:00Z"},
            "UpdatedAt": {"S": "2024-01-01T00:00:00Z"},
        }
    }

    # Mock JWT verification
    with patch(
        "services.policy_svc.app.routers.policies.get_current_customer"
    ) as mock_auth:
        mock_auth.return_value = "CUST-TEST01"

        response = client.get("/policies/POL-12345678")
        assert response.status_code == 200
        assert response.json()["policyId"] == "POL-12345678"
