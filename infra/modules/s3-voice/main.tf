locals {
  name_prefix = "${var.environment}-disciplineos"
}

resource "aws_s3_bucket" "voice" {
  bucket        = "${local.name_prefix}-voice"
  force_destroy = true

  tags = var.tags
}

# Versioning disabled — voice blobs are write-once, hard-deleted at 72h.
# See CLAUDE.md rule 7 and Docs/Technicals/08_Infrastructure_DevOps.md §6.4.
resource "aws_s3_bucket_versioning" "voice" {
  bucket = aws_s3_bucket.voice.id

  versioning_configuration {
    status = "Disabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "voice" {
  bucket = aws_s3_bucket.voice.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "voice" {
  bucket = aws_s3_bucket.voice.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Voice blobs hard-delete at 72 h. Non-negotiable per CLAUDE.md rule 7.
resource "aws_s3_bucket_lifecycle_configuration" "voice" {
  bucket = aws_s3_bucket.voice.id

  rule {
    id     = "voice-hard-delete-72h"
    status = "Enabled"

    expiration {
      days = 3
    }

    abort_incomplete_multipart_upload {
      days_after_initiation = 1
    }
  }
}

resource "aws_s3_bucket_cors_configuration" "voice" {
  bucket = aws_s3_bucket.voice.id

  cors_rule {
    allowed_methods = ["POST", "PUT"]
    allowed_origins = var.api_origins
    allowed_headers = ["*"]
    max_age_seconds = 3600
  }
}

resource "aws_s3_bucket_policy" "voice" {
  bucket = aws_s3_bucket.voice.id
  policy = data.aws_iam_policy_document.voice_bucket.json
}

data "aws_iam_policy_document" "voice_bucket" {
  statement {
    sid    = "DenyInsecureTransport"
    effect = "Deny"
    principals {
      type        = "*"
      identifiers = ["*"]
    }
    actions   = ["s3:*"]
    resources = [aws_s3_bucket.voice.arn, "${aws_s3_bucket.voice.arn}/*"]
    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }
  }
}
