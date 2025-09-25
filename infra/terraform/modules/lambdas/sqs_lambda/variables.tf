variable "function_name" {
  type        = string
  description = "Lambda function name"
}

variable "role_name_prefix" {
  type        = string
  description = "Prefix for IAM role name"
  default     = "ingest"
}

variable "image_uri" {
  type        = string
  description = "ECR image URI for Lambda"
}

variable "queue_arns" {
  type        = list(string)
  description = "List of SQS queue ARNs to subscribe"
}

variable "s3_bronze_bucket" {
  type        = string
  description = "Bronze S3 bucket name"
}

variable "s3_silver_bucket" {
  type        = string
  description = "Silver S3 bucket name (optional)"
  default     = null
}

variable "opensearch_domain_arn" {
  type        = string
  description = "OpenSearch domain ARN for access policy"
}

variable "environment" {
  type        = map(string)
  description = "Environment variables for Lambda"
  default     = {}
}

variable "timeout_seconds" {
  type        = number
  description = "Lambda timeout"
  default     = 30
}

variable "memory_mb" {
  type        = number
  description = "Lambda memory"
  default     = 512
}

variable "reserved_concurrency" {
  type        = number
  description = "Reserved concurrency"
  default     = -1
}

variable "batch_size" {
  type        = number
  description = "SQS batch size"
  default     = 10
}

variable "maximum_batching_window_in_seconds" {
  type        = number
  description = "Max batching window"
  default     = 1
}

variable "maximum_concurrency" {
  type        = number
  description = "Max concurrent batches (per mapping)"
  default     = 5
}

variable "maximum_retry_attempts" {
  type        = number
  description = "Max retry attempts for failed batches"
  default     = 2
}

variable "create_vpc_config" {
  type        = bool
  description = "Whether to attach VPC config"
  default     = false
}

variable "subnet_ids" {
  type        = list(string)
  description = "Subnet IDs for Lambda in VPC"
  default     = []
}

variable "security_group_ids" {
  type        = list(string)
  description = "Security group IDs for Lambda"
  default     = []
}

variable "enable_xray" {
  type        = bool
  description = "Enable X-Ray tracing"
  default     = true
}

variable "log_retention_days" {
  type        = number
  description = "CloudWatch Logs retention"
  default     = 14
}

variable "tags" {
  type        = map(string)
  description = "Resource tags"
  default     = {}
}


