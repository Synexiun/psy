# WAF for CloudFront must be provisioned in us-east-1 regardless of the primary region.
# This alias provider is passed in from the environment root module.
terraform {
  required_providers {
    aws = {
      source                = "hashicorp/aws"
      version               = "~> 5.0"
      configuration_aliases = [aws.us_east_1]
    }
  }
}
