variable "environment" {
  description = "Environment name (staging | prod)"
  type        = string
}

variable "distribution_name" {
  description = "Short identifier for this distribution (e.g. api, app, clinician)"
  type        = string
}

variable "origin_domain_name" {
  description = "Origin domain name — ALB DNS name or S3 bucket regional domain"
  type        = string
}

variable "origin_is_alb" {
  description = "true = ALB origin (custom_origin_config); false = S3 origin (s3_origin_config)"
  type        = bool
  default     = true
}

variable "origin_access_identity" {
  description = "CloudFront origin access identity path (S3 origins only)"
  type        = string
  default     = ""
}

variable "origin_verify_secret" {
  description = "Secret value sent as X-Origin-Verify header to prevent direct ALB access"
  type        = string
  sensitive   = true
}

variable "domain_aliases" {
  description = "Custom domain aliases (e.g. api.disciplineos.com)"
  type        = list(string)
  default     = []
}

variable "default_root_object" {
  description = "Default root object for the distribution (index.html for static sites)"
  type        = string
  default     = ""
}

variable "acm_certificate_arn" {
  description = "ACM certificate ARN in us-east-1 (required for CloudFront)"
  type        = string
}

variable "tags" {
  description = "Common resource tags"
  type        = map(string)
  default     = {}
}
