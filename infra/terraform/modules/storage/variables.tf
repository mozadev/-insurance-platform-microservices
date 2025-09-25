variable "name" {
  type        = string
  description = "Name prefix for all resources"
}

variable "environment" {
  type        = string
  description = "Environment name"
}

variable "tags" {
  type        = map(string)
  description = "Tags to apply to all resources"
  default     = {}
}
