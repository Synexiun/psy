terraform {
  required_version = ">= 1.8"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket         = "disciplineos-tf-state-staging"
    key            = "staging/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "disciplineos-tf-locks"
    encrypt        = true
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Environment = var.environment
      Project     = "discipline-os"
      ManagedBy   = "terraform"
    }
  }
}

# WAF for CloudFront must live in us-east-1.
provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"

  default_tags {
    tags = {
      Environment = var.environment
      Project     = "discipline-os"
      ManagedBy   = "terraform"
    }
  }
}

locals {
  common_tags = {
    Environment = var.environment
    Project     = "discipline-os"
    ManagedBy   = "terraform"
  }
}

# ── Networking ────────────────────────────────────────────────────────────────

module "networking" {
  source = "../../modules/networking"

  environment        = var.environment
  aws_region         = var.aws_region
  vpc_cidr           = var.vpc_cidr
  availability_zones = var.availability_zones
  nat_gateway_count  = 1
  tags               = local.common_tags
}

# ── RDS PostgreSQL ────────────────────────────────────────────────────────────

module "rds" {
  source = "../../modules/rds-postgres"

  environment                = var.environment
  vpc_id                     = module.networking.vpc_id
  private_subnet_ids         = module.networking.private_subnet_ids
  allowed_security_group_ids = [module.api.ecs_security_group_id]

  db_instance_class    = "db.t3.medium"
  db_name              = var.db_name
  db_username          = var.db_username
  db_password_ssm_path = "/${var.environment}/disciplineos/db/password"
  allocated_storage    = 20
  multi_az             = false
  deletion_protection  = false

  tags = local.common_tags
}

# ── ElastiCache Redis ─────────────────────────────────────────────────────────

module "redis" {
  source = "../../modules/elasticache-redis"

  environment                = var.environment
  vpc_id                     = module.networking.vpc_id
  private_subnet_ids         = module.networking.private_subnet_ids
  allowed_security_group_ids = [module.api.ecs_security_group_id]

  node_type = "cache.t3.micro"
  multi_az  = false

  tags = local.common_tags
}

# ── ECS Fargate API ───────────────────────────────────────────────────────────

module "api" {
  source = "../../modules/ecs-service"

  environment  = var.environment
  aws_region   = var.aws_region
  service_name = "api"
  image_uri    = var.api_image_uri

  task_cpu    = 512
  task_memory = 1024

  desired_count = 2
  min_capacity  = 2
  max_capacity  = 10

  vpc_id             = module.networking.vpc_id
  public_subnet_ids  = module.networking.public_subnet_ids
  private_subnet_ids = module.networking.private_subnet_ids
  acm_certificate_arn = var.acm_certificate_arn

  environment_vars = [
    { name = "APP_ENV",      value = var.environment },
    { name = "DB_HOST",      value = module.rds.address },
    { name = "DB_NAME",      value = module.rds.db_name },
    { name = "REDIS_HOST",   value = module.redis.primary_endpoint },
    { name = "REDIS_PORT",   value = tostring(module.redis.port) },
    { name = "AWS_REGION",   value = var.aws_region },
  ]

  ssm_secret_paths = [
    "/${var.environment}/disciplineos/db/password",
    "/${var.environment}/disciplineos/clerk/secret-key",
    "/${var.environment}/disciplineos/anthropic/api-key",
    "/${var.environment}/disciplineos/stripe/secret-key",
    "/${var.environment}/disciplineos/audit/chain-secret",
  ]

  tags = local.common_tags
}

# ── S3 Voice Bucket ───────────────────────────────────────────────────────────

module "s3_voice" {
  source = "../../modules/s3-voice"

  environment = var.environment
  api_origins = ["https://api.staging.disciplineos.com"]

  tags = local.common_tags
}

# ── CloudFront + WAF (API) ────────────────────────────────────────────────────

module "cloudfront_api" {
  source = "../../modules/cloudfront-waf"

  providers = {
    aws           = aws
    aws.us_east_1 = aws.us_east_1
  }

  environment        = var.environment
  distribution_name  = "api"
  origin_domain_name = module.api.alb_dns_name
  origin_is_alb      = true
  origin_verify_secret = var.cloudfront_origin_verify_secret
  domain_aliases     = ["api.staging.disciplineos.com"]
  acm_certificate_arn = var.acm_certificate_arn

  tags = local.common_tags
}
