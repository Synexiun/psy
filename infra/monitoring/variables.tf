# ── Discipline OS — Monitoring module variables ────────────────────────────────
# All CloudWatch alarms and related resources are parameterised through these
# variables so the same module can be applied to staging and prod without
# hardcoded environment names.

variable "environment" {
  description = "Deployment environment (staging | prod). Used as a prefix in all resource names."
  type        = string

  validation {
    condition     = contains(["staging", "prod"], var.environment)
    error_message = "environment must be 'staging' or 'prod'."
  }
}

variable "aws_region" {
  description = "AWS region where resources are deployed."
  type        = string
  default     = "us-east-1"
}

variable "alerts_sns_topic_arn" {
  description = "ARN of the SNS topic that receives CloudWatch alarm notifications. Provisioned separately (PagerDuty / Opsgenie subscription)."
  type        = string
}

variable "tags" {
  description = "Common tags applied to all resources in this module."
  type        = map(string)
  default     = {}
}

# ── ECS ───────────────────────────────────────────────────────────────────────

variable "ecs_cluster_name" {
  description = "ECS cluster name (output of the ecs-service module). Used to scope ECS CloudWatch metrics."
  type        = string
}

variable "ecs_service_name" {
  description = "ECS service name for the API (output of the ecs-service module)."
  type        = string
  default     = "api"
}

variable "ecs_desired_count" {
  description = "Desired ECS task count for the API service. The 'tasks low' alarm fires when running tasks fall below this value."
  type        = number
  default     = 2
}

# ── ALB ───────────────────────────────────────────────────────────────────────

variable "alb_arn_suffix" {
  description = "ALB ARN suffix (the portion after 'loadbalancer/', from the ALB ARN). Used to scope ALB CloudWatch metrics."
  type        = string
}

variable "alb_target_group_arn_suffix" {
  description = "ALB target group ARN suffix (the portion after 'targetgroup/'). Required for per-target-group metrics."
  type        = string
}

# ── RDS ───────────────────────────────────────────────────────────────────────

variable "rds_instance_identifier" {
  description = "RDS instance identifier (DBInstanceIdentifier). Used to scope RDS CloudWatch metrics."
  type        = string
}

variable "rds_storage_low_threshold_gb" {
  description = "Alert when RDS free storage falls below this value in GB."
  type        = number
  default     = 10
}

variable "rds_cpu_threshold_percent" {
  description = "Alert when RDS CPU utilisation exceeds this percentage for the evaluation period."
  type        = number
  default     = 85
}

# ── ElastiCache Redis ─────────────────────────────────────────────────────────

variable "redis_replication_group_id" {
  description = "ElastiCache replication group ID. Used to scope Redis CloudWatch metrics."
  type        = string
}

variable "redis_evictions_threshold" {
  description = "Alert when Redis evictions per 5-minute period exceed this count. Even a single eviction indicates memory pressure when using noeviction policy."
  type        = number
  default     = 0
}

# ── Crisis path ───────────────────────────────────────────────────────────────

variable "crisis_latency_p99_threshold_ms" {
  description = "Crisis path p99 latency alert threshold in milliseconds. Clinical SLO is 200 ms; alarm fires sooner at this value to give operators headroom."
  type        = number
  default     = 150

  validation {
    condition     = var.crisis_latency_p99_threshold_ms <= 200
    error_message = "crisis_latency_p99_threshold_ms must not exceed 200 ms (the clinical SLO)."
  }
}
