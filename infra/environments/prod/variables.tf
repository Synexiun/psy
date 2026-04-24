variable "environment" {
  description = "Environment name"
  type        = string
  default     = "prod"
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "AZs to deploy into — all 3 used for prod HA"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b", "us-east-1c"]
}

variable "db_name" {
  description = "PostgreSQL database name"
  type        = string
  default     = "discipline"
}

variable "db_username" {
  description = "PostgreSQL master username"
  type        = string
  default     = "discipline_admin"
}

variable "api_image_uri" {
  description = "ECR image URI for the FastAPI container"
  type        = string
}

variable "acm_certificate_arn" {
  description = "ACM certificate ARN (us-east-1) for ALB and CloudFront"
  type        = string
}

variable "cloudfront_origin_verify_secret" {
  description = "Secret header value sent from CloudFront to ALB origin"
  type        = string
  sensitive   = true
}
