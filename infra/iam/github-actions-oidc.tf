# GitHub Actions OIDC Provider
# Enables GitHub Actions to assume AWS roles without long-lived access keys.
# Per AWS best practice: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_create_oidc.html
#
# One-time bootstrap: apply this file from whichever env holds the CI role
# (typically the staging account, since CI deploys to staging on every main push).
#
# After apply, set the output value as AWS_ROLE_ARN in GitHub repository secrets.

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# ── OIDC provider (one per AWS account) ──────────────────────────────────────

resource "aws_iam_openid_connect_provider" "github_actions" {
  url            = "https://token.actions.githubusercontent.com"
  client_id_list = ["sts.amazonaws.com"]

  # Thumbprint for token.actions.githubusercontent.com as of 2024.
  # AWS now validates the OIDC provider's certificate automatically for
  # github-hosted tokens, but the field is still required by the API.
  thumbprint_list = ["6938fd4d98bab03faadb97b34396831e3780aea1"]

  tags = {
    Project   = "discipline-os"
    ManagedBy = "terraform"
  }
}

# ── CI role ───────────────────────────────────────────────────────────────────

resource "aws_iam_role" "github_actions_ci" {
  name = "discipline-os-github-actions-ci"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Federated = aws_iam_openid_connect_provider.github_actions.arn }
      Action    = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringEquals = {
          # Audience must match what the AWS credential action sends.
          "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
        }
        StringLike = {
          # Restrict to this repository's main branch and PR workflow refs.
          # PRs from forks get a pull_request ref, not a branch ref, so both
          # patterns are needed to allow PR-triggered builds without granting
          # fork PRs push-equivalent permissions (ECR push only runs on main).
          "token.actions.githubusercontent.com:sub" = [
            "repo:Synexiun/Psycho:ref:refs/heads/main",
            "repo:Synexiun/Psycho:pull_request"
          ]
        }
      }
    }]
  })

  tags = {
    Project   = "discipline-os"
    ManagedBy = "terraform"
  }
}

# ── CI permissions ────────────────────────────────────────────────────────────

resource "aws_iam_role_policy" "github_actions_ci_policy" {
  name = "ci-permissions"
  role = aws_iam_role.github_actions_ci.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        # ECR: authenticate and push container images built in CI.
        # GetAuthorizationToken is account-scoped (no resource restriction possible).
        Sid    = "ECRPush"
        Effect = "Allow"
        Action = [
          "ecr:GetAuthorizationToken",
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:PutImage",
          "ecr:InitiateLayerUpload",
          "ecr:UploadLayerPart",
          "ecr:CompleteLayerUpload"
        ]
        Resource = "*"
      },
      {
        # ECS: register new task definitions and trigger rolling deploys on staging.
        # Scoped to all resources because the task definition ARN includes a
        # revision suffix that is unknown at policy-authoring time.
        Sid    = "ECSDeployStaging"
        Effect = "Allow"
        Action = [
          "ecs:RegisterTaskDefinition",
          "ecs:UpdateService",
          "ecs:DescribeServices",
          "ecs:DescribeTaskDefinition"
        ]
        Resource = "*"
      },
      {
        # S3: write static web-app assets and crisis export after build.
        # Restricted to buckets whose name starts with the product prefix.
        Sid    = "S3StaticAssets"
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::discipline-os-static-*",
          "arn:aws:s3:::discipline-os-static-*/*"
        ]
      },
      {
        # CloudFront: invalidate the CDN cache after a static deploy so users
        # immediately receive the new crisis / marketing build.
        Sid      = "CloudFrontInvalidate"
        Effect   = "Allow"
        Action   = ["cloudfront:CreateInvalidation"]
        Resource = "*"
      }
    ]
  })
}

# ── Outputs ───────────────────────────────────────────────────────────────────

output "github_actions_role_arn" {
  value       = aws_iam_role.github_actions_ci.arn
  description = "Set this value as the AWS_ROLE_ARN secret in the GitHub repository settings."
}

output "oidc_provider_arn" {
  value       = aws_iam_openid_connect_provider.github_actions.arn
  description = "ARN of the GitHub Actions OIDC provider in this AWS account."
}
