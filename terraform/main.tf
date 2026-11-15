terraform {
  required_version = ">= 1.5, < 2.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

resource "aws_s3_bucket" "portal_backups" {
  bucket_prefix = "blessings-portal-backups-"

  tags = {
    Name    = "Student portal backups"
    Project = "Secure DevSecOps Pipeline"
  }
}

resource "aws_s3_bucket_public_access_block" "portal_backups" {
  bucket = aws_s3_bucket.portal_backups.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "portal_backups" {
  bucket = aws_s3_bucket.portal_backups.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "portal_backups" {
  bucket = aws_s3_bucket.portal_backups.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.portal_backups.arn
    }
  }
}

data "aws_caller_identity" "current" {}

data "aws_partition" "current" {}

resource "aws_kms_key" "portal_backups" {
  description             = "Encryption key for student portal backups"
  enable_key_rotation     = true
  deletion_window_in_days = 30

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid    = "EnableAccountPermissions"
      Effect = "Allow"
      Principal = {
        AWS = "arn:${data.aws_partition.current.partition}:iam::${data.aws_caller_identity.current.account_id}:root"
      }
      Action   = "kms:*"
      Resource = "*"
    }]
  })
}
resource "aws_s3_bucket_notification" "portal_backups" {
  bucket      = aws_s3_bucket.portal_backups.id
  eventbridge = true
}

resource "aws_s3_bucket_lifecycle_configuration" "portal_backups" {
  bucket = aws_s3_bucket.portal_backups.id

  rule {
    id     = "clean-up-incomplete-uploads"
    status = "Enabled"

    filter {}

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }
}