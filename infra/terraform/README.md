# Infrastructure — Terraform

AWS infrastructure as code for Discipline OS. See `Docs/Technicals/08_Infrastructure_DevOps.md` for the full architecture and region strategy.

## Layout

```
infra/terraform/
├── modules/                 Reusable modules
│   ├── network/             VPC, subnets, NAT, VPC endpoints
│   ├── ecs-service/         ECS task + service + ALB target
│   ├── rds-postgres/        RDS Postgres + replicas
│   ├── redis/               ElastiCache Redis
│   ├── s3-phi-bucket/       S3 bucket with PHI-grade defaults
│   └── kms/                 KMS CMKs per env
├── envs/
│   ├── dev/                 Sandbox / per-developer tier
│   ├── staging/             Pre-prod mirror
│   └── prod/                Production
└── platform/                Shared org-level (Orgs, IAM Identity Center, Control Tower)
```

## Rules

- **State backend:** S3 + DynamoDB lock, per-env. Never local state.
- **No inline policy in Terraform.** Policies live under `platform/policies/` as JSON and are referenced by ARN.
- **Plan on PR, apply gated by human approval.** No `terraform apply` from a developer laptop against prod.
- **Drift detection:** nightly `terraform plan` in CI against prod. Any drift paged.
- **Sensitive vars via Parameter Store / Secrets Manager, not tfvars files.**

## Minimum required variables

Per environment, provide:
- `aws_region`
- `env` (dev | staging | prod)
- `domain` (disciplineos.com, staging.disciplineos.com, ...)
- `vpc_cidr`
- `alert_email`

## Local-first checks

```bash
# Format
terraform fmt -recursive

# Validate
cd envs/dev
terraform init -backend=false
terraform validate

# Plan (requires auth)
terraform init
terraform plan -out=tfplan
```

## What's in this stub

Only the `envs/dev/` entrypoint with a provider and a placeholder module call exists today. The real modules will be built during Phase 1 of the technical roadmap (Months 4–9).
