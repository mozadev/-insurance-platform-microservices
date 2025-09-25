"""DynamoDB repository for policy service."""

import uuid
from datetime import datetime
from typing import List, Optional

import boto3
from botocore.exceptions import ClientError
from pydantic import ValidationError

from ...shared.logging import LoggerMixin
from ..models import Policy, PolicyCreate, PolicyUpdate


class PolicyRepository(LoggerMixin):
    """Repository for policy data access."""
    
    def __init__(self, dynamodb_client, table_name: str):
        self.dynamodb = dynamodb_client
        self.table_name = table_name
    
    def create_policy(self, policy_data: PolicyCreate) -> Policy:
        """Create a new policy."""
        policy_id = f"POL-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.utcnow()
        
        policy = Policy(
            policy_id=policy_id,
            created_at=now,
            updated_at=now,
            **policy_data.dict()
        )
        
        try:
            # Store in DynamoDB
            self.dynamodb.put_item(
                TableName=self.table_name,
                Item={
                    'PK': {'S': f'POL#{policy_id}'},
                    'SK': {'S': f'META#{int(now.timestamp())}'},
                    'PolicyId': {'S': policy_id},
                    'CustomerId': {'S': policy.customer_id},
                    'Status': {'S': policy.status},
                    'Premium': {'N': str(policy.premium)},
                    'EffectiveDate': {'S': policy.effective_date.isoformat()},
                    'ExpirationDate': {'S': policy.expiration_date.isoformat()},
                    'CoverageType': {'S': policy.coverage_type},
                    'Deductible': {'N': str(policy.deductible)},
                    'CoverageLimit': {'N': str(policy.coverage_limit)},
                    'CreatedAt': {'S': policy.created_at.isoformat()},
                    'UpdatedAt': {'S': policy.updated_at.isoformat()},
                    'GSI1PK': {'S': f'CUST#{policy.customer_id}'},
                    'GSI1SK': {'S': f'POL#{policy_id}#{int(now.timestamp())}'},
                    'TTL': {'N': str(int((now.timestamp() + 86400 * 365 * 10)))},  # 10 years
                }
            )
            
            self.logger.info("Policy created successfully", policy_id=policy_id)
            return policy
            
        except ClientError as e:
            self.logger.error("Failed to create policy", error=str(e), policy_id=policy_id)
            raise RuntimeError(f"Failed to create policy: {str(e)}") from e
    
    def get_policy(self, policy_id: str) -> Optional[Policy]:
        """Get a policy by ID."""
        try:
            response = self.dynamodb.get_item(
                TableName=self.table_name,
                Key={
                    'PK': {'S': f'POL#{policy_id}'},
                    'SK': {'S': f'META#{int(datetime.utcnow().timestamp())}'}
                }
            )
            
            if 'Item' not in response:
                return None
            
            item = response['Item']
            return Policy(
                policy_id=item['PolicyId']['S'],
                customer_id=item['CustomerId']['S'],
                status=item['Status']['S'],
                premium=float(item['Premium']['N']),
                effective_date=datetime.fromisoformat(item['EffectiveDate']['S']).date(),
                expiration_date=datetime.fromisoformat(item['ExpirationDate']['S']).date(),
                coverage_type=item['CoverageType']['S'],
                deductible=float(item['Deductible']['N']),
                coverage_limit=float(item['CoverageLimit']['N']),
                created_at=datetime.fromisoformat(item['CreatedAt']['S']),
                updated_at=datetime.fromisoformat(item['UpdatedAt']['S'])
            )
            
        except (ClientError, KeyError, ValidationError) as e:
            self.logger.error("Failed to get policy", error=str(e), policy_id=policy_id)
            return None
    
    def get_customer_policies(
        self, 
        customer_id: str, 
        limit: int = 20, 
        next_token: Optional[str] = None
    ) -> tuple[List[Policy], Optional[str]]:
        """Get policies for a customer."""
        try:
            query_params = {
                'TableName': self.table_name,
                'IndexName': 'GSI1',
                'KeyConditionExpression': 'GSI1PK = :customer_id',
                'ExpressionAttributeValues': {
                    ':customer_id': {'S': f'CUST#{customer_id}'}
                },
                'ScanIndexForward': False,  # Most recent first
                'Limit': limit
            }
            
            if next_token:
                query_params['ExclusiveStartKey'] = eval(next_token)  # In production, use proper token handling
            
            response = self.dynamodb.query(**query_params)
            
            policies = []
            for item in response.get('Items', []):
                try:
                    policy = Policy(
                        policy_id=item['PolicyId']['S'],
                        customer_id=item['CustomerId']['S'],
                        status=item['Status']['S'],
                        premium=float(item['Premium']['N']),
                        effective_date=datetime.fromisoformat(item['EffectiveDate']['S']).date(),
                        expiration_date=datetime.fromisoformat(item['ExpirationDate']['S']).date(),
                        coverage_type=item['CoverageType']['S'],
                        deductible=float(item['Deductible']['N']),
                        coverage_limit=float(item['CoverageLimit']['N']),
                        created_at=datetime.fromisoformat(item['CreatedAt']['S']),
                        updated_at=datetime.fromisoformat(item['UpdatedAt']['S'])
                    )
                    policies.append(policy)
                except (KeyError, ValidationError) as e:
                    self.logger.warning("Skipping invalid policy item", error=str(e))
                    continue
            
            next_token = None
            if 'LastEvaluatedKey' in response:
                next_token = str(response['LastEvaluatedKey'])
            
            return policies, next_token
            
        except ClientError as e:
            self.logger.error("Failed to get customer policies", error=str(e), customer_id=customer_id)
            raise RuntimeError(f"Failed to get customer policies: {str(e)}") from e
    
    def update_policy(self, policy_id: str, update_data: PolicyUpdate) -> Optional[Policy]:
        """Update a policy."""
        # First get the current policy
        current_policy = self.get_policy(policy_id)
        if not current_policy:
            return None
        
        # Merge updates
        update_dict = update_data.dict(exclude_unset=True)
        updated_policy = current_policy.copy(update=update_dict)
        updated_policy.updated_at = datetime.utcnow()
        
        try:
            # Update in DynamoDB
            update_expression = "SET UpdatedAt = :updated_at"
            expression_values = {':updated_at': {'S': updated_policy.updated_at.isoformat()}}
            
            for field, value in update_dict.items():
                if field == 'effective_date':
                    update_expression += f", EffectiveDate = :{field}"
                    expression_values[f':{field}'] = {'S': value.isoformat()}
                elif field == 'expiration_date':
                    update_expression += f", ExpirationDate = :{field}"
                    expression_values[f':{field}'] = {'S': value.isoformat()}
                elif field in ['premium', 'deductible', 'coverage_limit']:
                    update_expression += f", {field.capitalize()} = :{field}"
                    expression_values[f':{field}'] = {'N': str(value)}
                else:
                    update_expression += f", {field.capitalize()} = :{field}"
                    expression_values[f':{field}'] = {'S': str(value)}
            
            self.dynamodb.update_item(
                TableName=self.table_name,
                Key={
                    'PK': {'S': f'POL#{policy_id}'},
                    'SK': {'S': f'META#{int(datetime.utcnow().timestamp())}'}
                },
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values,
                ConditionExpression='attribute_exists(PK)'
            )
            
            self.logger.info("Policy updated successfully", policy_id=policy_id)
            return updated_policy
            
        except ClientError as e:
            self.logger.error("Failed to update policy", error=str(e), policy_id=policy_id)
            raise RuntimeError(f"Failed to update policy: {str(e)}") from e
