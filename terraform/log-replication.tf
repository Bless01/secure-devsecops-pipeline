# Permissions for copying logs between the existing logging buckets.
locals {
  portal_log_replication = {
    east_to_west = {
      source_arn      = aws_s3_bucket.portal_access_logs.arn
      destination_arn = aws_s3_bucket.portal_replica_logs.arn
      prefix          = "backups/"
    }

    west_to_east = {
      source_arn      = aws_s3_bucket.portal_replica_logs.arn
      destination_arn = aws_s3_bucket.portal_access_logs.arn
      prefix          = "replica/"
    }
  }
}

resource "aws_iam_role" "portal_log_replication" {
  for_each = local.portal_log_replication

  name_prefix = "portal-logs-${each.key}-"

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

resource "aws_iam_role_policy" "portal_log_replication" {
  for_each = local.portal_log_replication

  name = "replicate-portal-access-logs"
  role = aws_iam_role.portal_log_replication[each.key].id

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
        Resource = each.value.source_arn
      },
      {
        Sid    = "ReadOriginalLogs"
        Effect = "Allow"
        Action = [
          "s3:GetObjectVersionForReplication",
          "s3:GetObjectVersionAcl",
          "s3:GetObjectVersionTagging"
        ]
        Resource = "${each.value.source_arn}/${each.value.prefix}*"
      },
      {
        Sid    = "WriteLogReplicas"
        Effect = "Allow"
        Action = [
          "s3:ReplicateObject",
          "s3:ReplicateTags"
        ]
        Resource = "${each.value.destination_arn}/${each.value.prefix}*"
      }
    ]
  })
}

# Copy original east-region logs into the west-region logging bucket.
resource "aws_s3_bucket_replication_configuration" "portal_access_logs" {
  bucket = aws_s3_bucket.portal_access_logs.id
  role   = aws_iam_role.portal_log_replication["east_to_west"].arn

  rule {
    id       = "replicate-original-backup-logs"
    priority = 1
    status   = "Enabled"

    filter {
      prefix = "backups/"
    }

    delete_marker_replication {
      status = "Disabled"
    }

    destination {
      bucket        = aws_s3_bucket.portal_replica_logs.arn
      storage_class = "STANDARD"
    }
  }

  depends_on = [
    aws_s3_bucket_versioning.portal_access_logs,
    aws_s3_bucket_versioning.portal_replica_logs,
    aws_s3_bucket_server_side_encryption_configuration.portal_replica_logs,
    aws_iam_role_policy.portal_log_replication
  ]
}

# Copy original west-region logs into the east-region logging bucket.
resource "aws_s3_bucket_replication_configuration" "portal_replica_logs" {
  provider = aws.replica

  bucket = aws_s3_bucket.portal_replica_logs.id
  role   = aws_iam_role.portal_log_replication["west_to_east"].arn

  rule {
    id       = "replicate-original-replica-logs"
    priority = 1
    status   = "Enabled"

    filter {
      prefix = "replica/"
    }

    delete_marker_replication {
      status = "Disabled"
    }

    destination {
      bucket        = aws_s3_bucket.portal_access_logs.arn
      storage_class = "STANDARD"
    }
  }

  depends_on = [
    aws_s3_bucket_versioning.portal_access_logs,
    aws_s3_bucket_versioning.portal_replica_logs,
    aws_s3_bucket_server_side_encryption_configuration.portal_access_logs,
    aws_iam_role_policy.portal_log_replication
  ]
}