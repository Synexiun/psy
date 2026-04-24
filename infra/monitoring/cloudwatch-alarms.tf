# ── Discipline OS — CloudWatch Alarms ─────────────────────────────────────────
#
# All alarms notify the shared SNS topic (var.alerts_sns_topic_arn), which is
# subscribed to PagerDuty / Opsgenie for P0/P1 pages and a Slack webhook for
# P2 notifications. Topic provisioning is out of scope for this module.
#
# Alarm naming convention: ${environment}-disciplineos-<subsystem>-<condition>
# This matches the name_prefix used in all other Discipline OS Terraform modules.
#
# treat_missing_data:
#   - "breaching"    — health checks: missing data = assume the worst.
#   - "notBreaching" — rate/utilisation metrics: missing data = no traffic, OK.
#
# Evaluation periods and thresholds follow the SLO tiers in
# Docs/Technicals/08_Infrastructure_DevOps.md §11:
#   T3 (crisis, 99.95%): 1-min evaluation period, 1 datapoint to alarm.
#   T2/T1 (API, 99.9%):  5-min evaluation period, 2–3 datapoints to alarm.
#
# Runbook base URL: https://github.com/disciplineos/disciplineos/tree/main/docs/runbooks
# ──────────────────────────────────────────────────────────────────────────────

locals {
  alarm_prefix = "${var.environment}-disciplineos"
  sns_topic_arn = var.alerts_sns_topic_arn

  # Runbook base URL used in alarm descriptions.
  runbook_base = "https://github.com/disciplineos/disciplineos/blob/main/docs/runbooks"
}

# ─────────────────────────────────────────────────────────────────────────────
# 1. ECS running task count — HEALTH
# Priority: P0 — a task count below the minimum means the service is degraded.
# treat_missing_data = "breaching": if CloudWatch stops receiving Container
# Insights data, assume the cluster is down.
# ─────────────────────────────────────────────────────────────────────────────
resource "aws_cloudwatch_metric_alarm" "ecs_running_tasks_low" {
  alarm_name          = "${local.alarm_prefix}-ecs-tasks-low"
  alarm_description   = <<-EOT
    [P0] ECS running task count for the API service has dropped below the
    desired minimum (${var.ecs_desired_count}). This means the API is
    under-provisioned or tasks are crash-looping.

    Immediate action: check ECS service events, recent deployment status,
    and task stopped reasons in the AWS console or via:
      aws ecs describe-services --cluster ${var.ecs_cluster_name} \
        --services ${var.ecs_service_name}

    Runbook: ${local.runbook_base}/ecs-task-health.md
  EOT

  namespace           = "ECS/ContainerInsights"
  metric_name         = "RunningTaskCount"
  dimensions = {
    ClusterName = var.ecs_cluster_name
    ServiceName = var.ecs_service_name
  }

  statistic           = "Minimum"
  period              = 60   # 1-minute granularity — fast detection
  evaluation_periods  = 2    # fire after 2 consecutive low readings (~2 min)
  threshold           = var.ecs_desired_count
  comparison_operator = "LessThanThreshold"
  treat_missing_data  = "breaching"

  alarm_actions = [local.sns_topic_arn]
  ok_actions    = [local.sns_topic_arn]

  tags = var.tags
}

# ─────────────────────────────────────────────────────────────────────────────
# 2. ECS CPU utilisation — high
# Priority: P1 — sustained high CPU means the service is saturated and
# auto-scaling may not be keeping up.
# ─────────────────────────────────────────────────────────────────────────────
resource "aws_cloudwatch_metric_alarm" "ecs_cpu_high" {
  alarm_name          = "${local.alarm_prefix}-ecs-cpu-high"
  alarm_description   = <<-EOT
    [P1] ECS API service CPU utilisation has exceeded 85% for 10 minutes.
    Auto-scaling target is 60% CPU; sustained 85%+ indicates the scaler is
    not keeping up with demand or tasks are in a hot loop.

    Check: current running task count vs desired, active scale-out activities,
    and whether the ALB request count is driving the load.

    Runbook: ${local.runbook_base}/ecs-cpu-saturation.md
  EOT

  namespace           = "AWS/ECS"
  metric_name         = "CPUUtilization"
  dimensions = {
    ClusterName = var.ecs_cluster_name
    ServiceName = var.ecs_service_name
  }

  statistic           = "Average"
  period              = 300  # 5-minute periods
  evaluation_periods  = 2    # 10 minutes sustained
  threshold           = 85
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"

  alarm_actions = [local.sns_topic_arn]
  ok_actions    = [local.sns_topic_arn]

  tags = var.tags
}

# ─────────────────────────────────────────────────────────────────────────────
# 3. ALB 5xx error rate — high
# Priority: P1 — >1% 5xx rate over 5 minutes breaches the API SLO.
# Uses a metric math expression to compute the ratio safely when request
# count is 0 (avoids division-by-zero false alarms at very low traffic).
# ─────────────────────────────────────────────────────────────────────────────
resource "aws_cloudwatch_metric_alarm" "alb_5xx_rate_high" {
  alarm_name          = "${local.alarm_prefix}-5xx-rate-high"
  alarm_description   = <<-EOT
    [P1] ALB 5xx error rate has exceeded 1% over the last 5 minutes.
    This breaches the API error-rate SLO. Possible causes: ECS task OOM /
    crash, unhandled exception, database connection exhaustion, or
    downstream dependency failure.

    Check: ECS task logs in CloudWatch (/ecs/${local.alarm_prefix}-api),
    RDS connection counts, and Redis availability.

    SLO target: <0.1% steady state, <1% allowed burst.

    Runbook: ${local.runbook_base}/alb-5xx-rate.md
  EOT

  # Metric math: HTTPCode_Target_5XX_Count / RequestCount.
  # m1 = 5xx responses, m2 = total requests.
  # Expression: IF(m2 > 0, m1/m2, 0) — avoids division by zero at low traffic.
  metric_query {
    id          = "error_rate"
    expression  = "IF(m2 > 0, m1/m2, 0)"
    label       = "5xx Error Rate"
    return_data = true
  }

  metric_query {
    id = "m1"
    metric {
      namespace   = "AWS/ApplicationELB"
      metric_name = "HTTPCode_Target_5XX_Count"
      dimensions = {
        LoadBalancer = var.alb_arn_suffix
      }
      period = 300
      stat   = "Sum"
    }
  }

  metric_query {
    id = "m2"
    metric {
      namespace   = "AWS/ApplicationELB"
      metric_name = "RequestCount"
      dimensions = {
        LoadBalancer = var.alb_arn_suffix
      }
      period = 300
      stat   = "Sum"
    }
  }

  evaluation_periods  = 1
  threshold           = 0.01  # 1%
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"

  alarm_actions = [local.sns_topic_arn]
  ok_actions    = [local.sns_topic_arn]

  tags = var.tags
}

# ─────────────────────────────────────────────────────────────────────────────
# 4. ALB target response time — P99 budget for general API
# Priority: P1 — helps catch latency regressions before they become SLO burns.
# Note: this is the overall API p99; crisis-path latency is tracked separately
# in alarm #8 with a tighter threshold and shorter evaluation period.
# ─────────────────────────────────────────────────────────────────────────────
resource "aws_cloudwatch_metric_alarm" "alb_target_response_time_high" {
  alarm_name          = "${local.alarm_prefix}-api-latency-p99-high"
  alarm_description   = <<-EOT
    [P1] ALB target response time p99 has exceeded 500 ms over the last 10
    minutes. This is the general API SLO budget; the crisis-path budget is
    stricter (200 ms, monitored separately).

    A staging latency regression >15% relative to the 7-day baseline also
    blocks prod promotion in CI.

    Check: ECS task CPU/memory, RDS query performance insights, Redis latency,
    and whether a recent deployment changed query patterns.

    Runbook: ${local.runbook_base}/api-latency-regression.md
  EOT

  namespace           = "AWS/ApplicationELB"
  metric_name         = "TargetResponseTime"
  dimensions = {
    LoadBalancer = var.alb_arn_suffix
  }

  extended_statistic  = "p99"
  period              = 300
  evaluation_periods  = 2    # 10 minutes
  threshold           = 0.5  # 500 ms in seconds
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"

  alarm_actions = [local.sns_topic_arn]
  ok_actions    = [local.sns_topic_arn]

  tags = var.tags
}

# ─────────────────────────────────────────────────────────────────────────────
# 5. RDS CPU — high
# Priority: P2 — high CPU sustained for 15 minutes warrants investigation.
# The scale-trigger threshold from the architecture doc is 65% for 5 days;
# this alarm fires sooner at 85% for immediate ops awareness.
# ─────────────────────────────────────────────────────────────────────────────
resource "aws_cloudwatch_metric_alarm" "rds_cpu_high" {
  alarm_name          = "${local.alarm_prefix}-rds-cpu-high"
  alarm_description   = <<-EOT
    [P2] RDS PostgreSQL CPU utilisation has exceeded 85% for 15 minutes.
    At this level query latency begins to degrade. Check pg_stat_statements
    for hot queries, and consider whether a recent deployment changed query
    patterns or index coverage.

    Architecture scale-up trigger: sustained >65% for 5 days → vertical
    upgrade to db.r7g.4xlarge.

    Runbook: ${local.runbook_base}/rds-cpu-high.md
  EOT

  namespace           = "AWS/RDS"
  metric_name         = "CPUUtilization"
  dimensions = {
    DBInstanceIdentifier = var.rds_instance_identifier
  }

  statistic           = "Average"
  period              = 300
  evaluation_periods  = 3    # 15 minutes
  threshold           = var.rds_cpu_threshold_percent
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"

  alarm_actions = [local.sns_topic_arn]
  ok_actions    = [local.sns_topic_arn]

  tags = var.tags
}

# ─────────────────────────────────────────────────────────────────────────────
# 6. RDS free storage — low
# Priority: P1 — running out of disk will crash the database.
# Default threshold: 10 GB free (var.rds_storage_low_threshold_gb).
# ─────────────────────────────────────────────────────────────────────────────
resource "aws_cloudwatch_metric_alarm" "rds_storage_low" {
  alarm_name          = "${local.alarm_prefix}-rds-storage-low"
  alarm_description   = <<-EOT
    [P1] RDS PostgreSQL free storage has dropped below ${var.rds_storage_low_threshold_gb} GB.
    At zero free storage the instance becomes read-only, which will cause all
    write operations (including check-in ingestion and audit log writes) to fail.

    Immediate action: check active table growth in pg_stat_user_tables,
    VACUUM ANALYZE dead tuple accumulation, and initiate storage autoscaling
    or a manual storage increase in the AWS console.

    Runbook: ${local.runbook_base}/rds-storage-low.md
  EOT

  namespace           = "AWS/RDS"
  metric_name         = "FreeStorageSpace"
  dimensions = {
    DBInstanceIdentifier = var.rds_instance_identifier
  }

  statistic           = "Minimum"
  period              = 300
  evaluation_periods  = 1
  # CloudWatch metric is in bytes; convert GB to bytes.
  threshold           = var.rds_storage_low_threshold_gb * 1024 * 1024 * 1024
  comparison_operator = "LessThanThreshold"
  treat_missing_data  = "notBreaching"

  alarm_actions = [local.sns_topic_arn]
  ok_actions    = [local.sns_topic_arn]

  tags = var.tags
}

# ─────────────────────────────────────────────────────────────────────────────
# 7. ElastiCache Redis evictions
# Priority: P1 — any evictions indicate Redis is under memory pressure.
# Redis is used for Celery task queues, rate-limiting, and session tokens.
# Evicting queue items silently drops background jobs; evicting session tokens
# logs users out mid-session.
# ─────────────────────────────────────────────────────────────────────────────
resource "aws_cloudwatch_metric_alarm" "redis_evictions" {
  alarm_name          = "${local.alarm_prefix}-redis-evictions"
  alarm_description   = <<-EOT
    [P1] ElastiCache Redis is evicting keys. The maxmemory-policy is
    'noeviction' for critical data stores; any evictions indicate the instance
    has hit its memory limit.

    Impact: Celery tasks may be silently dropped (nudge scheduling, pattern
    computation, voice purge). Session tokens may be evicted, logging users out.

    Immediate action: check Redis memory usage (redis_memory_used_bytes /
    redis_memory_max_bytes via Grafana), identify large keyspaces with
    MEMORY USAGE, and initiate a node type upgrade if sustained.

    Architecture scale trigger: >75% memory → cluster resize.

    Runbook: ${local.runbook_base}/redis-evictions.md
  EOT

  namespace           = "AWS/ElastiCache"
  metric_name         = "Evictions"
  dimensions = {
    ReplicationGroupId = var.redis_replication_group_id
  }

  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 1
  threshold           = var.redis_evictions_threshold
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"

  alarm_actions = [local.sns_topic_arn]
  ok_actions    = [local.sns_topic_arn]

  tags = var.tags
}

# ─────────────────────────────────────────────────────────────────────────────
# 8. Crisis path latency — P0 (clinical SLO)
# Priority: P0 — the clinical SLO for /v1/sos and /v1/crisis/resources is
# p99 ≤ 200 ms (T3 requirement, Docs/Technicals/08 §10.4).
#
# This alarm uses a SHORTER evaluation period and fires on a SINGLE
# datapoint compared to the general API latency alarm above. Crisis path
# latency violations must page immediately — do not wait for 10 minutes.
#
# Note: ALB p99 is a proxy. For true per-path p99 use the Prometheus
# histogram_quantile alarm on the ADOT/Prometheus side. This CloudWatch
# alarm covers the ALB-level view (all paths), which is a conservative
# upper bound. The Prometheus recording rules (infra/monitoring/rules/) hold
# the path-filtered SLO burn-rate alarms.
# ─────────────────────────────────────────────────────────────────────────────
resource "aws_cloudwatch_metric_alarm" "crisis_path_latency_high" {
  alarm_name          = "${local.alarm_prefix}-crisis-latency-p99-high"
  alarm_description   = <<-EOT
    [P0 — CLINICAL SLO] ALB p99 response time has exceeded
    ${var.crisis_latency_p99_threshold_ms} ms (early-warning threshold; hard
    SLO is 200 ms). The T3 clinical requirement is that crisis path endpoints
    (/v1/sos, /v1/crisis/resources) respond within 200 ms p99 regardless of
    overall API load.

    This is a P0 incident. Page the on-call engineer AND notify the clinical
    operations lead. The T3 fast-lane allows <60 min from identification to
    deployed fix (Docs/Technicals/08 §8.3).

    Note: this alarm covers the full ALB (all paths). Check the Grafana
    Crisis Path SLO dashboard for per-path p99 drill-down:
    https://grafana.disciplineos.internal/d/discipline-crisis-path

    Runbook: ${local.runbook_base}/crisis-path-latency.md
  EOT

  namespace           = "AWS/ApplicationELB"
  metric_name         = "TargetResponseTime"
  dimensions = {
    LoadBalancer = var.alb_arn_suffix
  }

  # Tighter than the general API alarm: 1-minute period, fire on first breach.
  extended_statistic  = "p99"
  period              = 60
  evaluation_periods  = 1
  # Threshold in seconds (convert from ms variable).
  threshold           = var.crisis_latency_p99_threshold_ms / 1000.0
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"

  alarm_actions = [local.sns_topic_arn]
  ok_actions    = [local.sns_topic_arn]

  tags = merge(var.tags, {
    SLOTier  = "T3"
    Clinical = "true"
  })
}
