output "bucket_name" {
  description = "Voice blob S3 bucket name"
  value       = aws_s3_bucket.voice.id
}

output "bucket_arn" {
  description = "Voice blob S3 bucket ARN"
  value       = aws_s3_bucket.voice.arn
}
