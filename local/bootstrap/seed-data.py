#!/usr/bin/env python3
"""Seed data script for local development."""

import json
import time
import uuid
from datetime import datetime
from typing import Dict, Any

import boto3
import requests
from opensearchpy import OpenSearch


def create_aws_clients():
    """Create AWS clients for LocalStack."""
    return {
        "sns": boto3.client(
            "sns",
            endpoint_url="http://localhost:4566",
            aws_access_key_id="test",
            aws_secret_access_key="test",
            region_name="us-east-1",
        ),
        "sqs": boto3.client(
            "sqs",
            endpoint_url="http://localhost:4566",
            aws_access_key_id="test",
            aws_secret_access_key="test",
            region_name="us-east-1",
        ),
        "dynamodb": boto3.client(
            "dynamodb",
            endpoint_url="http://localhost:4566",
            aws_access_key_id="test",
            aws_secret_access_key="test",
            region_name="us-east-1",
        ),
    }


def create_opensearch_client():
    """Create OpenSearch client."""
    return OpenSearch(
        hosts=[{"host": "localhost", "port": 9200}],
        http_auth=None,
        use_ssl=False,
        verify_certs=False,
        ssl_assert_hostname=False,
    )


def wait_for_services():
    """Wait for services to be ready."""
    print("⏳ Waiting for services to be ready...")

    # Wait for LocalStack
    while True:
        try:
            response = requests.get(
                "http://localhost:4566/_localstack/health", timeout=5
            )
            if response.status_code == 200:
                break
        except requests.exceptions.RequestException:
            pass
        time.sleep(2)

    # Wait for OpenSearch
    while True:
        try:
            response = requests.get("http://localhost:9200/_cluster/health", timeout=5)
            if response.status_code == 200:
                break
        except requests.exceptions.RequestException:
            pass
        time.sleep(2)

    # Wait for services
    services = [
        ("http://localhost:8001/health", "Policy Service"),
        ("http://localhost:8002/health", "Claim Service"),
        ("http://localhost:8005/health", "Search Service"),
    ]

    for url, name in services:
        while True:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    print(f"✅ {name} is ready")
                    break
            except requests.exceptions.RequestException:
                pass
            time.sleep(2)

    print("✅ All services are ready!")


def create_sample_policies(aws_clients: Dict[str, Any]) -> list[Dict[str, Any]]:
    """Create sample policies."""
    print("📋 Creating sample policies...")

    policies = [
        {
            "policyId": "POL-12345678",
            "customerId": "CUST-TEST01",
            "status": "active",
            "premium": 1200.00,
            "effectiveDate": "2024-01-01",
            "expirationDate": "2024-12-31",
            "coverageType": "auto",
            "deductible": 500.00,
            "coverageLimit": 50000.00,
            "createdAt": datetime.utcnow().isoformat(),
            "updatedAt": datetime.utcnow().isoformat(),
        },
        {
            "policyId": "POL-87654321",
            "customerId": "CUST-TEST02",
            "status": "active",
            "premium": 800.00,
            "effectiveDate": "2024-01-01",
            "expirationDate": "2024-12-31",
            "coverageType": "property",
            "deductible": 1000.00,
            "coverageLimit": 100000.00,
            "createdAt": datetime.utcnow().isoformat(),
            "updatedAt": datetime.utcnow().isoformat(),
        },
    ]

    # Store in DynamoDB
    for policy in policies:
        aws_clients["dynamodb"].put_item(
            TableName="policy-svc_policies",
            Item={
                "PK": {"S": f"POL#{policy['policyId']}"},
                "SK": {"S": f"META#{int(datetime.utcnow().timestamp())}"},
                "PolicyId": {"S": policy["policyId"]},
                "CustomerId": {"S": policy["customerId"]},
                "Status": {"S": policy["status"]},
                "Premium": {"N": str(policy["premium"])},
                "EffectiveDate": {"S": policy["effectiveDate"]},
                "ExpirationDate": {"S": policy["expirationDate"]},
                "CoverageType": {"S": policy["coverageType"]},
                "Deductible": {"N": str(policy["deductible"])},
                "CoverageLimit": {"N": str(policy["coverageLimit"])},
                "CreatedAt": {"S": policy["createdAt"]},
                "UpdatedAt": {"S": policy["updatedAt"]},
                "GSI1PK": {"S": f"CUST#{policy['customerId']}"},
                "GSI1SK": {
                    "S": f"POL#{policy['policyId']}#{int(datetime.utcnow().timestamp())}"
                },
                "TTL": {
                    "N": str(int((datetime.utcnow().timestamp() + 86400 * 365 * 10)))
                },
            },
        )

    return policies


def create_sample_claims(aws_clients: Dict[str, Any]) -> list[Dict[str, Any]]:
    """Create sample claims."""
    print("📋 Creating sample claims...")

    claims = [
        {
            "claimId": "CLAIM-11111111",
            "policyId": "POL-12345678",
            "customerId": "CUST-TEST01",
            "status": "open",
            "amount": 2500.00,
            "occurredAt": "2024-01-15T10:30:00Z",
            "description": "Car accident on highway",
            "category": "auto",
            "createdAt": datetime.utcnow().isoformat(),
            "updatedAt": datetime.utcnow().isoformat(),
        },
        {
            "claimId": "CLAIM-22222222",
            "policyId": "POL-87654321",
            "customerId": "CUST-TEST02",
            "status": "in_review",
            "amount": 5000.00,
            "occurredAt": "2024-01-20T14:45:00Z",
            "description": "Water damage to basement",
            "category": "property",
            "createdAt": datetime.utcnow().isoformat(),
            "updatedAt": datetime.utcnow().isoformat(),
        },
    ]

    # Store in DynamoDB
    for claim in claims:
        aws_clients["dynamodb"].put_item(
            TableName="claim-svc_claims",
            Item={
                "PK": {"S": f"CLAIM#{claim['claimId']}"},
                "SK": {"S": f"META#{int(datetime.utcnow().timestamp())}"},
                "ClaimId": {"S": claim["claimId"]},
                "PolicyId": {"S": claim["policyId"]},
                "CustomerId": {"S": claim["customerId"]},
                "Status": {"S": claim["status"]},
                "Amount": {"N": str(claim["amount"])},
                "OccurredAt": {"S": claim["occurredAt"]},
                "Description": {"S": claim["description"]},
                "Category": {"S": claim["category"]},
                "CreatedAt": {"S": claim["createdAt"]},
                "UpdatedAt": {"S": claim["updatedAt"]},
                "GSI1PK": {"S": f"POL#{claim['policyId']}"},
                "GSI1SK": {
                    "S": f"STATUS#{claim['status']}#{int(datetime.utcnow().timestamp())}"
                },
                "TTL": {
                    "N": str(int((datetime.utcnow().timestamp() + 86400 * 365 * 7)))
                },
            },
        )

    return claims


def publish_events(
    aws_clients: Dict[str, Any],
    policies: list[Dict[str, Any]],
    claims: list[Dict[str, Any]],
):
    """Publish events to SNS."""
    print("📢 Publishing events...")

    # Get topic ARNs
    topics = aws_clients["sns"].list_topics()
    policies_topic_arn = None
    claims_topic_arn = None

    for topic in topics["Topics"]:
        if "policies-topic" in topic["TopicArn"]:
            policies_topic_arn = topic["TopicArn"]
        elif "claims-topic" in topic["TopicArn"]:
            claims_topic_arn = topic["TopicArn"]

    # Publish policy events
    for policy in policies:
        event = {
            "eventId": str(uuid.uuid4()),
            "eventType": "PolicyCreated",
            "eventVersion": 1,
            "occurredAt": datetime.utcnow().isoformat() + "Z",
            "policy": policy,
        }

        aws_clients["sns"].publish(
            TopicArn=policies_topic_arn,
            Message=json.dumps(event),
            MessageAttributes={
                "eventType": {"DataType": "String", "StringValue": "PolicyCreated"}
            },
        )

    # Publish claim events
    for claim in claims:
        event = {
            "eventId": str(uuid.uuid4()),
            "eventType": "ClaimCreated",
            "eventVersion": 1,
            "occurredAt": datetime.utcnow().isoformat() + "Z",
            "claim": claim,
        }

        aws_clients["sns"].publish(
            TopicArn=claims_topic_arn,
            Message=json.dumps(event),
            MessageAttributes={
                "eventType": {"DataType": "String", "StringValue": "ClaimCreated"}
            },
        )


def index_in_opensearch(
    opensearch_client: OpenSearch,
    policies: list[Dict[str, Any]],
    claims: list[Dict[str, Any]],
):
    """Index data in OpenSearch."""
    print("🔍 Indexing data in OpenSearch...")

    # Create indices if they don't exist
    indices = ["ins-claims", "ins-policies"]
    for index in indices:
        if not opensearch_client.indices.exists(index=index):
            opensearch_client.indices.create(index=index)

    # Index policies
    for policy in policies:
        doc = policy.copy()
        doc["type"] = "policy"
        doc["customerName"] = f"Customer {policy['customerId']}"
        doc["indexedAt"] = datetime.utcnow().isoformat()

        opensearch_client.index(index="ins-policies", id=policy["policyId"], body=doc)

    # Index claims
    for claim in claims:
        doc = claim.copy()
        doc["type"] = "claim"
        doc["customerName"] = f"Customer {claim['customerId']}"
        doc["indexedAt"] = datetime.utcnow().isoformat()

        opensearch_client.index(index="ins-claims", id=claim["claimId"], body=doc)


def test_apis():
    """Test the APIs."""
    print("🧪 Testing APIs...")

    # Test policy service
    try:
        response = requests.get("http://localhost:8001/health")
        print(f"✅ Policy Service: {response.status_code}")
    except Exception as e:
        print(f"❌ Policy Service: {e}")

    # Test claim service
    try:
        response = requests.get("http://localhost:8002/health")
        print(f"✅ Claim Service: {response.status_code}")
    except Exception as e:
        print(f"❌ Claim Service: {e}")

    # Test search service
    try:
        response = requests.get("http://localhost:8005/health")
        print(f"✅ Search Service: {response.status_code}")
    except Exception as e:
        print(f"❌ Search Service: {e}")

    # Test search functionality
    try:
        response = requests.get("http://localhost:8005/search/?q=POL-12345678")
        print(f"✅ Search API: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Found {data['total']} results")
    except Exception as e:
        print(f"❌ Search API: {e}")


def main():
    """Main function."""
    print("🌱 Starting seed data process...")

    # Wait for services
    wait_for_services()

    # Create clients
    aws_clients = create_aws_clients()
    opensearch_client = create_opensearch_client()

    # Create sample data
    policies = create_sample_policies(aws_clients)
    claims = create_sample_claims(aws_clients)

    # Publish events
    publish_events(aws_clients, policies, claims)

    # Index in OpenSearch
    index_in_opensearch(opensearch_client, policies, claims)

    # Test APIs
    test_apis()

    print("🎉 Seed data process completed!")
    print("\n📋 Sample data created:")
    print(f"  - {len(policies)} policies")
    print(f"  - {len(claims)} claims")
    print("\n🔗 Test the APIs:")
    print("  - Policy Service: http://localhost:8001/docs")
    print("  - Claim Service: http://localhost:8002/docs")
    print("  - Search Service: http://localhost:8005/docs")


if __name__ == "__main__":
    main()
