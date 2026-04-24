variable "environment" {
  description = "Environment name (staging | prod)"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "service_name" {
  description = "Short service identifier used in resource names (e.g. api)"
  type        = string
  default     = "api"
}

variable "image_uri" {
  description = "ECR image URI including tag (e.g. 123456789.dkr.ecr.us-east-1.amazonaws.com/discipline-api:latest)"
  type        = string
}

variable "task_cpu" {
  description = "Fargate task CPU units (512, 1024, 2048 …)"
  type        = number
  default     = 512
}

variable "task_memory" {
  description = "Fargate task memory in MiB"
  type        = number
  default     = 1024
}

variable "desired_count" {
  description = "Initial desired task count"
  type        = number
  default     = 2
}

variable "min_capacity" {
  description = "Auto-scaling minimum tasks"
  type        = number
  default     = 2
}

variable "max_capacity" {
  description = "Auto-scaling maximum tasks"
  type        = number
  default     = 10
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "public_subnet_ids" {
  description = "Public subnet IDs for the ALB"
  type        = list(string)
}

variable "private_subnet_ids" {
  description = "Private subnet IDs for ECS tasks"
  type        = list(string)
}

variable "acm_certificate_arn" {
  description = "ACM certificate ARN for the HTTPS ALB listener"
  type        = string
}

variable "environment_vars" {
  description = "Non-secret environment variables injected into the container"
  type = list(object({
    name  = string
    value = string
  }))
  default = []
}

variable "ssm_secret_paths" {
  description = "SSM Parameter Store paths for secrets (injected as container secrets)"
  type        = list(string)
  default     = []
}

variable "tags" {
  description = "Common resource tags"
  type        = map(string)
  default     = {}
}
