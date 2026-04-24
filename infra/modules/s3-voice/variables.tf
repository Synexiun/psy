variable "environment" {
  description = "Environment name (staging | prod)"
  type        = string
}

variable "api_origins" {
  description = "Allowed CORS origins for POST/PUT (API server origins only)"
  type        = list(string)
}

variable "tags" {
  description = "Common resource tags"
  type        = map(string)
  default     = {}
}
