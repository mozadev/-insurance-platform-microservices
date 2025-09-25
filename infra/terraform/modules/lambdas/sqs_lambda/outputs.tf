output "lambda_function_arn" {
  value       = aws_lambda_function.this.arn
  description = "Lambda function ARN"
}

output "lambda_role_arn" {
  value       = aws_iam_role.lambda_role.arn
  description = "IAM role ARN for the Lambda"
}


