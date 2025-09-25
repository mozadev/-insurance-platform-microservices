output "bronze_bucket_name" {
  value       = aws_s3_bucket.bronze.bucket
  description = "Bronze S3 bucket name"
}

output "bronze_bucket_arn" {
  value       = aws_s3_bucket.bronze.arn
  description = "Bronze S3 bucket ARN"
}

output "silver_bucket_name" {
  value       = aws_s3_bucket.silver.bucket
  description = "Silver S3 bucket name"
}

output "silver_bucket_arn" {
  value       = aws_s3_bucket.silver.arn
  description = "Silver S3 bucket ARN"
}
