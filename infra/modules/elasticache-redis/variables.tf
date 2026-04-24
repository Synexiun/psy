variable "environment" {
  description = "Environment name (staging | prod)"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnet IDs for the ElastiCache subnet group"
  type        = list(string)
}

variable "allowed_security_group_ids" {
  description = "Security group IDs that may connect on port 6379 (ECS task SG)"
  type        = list(string)
}

variable "node_type" {
  description = "ElastiCache node type (cache.t3.micro for staging, cache.r6g.large for prod)"
  type        = string
  default     = "cache.t3.micro"
}

variable "multi_az" {
  description = "Enable Multi-AZ with automatic failover (false for staging, true for prod)"
  type        = bool
  default     = false
}

variable "tags" {
  description = "Common resource tags"
  type        = map(string)
  default     = {}
}
