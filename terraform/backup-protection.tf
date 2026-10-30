# Second region for backup copies
provider "aws" {
  alias  = "replica"
  region = "us-west-2"
}

# Access logs for the original backup bucket
resource "aws_s3_bucket" "portal_access_logs" {
  # checkov:skip=CKV_AWS_145:S3 server access log destination uses SSE-S3 as documented by AWS.

  bucket_prefix = "blessings-portal-access-logs-"

  tags = {
    Name    = "Student portal backup access logs"
    Project = "Secure DevSecOps Pipeline"
  }
}

resource "aws_s3_bucket_public_access_block" "portal_access_logs" {
  bucket = aws_s3_bucket.portal_access_logs.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "portal_access_logs" {
  bucket = aws_s3_bucket.portal_access_logs.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "portal_access_logs" {
  bucket = aws_s3_bucket.portal_access_logs.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_policy" "portal_access_logs" {
  bucket = aws_s3_bucket.portal_access_logs.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid    = "AllowBackupAccessLogs"
      Effect = "Allow"
      Principal = {
        Service = "logging.s3.amazonaws.com"
      }
      Action   = "s3:PutObject"
      Resource = "${aws_s3_bucket.portal_access_logs.arn}/backups/*"
      Condition = {
        ArnLike = {
          "aws:SourceArn" = aws_s3_bucket.portal_backups.arn
        }
        StringEquals = {
          "aws:SourceAccount" = data.aws_caller_identity.current.account_id
        }
      }
    }]
  })
}

resource "aws_s3_bucket_logging" "portal_backups" {
  bucket = aws_s3_bucket.portal_backups.id

  target_bucket = aws_s3_bucket.portal_access_logs.id
  target_prefix = "backups/"

  depends_on = [
    aws_s3_bucket_policy.portal_access_logs
  ]
}

resource "aws_s3_bucket_notification" "portal_access_logs" {
  bucket      = aws_s3_bucket.portal_access_logs.id
  eventbridge = true
}

resource "aws_s3_bucket_lifecycle_configuration" "portal_access_logs" {
  bucket = aws_s3_bucket.portal_access_logs.id

  rule {
    id     = "clean-up-incomplete-uploads"
    status = "Enabled"

    filter {}

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }
}

# Backup replica in us-west-2
resource "aws_s3_bucket" "portal_replica" {
  provider      = aws.replica
  bucket_prefix = "blessings-portal-replica-"

  tags = {
    Name    = "Student portal backup replica"
    Project = "Secure DevSecOps Pipeline"
  }
}

resource "aws_s3_bucket_public_access_block" "portal_replica" {
  provider = aws.replica
  bucket   = aws_s3_bucket.portal_replica.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "portal_replica" {
  provider = aws.replica
  bucket   = aws_s3_bucket.portal_replica.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_kms_key" "portal_replica" {
  provider                = aws.replica
  description             = "Encryption key for student portal backup replicas"
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

resource "aws_s3_bucket_server_side_encryption_configuration" "portal_replica" {
  provider = aws.replica
  bucket   = aws_s3_bucket.portal_replica.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.portal_replica.arn
    }
  }
}

resource "aws_s3_bucket_notification" "portal_replica" {
  provider    = aws.replica
  bucket      = aws_s3_bucket.portal_replica.id
  eventbridge = true
}

resource "aws_s3_bucket_lifecycle_configuration" "portal_replica" {
  provider = aws.replica
  bucket   = aws_s3_bucket.portal_replica.id

  rule {
    id     = "clean-up-incomplete-uploads"
    status = "Enabled"

    filter {}

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }
}

# Permissions for encrypted backup replication
resource "aws_iam_role" "portal_replication" {
  name_prefix = "portal-backup-replication-"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "s3.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "portal_replication" {
  name = "portal-backup-replication"
  role = aws_iam_role.portal_replication.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "ReadSourceBucket"
        Effect = "Allow"
        Action = [
          "s3:GetReplicationConfiguration",
          "s3:ListBucket"
        ]
        Resource = aws_s3_bucket.portal_backups.arn
      },
      {
        Sid    = "ReadSourceObjects"
        Effect = "Allow"
        Action = [
          "s3:GetObjectVersionForReplication",
          "s3:GetObjectVersionAcl",
          "s3:GetObjectVersionTagging"
        ]
        Resource = "${aws_s3_bucket.portal_backups.arn}/*"
      },
      {
        Sid    = "WriteReplicas"
        Effect = "Allow"
        Action = [
          "s3:ReplicateObject",
          "s3:ReplicateTags"
        ]
        Resource = "${aws_s3_bucket.portal_replica.arn}/*"
      },
      {
        Sid      = "DecryptSourceBackups"
        Effect   = "Allow"
        Action   = "kms:Decrypt"
        Resource = aws_kms_key.portal_backups.arn
        Condition = {
          StringEquals = {
            "kms:ViaService" = "s3.us-east-1.amazonaws.com"
          }
        }
      },
      {
        Sid    = "EncryptBackupReplicas"
        Effect = "Allow"
        Action = [
          "kms:Encrypt",
          "kms:GenerateDataKey"
        ]
        Resource = aws_kms_key.portal_replica.arn
        Condition = {
          StringEquals = {
            "kms:ViaService" = "s3.us-west-2.amazonaws.com"
          }
        }
      }
    ]
  })
}

# Replicate new backups to the second region
resource "aws_s3_bucket_replication_configuration" "portal_backups" {
  bucket = aws_s3_bucket.portal_backups.id
  role   = aws_iam_role.portal_replication.arn

  rule {
    id       = "replicate-portal-backups"
    priority = 1
    status   = "Enabled"

    filter {}

    # Source delete markers are not copied to the replica.
    delete_marker_replication {
      status = "Disabled"
    }

    source_selection_criteria {
      sse_kms_encrypted_objects {
        status = "Enabled"
      }
    }

    destination {
      bucket        = aws_s3_bucket.portal_replica.arn
      storage_class = "STANDARD"

      encryption_configuration {
        replica_kms_key_id = aws_kms_key.portal_replica.arn
      }
    }
  }

  depends_on = [
    aws_s3_bucket_versioning.portal_backups,
    aws_s3_bucket_versioning.portal_replica,
    aws_s3_bucket_server_side_encryption_configuration.portal_replica,
    aws_iam_role_policy.portal_replication
  ]
}

# Access logs for the replica bucket in us-west-2
resource "aws_s3_bucket" "portal_replica_logs" {
  # checkov:skip=CKV_AWS_145:S3 server access log destination uses SSE-S3 as documented by AWS.

  provider      = aws.replica
  bucket_prefix = "blessings-portal-replica-logs-"

  tags = {
    Name    = "Student portal replica access logs"
    Project = "Secure DevSecOps Pipeline"
  }
}

resource "aws_s3_bucket_public_access_block" "portal_replica_logs" {
  provider = aws.replica
  bucket   = aws_s3_bucket.portal_replica_logs.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "portal_replica_logs" {
  provider = aws.replica
  bucket   = aws_s3_bucket.portal_replica_logs.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "portal_replica_logs" {
  provider = aws.replica
  bucket   = aws_s3_bucket.portal_replica_logs.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_policy" "portal_replica_logs" {
  provider = aws.replica
  bucket   = aws_s3_bucket.portal_replica_logs.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid    = "AllowReplicaAccessLogs"
      Effect = "Allow"
      Principal = {
        Service = "logging.s3.amazonaws.com"
      }
      Action   = "s3:PutObject"
      Resource = "${aws_s3_bucket.portal_replica_logs.arn}/replica/*"
      Condition = {
        ArnLike = {
          "aws:SourceArn" = aws_s3_bucket.portal_replica.arn
        }
        StringEquals = {
          "aws:SourceAccount" = data.aws_caller_identity.current.account_id
        }
      }
    }]
  })
}

resource "aws_s3_bucket_logging" "portal_replica" {
  provider = aws.replica
  bucket   = aws_s3_bucket.portal_replica.id

  target_bucket = aws_s3_bucket.portal_replica_logs.id
  target_prefix = "replica/"

  depends_on = [
    aws_s3_bucket_policy.portal_replica_logs
  ]
}

resource "aws_s3_bucket_notification" "portal_replica_logs" {
  provider    = aws.replica
  bucket      = aws_s3_bucket.portal_replica_logs.id
  eventbridge = true
}

resource "aws_s3_bucket_lifecycle_configuration" "portal_replica_logs" {
  provider = aws.replica
  bucket   = aws_s3_bucket.portal_replica_logs.id

  rule {
    id     = "clean-up-incomplete-uploads"
    status = "Enabled"

    filter {}

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }
}