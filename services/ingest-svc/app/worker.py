"""Background SQS worker for ingest-svc."""

import asyncio
import json
from typing import Any, Dict

from ...shared.config import get_settings
from ...shared.aws import get_sqs_client, get_s3_client, get_opensearch_client
from ...shared.events import EventValidator
from ...shared.logging import LoggerMixin


class IngestWorker(LoggerMixin):
    """Consumes SQS messages, stores to S3 (bronze) and indexes to OpenSearch."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.sqs = get_sqs_client(self.settings)
        self.s3 = get_s3_client(self.settings)
        self.opensearch = get_opensearch_client(self.settings)
        self.validator = EventValidator()
        self._stopping = asyncio.Event()

    async def run(self) -> None:
        """Main worker loop."""
        poll_interval_seconds = 2
        queues = [
            self.settings.policies_queue_url,
            self.settings.claims_queue_url,
        ]

        while not self._stopping.is_set():
            for queue_url in queues:
                try:
                    messages = self.sqs.receive_message(
                        QueueUrl=queue_url,
                        MaxNumberOfMessages=5,
                        WaitTimeSeconds=1,
                        MessageAttributeNames=["All"],
                    ).get("Messages", [])

                    for msg in messages:
                        receipt_handle = msg["ReceiptHandle"]
                        body = json.loads(msg["Body"]) if isinstance(msg.get("Body"), str) else msg.get("Body", {})
                        event = self._extract_event_from_sns_envelope(body)
                        await self._process_event(event)
                        # delete after success
                        self.sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt_handle)
                except Exception as e:
                    self.logger.error("Worker loop error", error=str(e), queue=queue_url)
                    continue

            try:
                await asyncio.wait_for(self._stopping.wait(), timeout=poll_interval_seconds)
            except asyncio.TimeoutError:
                pass

    async def stop(self) -> None:
        self._stopping.set()

    def _extract_event_from_sns_envelope(self, sns_body: Dict[str, Any]) -> Dict[str, Any]:
        # LocalStack/SNS via SQS delivers message with Records for SNS
        # We expect sns_body to already be SNS envelope or raw event
        if "Message" in sns_body:
            try:
                return json.loads(sns_body["Message"])  # event sent by publisher
            except json.JSONDecodeError:
                return {}
        if "Records" in sns_body and sns_body["Records"]:
            record = sns_body["Records"][0]
            message = record.get("Sns", {}).get("Message")
            if message:
                try:
                    return json.loads(message)
                except json.JSONDecodeError:
                    return {}
        return sns_body

    async def _process_event(self, event: Dict[str, Any]) -> None:
        if not event or not self.validator.validate_event(event):
            self.logger.warning("Skipping invalid event")
            return

        event_type = event.get("eventType")
        if event_type in {"PolicyCreated", "PolicyUpdated"}:
            await self._store_bronze("policies", event)
            await self._index_policy(event)
        elif event_type in {"ClaimCreated", "ClaimUpdated"}:
            await self._store_bronze("claims", event)
            await self._index_claim(event)

    async def _store_bronze(self, domain: str, event: Dict[str, Any]) -> None:
        key = f"{domain}/bronze/{event['eventType']}/{event['eventId']}.json"
        self.s3.put_object(
            Bucket=self.settings.s3_bronze_bucket,
            Key=key,
            Body=json.dumps(event).encode("utf-8"),
            ContentType="application/json",
        )
        self.logger.info("Stored event to S3 bronze", key=key, bucket=self.settings.s3_bronze_bucket)

    async def _index_policy(self, event: Dict[str, Any]) -> None:
        policy = event.get("policy") or event.get("data", {}).get("policy") or event
        doc_id = policy.get("policy_id") or policy.get("policyId")
        if not doc_id:
            return
        index = f"{self.settings.opensearch_index_prefix}-policies"
        body = self._normalize_policy(policy)
        self.opensearch.index(index=index, id=doc_id, body=body)
        self.logger.info("Indexed policy document", index=index, id=doc_id)

    async def _index_claim(self, event: Dict[str, Any]) -> None:
        claim = event.get("claim") or event.get("data", {}).get("claim") or event
        doc_id = claim.get("claim_id") or claim.get("claimId")
        if not doc_id:
            return
        index = f"{self.settings.opensearch_index_prefix}-claims"
        body = self._normalize_claim(claim)
        self.opensearch.index(index=index, id=doc_id, body=body)
        self.logger.info("Indexed claim document", index=index, id=doc_id)

    def _normalize_policy(self, p: Dict[str, Any]) -> Dict[str, Any]:
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

    def _normalize_claim(self, c: Dict[str, Any]) -> Dict[str, Any]:
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


