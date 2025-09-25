#!/bin/bash

# Bootstrap script to create AWS resources in LocalStack

set -e

echo "🚀 Bootstrapping AWS resources in LocalStack..."

# Wait for LocalStack to be ready
echo "⏳ Waiting for LocalStack to be ready..."
until curl -s http://localhost:4566/_localstack/health | grep -q '"s3": "available"'; do
  echo "Waiting for LocalStack..."
  sleep 2
done

echo "✅ LocalStack is ready!"

# Set AWS CLI to use LocalStack
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1
export AWS_ENDPOINT_URL=http://localhost:4566

# Create S3 buckets
echo "📦 Creating S3 buckets..."
aws s3 mb s3://ins-bronze
aws s3 mb s3://ins-silver

# Create DynamoDB tables
echo "🗄️ Creating DynamoDB tables..."

# Policy service tables
aws dynamodb create-table \
  --table-name policy-svc_policies \
  --attribute-definitions \
    AttributeName=PK,AttributeType=S \
    AttributeName=SK,AttributeType=S \
    AttributeName=GSI1PK,AttributeType=S \
    AttributeName=GSI1SK,AttributeType=S \
  --key-schema \
    AttributeName=PK,KeyType=HASH \
    AttributeName=SK,KeyType=RANGE \
  --global-secondary-indexes \
    IndexName=GSI1,KeySchema=[{AttributeName=GSI1PK,KeyType=HASH},{AttributeName=GSI1SK,KeyType=RANGE}],Projection={ProjectionType=ALL} \
  --billing-mode PAY_PER_REQUEST

aws dynamodb create-table \
  --table-name policy-svc_outbox \
  --attribute-definitions \
    AttributeName=eventId,AttributeType=S \
  --key-schema \
    AttributeName=eventId,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --time-to-live-specification \
    AttributeName=ttl,Enabled=true

# Claim service tables
aws dynamodb create-table \
  --table-name claim-svc_claims \
  --attribute-definitions \
    AttributeName=PK,AttributeType=S \
    AttributeName=SK,AttributeType=S \
    AttributeName=GSI1PK,AttributeType=S \
    AttributeName=GSI1SK,AttributeType=S \
  --key-schema \
    AttributeName=PK,KeyType=HASH \
    AttributeName=SK,KeyType=RANGE \
  --global-secondary-indexes \
    IndexName=GSI1,KeySchema=[{AttributeName=GSI1PK,KeyType=HASH},{AttributeName=GSI1SK,KeyType=RANGE}],Projection={ProjectionType=ALL} \
  --billing-mode PAY_PER_REQUEST

aws dynamodb create-table \
  --table-name claim-svc_outbox \
  --attribute-definitions \
    AttributeName=eventId,AttributeType=S \
  --key-schema \
    AttributeName=eventId,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --time-to-live-specification \
    AttributeName=ttl,Enabled=true

aws dynamodb create-table \
  --table-name claim-svc_idem \
  --attribute-definitions \
    AttributeName=PK,AttributeType=S \
    AttributeName=SK,AttributeType=S \
  --key-schema \
    AttributeName=PK,KeyType=HASH \
    AttributeName=SK,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST \
  --time-to-live-specification \
    AttributeName=ttl,Enabled=true

# Ingest service tables
aws dynamodb create-table \
  --table-name ingest-svc_idem \
  --attribute-definitions \
    AttributeName=PK,AttributeType=S \
    AttributeName=SK,AttributeType=S \
  --key-schema \
    AttributeName=PK,KeyType=HASH \
    AttributeName=SK,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST \
  --time-to-live-specification \
    AttributeName=ttl,Enabled=true

# Create SNS topics
echo "📢 Creating SNS topics..."
aws sns create-topic --name policies-topic
aws sns create-topic --name claims-topic

# Create SQS queues
echo "📬 Creating SQS queues..."

# Policies queue
aws sqs create-queue \
  --queue-name policies-queue \
  --attributes VisibilityTimeoutSeconds=30,MessageRetentionPeriod=1209600

# Claims queue
aws sqs create-queue \
  --queue-name claims-queue \
  --attributes VisibilityTimeoutSeconds=30,MessageRetentionPeriod=1209600

# DLQ for policies
aws sqs create-queue \
  --queue-name policies-dlq \
  --attributes MessageRetentionPeriod=1209600

# DLQ for claims
aws sqs create-queue \
  --queue-name claims-dlq \
  --attributes MessageRetentionPeriod=1209600

# Subscribe queues to topics
echo "🔗 Subscribing queues to topics..."

POLICIES_TOPIC_ARN=$(aws sns list-topics --query 'Topics[?contains(TopicArn, `policies-topic`)].TopicArn' --output text)
CLAIMS_TOPIC_ARN=$(aws sns list-topics --query 'Topics[?contains(TopicArn, `claims-topic`)].TopicArn' --output text)

POLICIES_QUEUE_URL=$(aws sqs get-queue-url --queue-name policies-queue --query 'QueueUrl' --output text)
CLAIMS_QUEUE_URL=$(aws sqs get-queue-url --queue-name claims-queue --query 'QueueUrl' --output text)

aws sns subscribe \
  --topic-arn "$POLICIES_TOPIC_ARN" \
  --protocol sqs \
  --endpoint "$POLICIES_QUEUE_URL"

aws sns subscribe \
  --topic-arn "$CLAIMS_TOPIC_ARN" \
  --protocol sqs \
  --endpoint "$CLAIMS_QUEUE_URL"

# Set up DLQ redrive policy
echo "🔄 Setting up DLQ redrive policies..."

POLICIES_DLQ_URL=$(aws sqs get-queue-url --queue-name policies-dlq --query 'QueueUrl' --output text)
CLAIMS_DLQ_URL=$(aws sqs get-queue-url --queue-name claims-dlq --query 'QueueUrl' --output text)

aws sqs set-queue-attributes \
  --queue-url "$POLICIES_QUEUE_URL" \
  --attributes '{
    "RedrivePolicy": "{\"deadLetterTargetArn\":\"'$POLICIES_DLQ_URL'\",\"maxReceiveCount\":3}"
  }'

aws sqs set-queue-attributes \
  --queue-url "$CLAIMS_QUEUE_URL" \
  --attributes '{
    "RedrivePolicy": "{\"deadLetterTargetArn\":\"'$CLAIMS_DLQ_URL'\",\"maxReceiveCount\":3}"
  }'

# Create IAM roles and policies for services
echo "🔐 Creating IAM roles and policies..."

# Policy service role
aws iam create-role \
  --role-name PolicyServiceRole \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Principal": {"Service": "lambda.amazonaws.com"},
        "Action": "sts:AssumeRole"
      }
    ]
  }'

# Claim service role
aws iam create-role \
  --role-name ClaimServiceRole \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Principal": {"Service": "lambda.amazonaws.com"},
        "Action": "sts:AssumeRole"
      }
    ]
  }'

echo "✅ Bootstrap completed successfully!"
echo ""
echo "📋 Summary:"
echo "  - S3 buckets: ins-bronze, ins-silver"
echo "  - DynamoDB tables: policy-svc_policies, claim-svc_claims, etc."
echo "  - SNS topics: policies-topic, claims-topic"
echo "  - SQS queues: policies-queue, claims-queue (with DLQs)"
echo "  - IAM roles: PolicyServiceRole, ClaimServiceRole"
echo ""
echo "🎉 Ready to start the microservices!"
