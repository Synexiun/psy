variable "environment" {
  description = "Environment name (staging | prod)"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "List of AZs to span (3 recommended for prod)"
  type        = list(string)
}

variable "nat_gateway_count" {
  description = "Number of NAT gateways: 1 for staging (cost), len(AZs) for prod (HA)"
  type        = number
  default     = 1
}

variable "tags" {
  description = "Common resource tags"
  type        = map(string)
  default     = {}
}
