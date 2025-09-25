terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }
}

locals {
  name = var.name
}

# OpenSearch Serverless Security Policy - Crear ANTES de la collection
resource "aws_opensearchserverless_security_policy" "main" {
  name = "${local.name}-search-policy"
  type = "encryption"

  policy = jsonencode({
    Rules = [
      {
        ResourceType = "collection"
        Resource = ["collection/${local.name}-search"]
      }
    ]
    AWSOwnedKey = true
  })
}

# OpenSearch Serverless Collection
resource "aws_opensearchserverless_collection" "main" {
  name = "${local.name}-search"
  type = "SEARCH"

  tags = merge(var.tags, {
    Name        = "${local.name}-search"
    Environment = var.environment
  })

  depends_on = [aws_opensearchserverless_security_policy.main]
}

# OpenSearch Serverless Network Policy
resource "aws_opensearchserverless_security_policy" "network" {
  name = "${local.name}-search-network-policy"
  type = "network"

  policy = jsonencode([
    {
      Rules = [
        {
          ResourceType = "collection"
          Resource = ["collection/${local.name}-search"]
        }
      ]
      AllowFromPublic = true
    }
  ])

  depends_on = [aws_opensearchserverless_security_policy.main]
}

# OpenSearch Serverless Data Access Policy
resource "aws_opensearchserverless_access_policy" "main" {
  name = "${local.name}-search-access-policy"
  type = "data"

  policy = jsonencode([
    {
      Rules = [
        {
          ResourceType = "collection"
          Resource = ["collection/${local.name}-search"]
          Permission = [
            "aoss:CreateCollectionItems",
            "aoss:DeleteCollectionItems",
            "aoss:UpdateCollectionItems",
            "aoss:DescribeCollectionItems"
          ]
        },
        {
          ResourceType = "index"
          Resource = ["index/${local.name}-search/*"]
          Permission = [
            "aoss:CreateIndex",
            "aoss:DeleteIndex",
            "aoss:UpdateIndex",
            "aoss:DescribeIndex",
            "aoss:ReadDocument",
            "aoss:WriteDocument"
          ]
        }
      ]
      Principal = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"]
    }
  ])

  depends_on = [
    aws_opensearchserverless_collection.main,
    aws_opensearchserverless_security_policy.main,
    aws_opensearchserverless_security_policy.network
  ]
}

data "aws_caller_identity" "current" {}
