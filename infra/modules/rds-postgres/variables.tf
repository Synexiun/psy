variable "environment" {
  description = "Environment name (staging | prod)"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnet IDs for the DB subnet group"
  type        = list(string)
}

variable "allowed_security_group_ids" {
  description = "Security group IDs that may connect on port 5432 (ECS task SG)"
  type        = list(string)
}

variable "db_instance_class" {
  description = "RDS instance class (db.t3.medium for staging, db.r6g.large for prod)"
  type        = string
  default     = "db.t3.medium"
}

variable "db_name" {
  description = "Initial database name"
  type        = string
  default     = "discipline"
}

variable "db_username" {
  description = "Master database username"
  type        = string
  default     = "discipline_admin"
}

variable "db_password_ssm_path" {
  description = "SSM Parameter Store path containing the master DB password (SecureString)"
  type        = string
}

variable "allocated_storage" {
  description = "Initial storage in GB (20 for staging, 100 for prod)"
  type        = number
  default     = 20
}

variable "multi_az" {
  description = "Enable Multi-AZ standby (false for staging, true for prod)"
  type        = bool
  default     = false
}

variable "deletion_protection" {
  description = "Prevent accidental deletion (false for staging, true for prod)"
  type        = bool
  default     = false
}

variable "tags" {
  description = "Common resource tags"
  type        = map(string)
  default     = {}
}
