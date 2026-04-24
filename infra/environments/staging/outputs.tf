output "vpc_id" {
  description = "VPC ID"
  value       = module.networking.vpc_id
}

output "api_alb_dns_name" {
  description = "API ALB DNS name"
  value       = module.api.alb_dns_name
}

output "api_cloudfront_domain" {
  description = "CloudFront distribution domain for the API"
  value       = module.cloudfront_api.distribution_domain_name
}

output "rds_endpoint" {
  description = "RDS instance endpoint"
  value       = module.rds.endpoint
}

output "redis_primary_endpoint" {
  description = "Redis primary endpoint"
  value       = module.redis.primary_endpoint
}

output "voice_bucket_name" {
  description = "S3 bucket name for voice blobs"
  value       = module.s3_voice.bucket_name
}

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = module.api.cluster_name
}
