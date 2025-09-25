terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }
}

locals {
  name = var.name
}

# SNS Topics
resource "aws_sns_topic" "policies" {
  name = "${local.name}-policies-topic"

  tags = merge(var.tags, {
    Name        = "${local.name}-policies-topic"
    Environment = var.environment
  })
}

resource "aws_sns_topic" "claims" {
  name = "${local.name}-claims-topic"

  tags = merge(var.tags, {
    Name        = "${local.name}-claims-topic"
    Environment = var.environment
  })
}

# SQS Queues
resource "aws_sqs_queue" "policies" {
  name                       = "${local.name}-policies-queue"
  visibility_timeout_seconds = 30
  message_retention_seconds  = 1209600 # 14 days
  receive_wait_time_seconds  = 20      # Long polling

  tags = merge(var.tags, {
    Name        = "${local.name}-policies-queue"
    Environment = var.environment
  })
}

resource "aws_sqs_queue" "claims" {
  name                       = "${local.name}-claims-queue"
  visibility_timeout_seconds = 30
  message_retention_seconds  = 1209600 # 14 days
  receive_wait_time_seconds  = 20      # Long polling

  tags = merge(var.tags, {
    Name        = "${local.name}-claims-queue"
    Environment = var.environment
  })
}

# Dead Letter Queues
resource "aws_sqs_queue" "policies_dlq" {
  name                      = "${local.name}-policies-dlq"
  message_retention_seconds = 1209600 # 14 days

  tags = merge(var.tags, {
    Name        = "${local.name}-policies-dlq"
    Environment = var.environment
    Type        = "DLQ"
  })
}

resource "aws_sqs_queue" "claims_dlq" {
  name                      = "${local.name}-claims-dlq"
  message_retention_seconds = 1209600 # 14 days

  tags = merge(var.tags, {
    Name        = "${local.name}-claims-dlq"
    Environment = var.environment
    Type        = "DLQ"
  })
}

# Redrive Policy for main queues
resource "aws_sqs_queue_redrive_policy" "policies" {
  queue_url = aws_sqs_queue.policies.id
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.policies_dlq.arn
    maxReceiveCount     = 3
  })
}

resource "aws_sqs_queue_redrive_policy" "claims" {
  queue_url = aws_sqs_queue.claims.id
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.claims_dlq.arn
    maxReceiveCount     = 3
  })
}

# SNS to SQS Subscriptions
resource "aws_sns_topic_subscription" "policies_to_sqs" {
  topic_arn = aws_sns_topic.policies.arn
  protocol  = "sqs"
  endpoint  = aws_sqs_queue.policies.arn
}

resource "aws_sns_topic_subscription" "claims_to_sqs" {
  topic_arn = aws_sns_topic.claims.arn
  protocol  = "sqs"
  endpoint  = aws_sqs_queue.claims.arn
}

# SQS Queue Policy for SNS
resource "aws_sqs_queue_policy" "policies" {
  queue_url = aws_sqs_queue.policies.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "sns.amazonaws.com"
        }
        Action   = "sqs:SendMessage"
        Resource = aws_sqs_queue.policies.arn
        Condition = {
          ArnEquals = {
            "aws:SourceArn" = aws_sns_topic.policies.arn
          }
        }
      }
    ]
  })
}

resource "aws_sqs_queue_policy" "claims" {
  queue_url = aws_sqs_queue.claims.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "sns.amazonaws.com"
        }
        Action   = "sqs:SendMessage"
        Resource = aws_sqs_queue.claims.arn
        Condition = {
          ArnEquals = {
            "aws:SourceArn" = aws_sns_topic.claims.arn
          }
        }
      }
    ]
  })
}
