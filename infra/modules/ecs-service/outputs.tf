output "alb_dns_name" {
  description = "ALB DNS name (use as CloudFront origin)"
  value       = aws_lb.api.dns_name
}

output "alb_arn" {
  description = "ALB ARN"
  value       = aws_lb.api.arn
}

output "cluster_name" {
  description = "ECS cluster name"
  value       = aws_ecs_cluster.main.name
}

output "service_name" {
  description = "ECS service name"
  value       = aws_ecs_service.api.name
}

output "ecs_security_group_id" {
  description = "Security group ID attached to ECS tasks"
  value       = aws_security_group.ecs.id
}

output "task_role_arn" {
  description = "IAM role ARN assumed by running task containers"
  value       = aws_iam_role.task.arn
}
