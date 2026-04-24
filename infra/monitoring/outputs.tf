# ── Discipline OS — Monitoring module outputs ──────────────────────────────────
# These outputs can be consumed by environment-level configurations (envs/prod,
# envs/staging) for cross-module references or CI/CD health checks.

output "alarm_arns" {
  description = "Map of alarm logical name to ARN for all CloudWatch alarms provisioned by this module."
  value = {
    ecs_running_tasks_low       = aws_cloudwatch_metric_alarm.ecs_running_tasks_low.arn
    ecs_cpu_high                = aws_cloudwatch_metric_alarm.ecs_cpu_high.arn
    alb_5xx_rate_high           = aws_cloudwatch_metric_alarm.alb_5xx_rate_high.arn
    alb_target_response_time    = aws_cloudwatch_metric_alarm.alb_target_response_time_high.arn
    rds_cpu_high                = aws_cloudwatch_metric_alarm.rds_cpu_high.arn
    rds_storage_low             = aws_cloudwatch_metric_alarm.rds_storage_low.arn
    redis_evictions             = aws_cloudwatch_metric_alarm.redis_evictions.arn
    crisis_path_latency_high    = aws_cloudwatch_metric_alarm.crisis_path_latency_high.arn
  }
}

output "alarm_names" {
  description = "Map of alarm logical name to CloudWatch alarm name (useful for runbook references and status-page integrations)."
  value = {
    ecs_running_tasks_low       = aws_cloudwatch_metric_alarm.ecs_running_tasks_low.alarm_name
    ecs_cpu_high                = aws_cloudwatch_metric_alarm.ecs_cpu_high.alarm_name
    alb_5xx_rate_high           = aws_cloudwatch_metric_alarm.alb_5xx_rate_high.alarm_name
    alb_target_response_time    = aws_cloudwatch_metric_alarm.alb_target_response_time_high.alarm_name
    rds_cpu_high                = aws_cloudwatch_metric_alarm.rds_cpu_high.alarm_name
    rds_storage_low             = aws_cloudwatch_metric_alarm.rds_storage_low.alarm_name
    redis_evictions             = aws_cloudwatch_metric_alarm.redis_evictions.alarm_name
    crisis_path_latency_high    = aws_cloudwatch_metric_alarm.crisis_path_latency_high.alarm_name
  }
}

output "crisis_alarm_arn" {
  description = "ARN of the crisis-path latency P0 alarm. Exposed separately for direct reference by clinical operations runbooks."
  value       = aws_cloudwatch_metric_alarm.crisis_path_latency_high.arn
}

output "alarm_count" {
  description = "Total number of CloudWatch alarms provisioned by this module."
  value       = 8
}
