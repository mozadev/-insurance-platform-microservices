"""AWS Lambda handler for ingesting events from SQS (SNS fanout)."""

import json
from typing import Any

from shared.aws import get_opensearch_client, get_s3_client
from shared.config import get_settings
from shared.events import EventValidator
from shared.logging import configure_logging, get_logger

_LOGGER_CONFIGURED = False


def _ensure_logging():
    global _LOGGER_CONFIGURED
    if not _LOGGER_CONFIGURED:
        settings = get_settings()
        configure_logging(settings.service_name, settings.log_level)
        _LOGGER_CONFIGURED = True


def _extract_event_from_sns_envelope(sqs_record_body: dict[str, Any]) -> dict[str, Any]:
    # Standard SNS → SQS envelope
    if "Message" in sqs_record_body:
        try:
            return json.loads(sqs_record_body["Message"])  # Publisher payload
        except json.JSONDecodeError:
            return {}
    if "Records" in sqs_record_body and sqs_record_body["Records"]:
        record = sqs_record_body["Records"][0]
        message = record.get("Sns", {}).get("Message")
        if message:
            try:
                return json.loads(message)
            except json.JSONDecodeError:
                return {}
    return sqs_record_body


def _normalize_policy(p: dict[str, Any]) -> dict[str, Any]:
    return {
        "policyId": p.get("policy_id") or p.get("policyId"),
        "customerId": p.get("customer_id") or p.get("customerId"),
        "status": p.get("status"),
        "premium": p.get("premium"),
        "effectiveDate": (p.get("effective_date") or p.get("effectiveDate")),
        "expirationDate": (p.get("expiration_date") or p.get("expirationDate")),
        "coverageType": p.get("coverage_type") or p.get("coverageType"),
        "deductible": p.get("deductible"),
        "coverageLimit": p.get("coverage_limit") or p.get("coverageLimit"),
        "createdAt": p.get("created_at") or p.get("createdAt"),
        "updatedAt": p.get("updated_at") or p.get("updatedAt"),
        "type": "policy",
    }


def _normalize_claim(c: dict[str, Any]) -> dict[str, Any]:
    return {
        "claimId": c.get("claim_id") or c.get("claimId"),
        "policyId": c.get("policy_id") or c.get("policyId"),
        "customerId": c.get("customer_id") or c.get("customerId"),
        "status": c.get("status"),
        "amount": c.get("amount"),
        "occurredAt": c.get("occurred_at") or c.get("occurredAt"),
        "description": c.get("description"),
        "category": c.get("category"),
        "createdAt": c.get("created_at") or c.get("createdAt"),
        "updatedAt": c.get("updated_at") or c.get("updatedAt"),
        "type": "claim",
    }


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """SQS batch event handler.

    Expects SQS records that wrap SNS messages containing event envelopes
    validated against contracts in contracts/events.
    """
    _ensure_logging()
    logger = get_logger(__name__)
    logger.info("Lambda function started - FORCE IAM ROLE TEST")

    settings = get_settings()
    s3 = get_s3_client(settings)
    opensearch = get_opensearch_client(settings)
    validator = EventValidator()

    failures: list[dict[str, str]] = []

    records: list[dict[str, Any]] = event.get("Records", [])
    for record in records:
        _ = record.get("receiptHandle") or record.get("receipt_handle")
        try:
            body = record.get("body")
            sqs_body = json.loads(body) if isinstance(body, str) else (body or {})
            domain_event = _extract_event_from_sns_envelope(sqs_body)

            if not domain_event or not validator.validate_event(domain_event):
                logger.warning("Skipping invalid event")
                continue

            event_type = domain_event.get("eventType")
            # Persist bronze
            if event_type.startswith("Policy"):
                # Try to ensure OpenSearch index exists (optional - graceful degradation)
                # Skip OpenSearch probe to avoid timeouts - focus on S3 reliability
                logger.info("Skipping OpenSearch probe - focusing on S3 reliability")

                key = f"policies/bronze/{event_type}/{domain_event['eventId']}.json"
                s3.put_object(
                    Bucket=settings.s3_bronze_bucket,
                    Key=key,
                    Body=json.dumps(domain_event).encode("utf-8"),
                    ContentType="application/json",
                )
                policy = (
                    domain_event.get("policy")
                    or domain_event.get("data", {}).get("policy")
                    or domain_event
                )
                doc_id = policy.get("policy_id") or policy.get("policyId")
                if doc_id:
                    doc = _normalize_policy(policy)
                    # Try OpenSearch with short timeout - graceful degradation
                    try:
                        # Set a short timeout to avoid Lambda timeouts
                        opensearch.index(
                            index=f"{settings.opensearch_index_prefix}-policies",
                            id=doc_id,
                            body=doc,
                            timeout="5s"  # Short timeout
                        )
                        logger.info(f"Indexed policy {doc_id} to OpenSearch")
                    except Exception as e:
                        logger.warning(f"OpenSearch indexing failed for policy {doc_id}: {e} - S3 storage successful")
            elif event_type.startswith("Claim"):
                key = f"claims/bronze/{event_type}/{domain_event['eventId']}.json"
                s3.put_object(
                    Bucket=settings.s3_bronze_bucket,
                    Key=key,
                    Body=json.dumps(domain_event).encode("utf-8"),
                    ContentType="application/json",
                )
                claim = (
                    domain_event.get("claim")
                    or domain_event.get("data", {}).get("claim")
                    or domain_event
                )
                doc_id = claim.get("claim_id") or claim.get("claimId")
                if doc_id:
                    doc = _normalize_claim(claim)
                    # Try OpenSearch with short timeout - graceful degradation
                    try:
                        # Set a short timeout to avoid Lambda timeouts
                        opensearch.index(
                            index=f"{settings.opensearch_index_prefix}-claims",
                            id=doc_id,
                            body=doc,
                            timeout="5s"  # Short timeout
                        )
                        logger.info(f"Indexed claim {doc_id} to OpenSearch")
                    except Exception as e:
                        logger.warning(f"OpenSearch indexing failed for claim {doc_id}: {e} - S3 storage successful")

        except Exception as e:
            logger.error("Record processing failed", error=str(e))
            if record.get("messageId"):
                failures.append({"itemIdentifier": record["messageId"]})

    # Partial batch response for SQS/Lambda to retry failed items only
    return {"batchItemFailures": failures}
