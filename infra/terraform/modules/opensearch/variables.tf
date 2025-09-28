variable "name" {
  type        = string
  description = "Name prefix for all resources"
}

variable "environment" {
  type        = string
  description = "Environment name"
}

variable "aws_region" {
  type        = string
  description = "AWS region for resource ARNs"
}

variable "subnet_ids" {
  type        = list(string)
  description = "Subnet IDs for OpenSearch domain"
}

variable "security_group_ids" {
  type        = list(string)
  description = "Security group IDs for OpenSearch domain"
}

variable "lambda_role_arns" {
  type        = list(string)
  description = "Lambda role ARNs that can access OpenSearch"
  default     = []
}

variable "instance_type" {
  type        = string
  description = "OpenSearch instance type"
  default     = "t3.small.elasticsearch"
}

variable "instance_count" {
  type        = number
  description = "Number of OpenSearch instances"
  default     = 2
}

variable "dedicated_master_enabled" {
  type        = bool
  description = "Enable dedicated master nodes"
  default     = false
}


variable "zone_awareness_enabled" {
  type        = bool
  description = "Enable zone awareness"
  default     = true
}

variable "az_count" {
  type        = number
  description = "Number of availability zones"
  default     = 2
}

variable "volume_size" {
  type        = number
  description = "EBS volume size in GB"
  default     = 20
}

variable "master_user_name" {
  type        = string
  description = "Master username"
  default     = "admin"
}

variable "master_user_password" {
  type        = string
  description = "Master password"
  sensitive   = true
}

variable "log_retention_days" {
  type        = number
  description = "CloudWatch log retention in days"
  default     = 14
}

variable "tags" {
  type        = map(string)
  description = "Tags to apply to all resources"
  default     = {}
}


