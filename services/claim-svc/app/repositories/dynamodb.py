"""DynamoDB repository for claim service."""

import uuid
from datetime import datetime
from typing import List, Optional

import boto3
from botocore.exceptions import ClientError
from pydantic import ValidationError

from ...shared.logging import LoggerMixin
from ..models import Claim, ClaimCreate, ClaimUpdate


class ClaimRepository(LoggerMixin):
    """Repository for claim data access."""
    
    def __init__(self, dynamodb_client, table_name: str):
        self.dynamodb = dynamodb_client
        self.table_name = table_name
    
    def create_claim(self, claim_data: ClaimCreate) -> Claim:
        """Create a new claim."""
        claim_id = f"CLAIM-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.utcnow()
        
        claim = Claim(
            claim_id=claim_id,
            created_at=now,
            updated_at=now,
            **claim_data.dict(exclude={'idempotency_key'})
        )
        
        try:
            # Store in DynamoDB
            self.dynamodb.put_item(
                TableName=self.table_name,
                Item={
                    'PK': {'S': f'CLAIM#{claim_id}'},
                    'SK': {'S': f'META#{int(now.timestamp())}'},
                    'ClaimId': {'S': claim_id},
                    'PolicyId': {'S': claim.policy_id},
                    'CustomerId': {'S': claim.customer_id},
                    'Status': {'S': claim.status},
                    'Amount': {'N': str(claim.amount)},
                    'OccurredAt': {'S': claim.occurred_at.isoformat()},
                    'Description': {'S': claim.description or ''},
                    'Category': {'S': claim.category},
                    'CreatedAt': {'S': claim.created_at.isoformat()},
                    'UpdatedAt': {'S': claim.updated_at.isoformat()},
                    'GSI1PK': {'S': f'POL#{claim.policy_id}'},
                    'GSI1SK': {'S': f'STATUS#{claim.status}#{int(now.timestamp())}'},
                    'TTL': {'N': str(int((now.timestamp() + 86400 * 365 * 7)))},  # 7 years
                }
            )
            
            self.logger.info("Claim created successfully", claim_id=claim_id)
            return claim
            
        except ClientError as e:
            self.logger.error("Failed to create claim", error=str(e), claim_id=claim_id)
            raise RuntimeError(f"Failed to create claim: {str(e)}")
    
    def get_claim(self, claim_id: str) -> Optional[Claim]:
        """Get a claim by ID."""
        try:
            response = self.dynamodb.get_item(
                TableName=self.table_name,
                Key={
                    'PK': {'S': f'CLAIM#{claim_id}'},
                    'SK': {'S': f'META#{int(datetime.utcnow().timestamp())}'}
                }
            )
            
            if 'Item' not in response:
                return None
            
            item = response['Item']
            return Claim(
                claim_id=item['ClaimId']['S'],
                policy_id=item['PolicyId']['S'],
                customer_id=item['CustomerId']['S'],
                status=item['Status']['S'],
                amount=float(item['Amount']['N']),
                occurred_at=datetime.fromisoformat(item['OccurredAt']['S']),
                description=item.get('Description', {}).get('S') or None,
                category=item['Category']['S'],
                created_at=datetime.fromisoformat(item['CreatedAt']['S']),
                updated_at=datetime.fromisoformat(item['UpdatedAt']['S'])
            )
            
        except (ClientError, KeyError, ValidationError) as e:
            self.logger.error("Failed to get claim", error=str(e), claim_id=claim_id)
            return None
    
    def get_policy_claims(
        self, 
        policy_id: str, 
        limit: int = 20, 
        next_token: Optional[str] = None
    ) -> tuple[List[Claim], Optional[str]]:
        """Get claims for a policy."""
        try:
            query_params = {
                'TableName': self.table_name,
                'IndexName': 'GSI1',
                'KeyConditionExpression': 'GSI1PK = :policy_id',
                'ExpressionAttributeValues': {
                    ':policy_id': {'S': f'POL#{policy_id}'}
                },
                'ScanIndexForward': False,  # Most recent first
                'Limit': limit
            }
            
            if next_token:
                query_params['ExclusiveStartKey'] = eval(next_token)  # In production, use proper token handling
            
            response = self.dynamodb.query(**query_params)
            
            claims = []
            for item in response.get('Items', []):
                try:
                    claim = Claim(
                        claim_id=item['ClaimId']['S'],
                        policy_id=item['PolicyId']['S'],
                        customer_id=item['CustomerId']['S'],
                        status=item['Status']['S'],
                        amount=float(item['Amount']['N']),
                        occurred_at=datetime.fromisoformat(item['OccurredAt']['S']),
                        description=item.get('Description', {}).get('S') or None,
                        category=item['Category']['S'],
                        created_at=datetime.fromisoformat(item['CreatedAt']['S']),
                        updated_at=datetime.fromisoformat(item['UpdatedAt']['S'])
                    )
                    claims.append(claim)
                except (KeyError, ValidationError) as e:
                    self.logger.warning("Skipping invalid claim item", error=str(e))
                    continue
            
            next_token = None
            if 'LastEvaluatedKey' in response:
                next_token = str(response['LastEvaluatedKey'])
            
            return claims, next_token
            
        except ClientError as e:
            self.logger.error("Failed to get policy claims", error=str(e), policy_id=policy_id)
            raise RuntimeError(f"Failed to get policy claims: {str(e)}")
    
    def update_claim(self, claim_id: str, update_data: ClaimUpdate) -> Optional[Claim]:
        """Update a claim."""
        # First get the current claim
        current_claim = self.get_claim(claim_id)
        if not current_claim:
            return None
        
        # Merge updates
        update_dict = update_data.dict(exclude_unset=True)
        updated_claim = current_claim.copy(update=update_dict)
        updated_claim.updated_at = datetime.utcnow()
        
        try:
            # Update in DynamoDB
            update_expression = "SET UpdatedAt = :updated_at"
            expression_values = {':updated_at': {'S': updated_claim.updated_at.isoformat()}}
            
            for field, value in update_dict.items():
                if field == 'occurred_at':
                    update_expression += f", OccurredAt = :{field}"
                    expression_values[f':{field}'] = {'S': value.isoformat()}
                elif field in ['amount']:
                    update_expression += f", {field.capitalize()} = :{field}"
                    expression_values[f':{field}'] = {'N': str(value)}
                else:
                    update_expression += f", {field.capitalize()} = :{field}"
                    expression_values[f':{field}'] = {'S': str(value)}
            
            self.dynamodb.update_item(
                TableName=self.table_name,
                Key={
                    'PK': {'S': f'CLAIM#{claim_id}'},
                    'SK': {'S': f'META#{int(datetime.utcnow().timestamp())}'}
                },
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values,
                ConditionExpression='attribute_exists(PK)'
            )
            
            self.logger.info("Claim updated successfully", claim_id=claim_id)
            return updated_claim
            
        except ClientError as e:
            self.logger.error("Failed to update claim", error=str(e), claim_id=claim_id)
            raise RuntimeError(f"Failed to update claim: {str(e)}")
