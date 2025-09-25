output "collection_endpoint" {
  value       = aws_opensearchserverless_collection.main.collection_endpoint
  description = "OpenSearch Serverless collection endpoint"
}

output "collection_arn" {
  value       = aws_opensearchserverless_collection.main.arn
  description = "OpenSearch Serverless collection ARN"
}

output "collection_id" {
  value       = aws_opensearchserverless_collection.main.id
  description = "OpenSearch Serverless collection ID"
}

output "dashboard_endpoint" {
  value       = aws_opensearchserverless_collection.main.dashboard_endpoint
  description = "OpenSearch Dashboards endpoint"
}
