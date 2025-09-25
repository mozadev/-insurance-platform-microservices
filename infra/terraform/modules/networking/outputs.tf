output "vpc_id" {
  value       = aws_vpc.main.id
  description = "VPC ID"
}

output "vpc_cidr_block" {
  value       = aws_vpc.main.cidr_block
  description = "VPC CIDR block"
}

output "public_subnet_ids" {
  value       = aws_subnet.public[*].id
  description = "Public subnet IDs"
}

output "private_subnet_ids" {
  value       = aws_subnet.private[*].id
  description = "Private subnet IDs"
}

output "lambda_security_group_id" {
  value       = aws_security_group.lambda.id
  description = "Security group ID for Lambda functions"
}

output "opensearch_security_group_id" {
  value       = aws_security_group.opensearch.id
  description = "Security group ID for OpenSearch"
}

output "alb_security_group_id" {
  value       = aws_security_group.alb.id
  description = "Security group ID for ALB"
}

output "ecs_security_group_id" {
  value       = aws_security_group.ecs.id
  description = "Security group ID for ECS"
}
