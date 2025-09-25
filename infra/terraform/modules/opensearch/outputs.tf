output "domain_arn" {
  value       = aws_opensearch_domain.main.arn
  description = "OpenSearch domain ARN"
}

output "domain_endpoint" {
  value       = aws_opensearch_domain.main.endpoint
  description = "OpenSearch domain endpoint"
}

output "domain_id" {
  value       = aws_opensearch_domain.main.domain_id
  description = "OpenSearch domain ID"
}

output "dashboard_endpoint" {
  value       = aws_opensearch_domain.main.dashboard_endpoint
  description = "OpenSearch Dashboards endpoint"
}


