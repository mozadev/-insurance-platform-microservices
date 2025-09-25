output "policies_topic_arn" {
  value       = aws_sns_topic.policies.arn
  description = "Policies SNS topic ARN"
}

output "claims_topic_arn" {
  value       = aws_sns_topic.claims.arn
  description = "Claims SNS topic ARN"
}

output "policies_queue_url" {
  value       = aws_sqs_queue.policies.url
  description = "Policies SQS queue URL"
}

output "policies_queue_arn" {
  value       = aws_sqs_queue.policies.arn
  description = "Policies SQS queue ARN"
}

output "claims_queue_url" {
  value       = aws_sqs_queue.claims.url
  description = "Claims SQS queue URL"
}

output "claims_queue_arn" {
  value       = aws_sqs_queue.claims.arn
  description = "Claims SQS queue ARN"
}

output "policies_dlq_url" {
  value       = aws_sqs_queue.policies_dlq.url
  description = "Policies DLQ URL"
}

output "claims_dlq_url" {
  value       = aws_sqs_queue.claims_dlq.url
  description = "Claims DLQ URL"
}


