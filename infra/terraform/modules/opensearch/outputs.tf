output "domain_arn" {
  value       = aws_elasticsearch_domain.main.arn
  description = "Elasticsearch domain ARN"
}

output "domain_endpoint" {
  value       = aws_elasticsearch_domain.main.endpoint
  description = "Elasticsearch domain endpoint"
}

output "domain_id" {
  value       = aws_elasticsearch_domain.main.domain_id
  description = "Elasticsearch domain ID"
}

output "kibana_endpoint" {
  value       = aws_elasticsearch_domain.main.kibana_endpoint
  description = "Kibana endpoint"
}


