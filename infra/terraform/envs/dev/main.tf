terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }
  
  backend "s3" {
    bucket = "insurance-microservices-terraform-state-202235431150"
    key    = "dev/terraform.tfstate"
    region = "us-east-1"
  }
}

provider "aws" {
  region = var.aws_region
}

# Variables
variable "aws_region" {
  type        = string
  description = "AWS region"
  default     = "us-east-1"
}

variable "environment" {
  type        = string
  description = "Environment name"
  default     = "dev"
}

variable "lambda_image_uri" {
  type        = string
  description = "ECR image URI for Lambda"
}

variable "opensearch_master_password" {
  type        = string
  description = "OpenSearch master password"
  sensitive   = true
}

variable "tags" {
  type        = map(string)
  description = "Tags to apply to all resources"
  default = {
    Project     = "insurance-platform"
    Environment = "dev"
    ManagedBy   = "terraform"
  }
}

# Networking Module
module "networking" {
  source = "../../modules/networking"

  name     = "ins-${var.environment}"
  vpc_cidr = "10.0.0.0/16"
  az_count = 2
  tags     = var.tags
}

# Storage Module
module "storage" {
  source = "../../modules/storage"

  name        = "ins-${var.environment}"
  environment = var.environment
  tags        = var.tags
}

# Messaging Module
module "messaging" {
  source = "../../modules/messaging"

  name        = "ins-${var.environment}"
  environment = var.environment
  tags        = var.tags
}

# OpenSearch Serverless Module
module "opensearch" {
  source = "../../modules/opensearch"

  name        = "ins-${var.environment}"
  environment = var.environment
  tags        = var.tags
  
  aws_region            = var.aws_region
  subnet_ids            = module.networking.private_subnet_ids
  security_group_ids    = [module.networking.opensearch_security_group_id]
  master_user_password  = var.opensearch_master_password
}

# Ingest Lambda Module
module "ingest_lambda" {
  source = "../../modules/lambdas/sqs_lambda"

  function_name           = "ins-${var.environment}-ingest-sqs"
  role_name_prefix        = "ins-${var.environment}"
  image_uri               = var.lambda_image_uri
  queue_arns              = [module.messaging.policies_queue_arn, module.messaging.claims_queue_arn]
  s3_bronze_bucket        = module.storage.bronze_bucket_name
  s3_silver_bucket        = module.storage.silver_bucket_name
  opensearch_domain_arn   = module.opensearch.domain_arn

  environment = {
    SERVICE_NAME              = "ingest-svc"
    SERVICE_PORT              = "8000"
    LOG_LEVEL                 = "INFO"
    OPENSEARCH_INDEX_PREFIX   = "ins"
    OPENSEARCH_ENDPOINT       = module.opensearch.domain_endpoint
    OPENSEARCH_USERNAME       = "admin"
    OPENSEARCH_PASSWORD       = var.opensearch_master_password
    S3_BRONZE_BUCKET          = module.storage.bronze_bucket_name
    S3_SILVER_BUCKET          = module.storage.silver_bucket_name
    POLICIES_TOPIC_ARN        = module.messaging.policies_topic_arn
    CLAIMS_TOPIC_ARN          = module.messaging.claims_topic_arn
    POLICIES_QUEUE_URL        = module.messaging.policies_queue_url
    CLAIMS_QUEUE_URL          = module.messaging.claims_queue_url
  }

  timeout_seconds                        = 30
  memory_mb                              = 512
  reserved_concurrency                   = -1
  batch_size                             = 10
  maximum_batching_window_in_seconds     = 1
  maximum_concurrency                    = 5
  maximum_retry_attempts                 = 2
  # create_vpc_config                      = true  # Temporarily disabled for debugging
  subnet_ids                             = module.networking.private_subnet_ids
  security_group_ids                     = [module.networking.lambda_security_group_id]
  enable_xray                            = true
  log_retention_days                     = 14

  tags = var.tags
}

# Outputs
output "vpc_id" {
  value       = module.networking.vpc_id
  description = "VPC ID"
}

output "public_subnet_ids" {
  value       = module.networking.public_subnet_ids
  description = "Public subnet IDs"
}

output "private_subnet_ids" {
  value       = module.networking.private_subnet_ids
  description = "Private subnet IDs"
}

output "bronze_bucket_name" {
  value       = module.storage.bronze_bucket_name
  description = "Bronze S3 bucket name"
}

output "silver_bucket_name" {
  value       = module.storage.silver_bucket_name
  description = "Silver S3 bucket name"
}

output "policies_topic_arn" {
  value       = module.messaging.policies_topic_arn
  description = "Policies SNS topic ARN"
}

output "claims_topic_arn" {
  value       = module.messaging.claims_topic_arn
  description = "Claims SNS topic ARN"
}

output "policies_queue_url" {
  value       = module.messaging.policies_queue_url
  description = "Policies SQS queue URL"
}

output "claims_queue_url" {
  value       = module.messaging.claims_queue_url
  description = "Claims SQS queue URL"
}

output "opensearch_domain_endpoint" {
  value       = module.opensearch.domain_endpoint
  description = "OpenSearch domain endpoint"
}

output "opensearch_dashboard_endpoint" {
  value       = module.opensearch.dashboard_endpoint
  description = "OpenSearch Dashboards endpoint"
}

output "ingest_lambda_arn" {
  value       = module.ingest_lambda.lambda_function_arn
  description = "Ingest Lambda function ARN"
}


