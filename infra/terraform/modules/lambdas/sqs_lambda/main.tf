terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }
}

locals {
  name = var.function_name
}

resource "aws_iam_role" "lambda_role" {
  name               = "${var.role_name_prefix}-${local.name}"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
  tags = var.tags
}

data "aws_iam_policy_document" "lambda_basic_logs" {
  statement {
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents"
    ]
    resources = ["*"]
  }
}

resource "aws_iam_policy" "lambda_basic_logs" {
  name   = "${local.name}-basic-logs"
  policy = data.aws_iam_policy_document.lambda_basic_logs.json
}

data "aws_iam_policy_document" "inline_min_permissions" {
  # SQS read/delete
  statement {
    effect = "Allow"
    actions = [
      "sqs:ReceiveMessage",
      "sqs:DeleteMessage",
      "sqs:GetQueueAttributes"
    ]
    resources = var.queue_arns
  }

  # S3 write to bronze (and optional silver)
  statement {
    effect = "Allow"
    actions = [
      "s3:PutObject",
      "s3:PutObjectAcl"
    ]
    resources = [
      "arn:aws:s3:::${var.s3_bronze_bucket}/*",
      var.s3_silver_bucket != null && var.s3_silver_bucket != "" ? "arn:aws:s3:::${var.s3_silver_bucket}/*" : null
    ]
    condition {
      test     = "StringNotEqualsIfExists"
      variable = "s3:x-amz-server-side-encryption"
      values   = ["aws:kms", "AES256"]
    }
  }

  # OpenSearch HTTP access (domain resource-level constraints vary per setup)
  statement {
    effect = "Allow"
    actions = [
      "es:ESHttpGet",
      "es:ESHttpPost",
      "es:ESHttpPut",
      "es:ESHttpDelete"
    ]
    resources = [
      var.opensearch_domain_arn,
      "${var.opensearch_domain_arn}/*"
    ]
  }

  # VPC permissions for Lambda in VPC
  statement {
    effect = "Allow"
    actions = [
      "ec2:CreateNetworkInterface",
      "ec2:DescribeNetworkInterfaces",
      "ec2:DeleteNetworkInterface",
      "ec2:AttachNetworkInterface",
      "ec2:DetachNetworkInterface"
    ]
    resources = ["*"]
  }
}

resource "aws_iam_policy" "lambda_inline_min_permissions" {
  name   = "${local.name}-min-permissions"
  policy = data.aws_iam_policy_document.inline_min_permissions.json
}

resource "aws_iam_role_policy_attachment" "basic_logs_attach" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.lambda_basic_logs.arn
}

resource "aws_iam_role_policy_attachment" "inline_min_attach" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.lambda_inline_min_permissions.arn
}

resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${local.name}"
  retention_in_days = var.log_retention_days
}

resource "aws_lambda_function" "this" {
  function_name = local.name
  role          = aws_iam_role.lambda_role.arn

  package_type = "Image"
  image_uri    = var.image_uri
  architectures = ["x86_64"]

  timeout     = var.timeout_seconds
  memory_size = var.memory_mb

  dynamic "vpc_config" {
    for_each = var.create_vpc_config ? [1] : []
    content {
      subnet_ids         = var.subnet_ids
      security_group_ids = var.security_group_ids
    }
  }

  environment {
    variables = var.environment
  }

  tracing_config {
    mode = var.enable_xray ? "Active" : "PassThrough"
  }

  reserved_concurrent_executions = var.reserved_concurrency

  depends_on = [
    aws_cloudwatch_log_group.lambda_logs
  ]
  tags = var.tags
}

resource "aws_lambda_event_source_mapping" "sqs_mappings" {
  for_each = { for idx, arn in var.queue_arns : idx => arn }

  event_source_arn                   = each.value
  function_name                      = aws_lambda_function.this.arn
  batch_size                         = var.batch_size
  maximum_batching_window_in_seconds = var.maximum_batching_window_in_seconds
  scaling_config {
    maximum_concurrency = var.maximum_concurrency
  }
  enabled                        = true
}


