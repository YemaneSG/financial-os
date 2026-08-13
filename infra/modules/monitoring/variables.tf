variable "project_id" {
  type        = string
  description = "GCP project ID."
}

variable "project_number" {
  type        = string
  description = "GCP project number (used for billing budget filter)."
}

variable "environment" {
  type        = string
  description = "Deployment environment."
}

variable "api_host" {
  type        = string
  description = "API hostname (without https://) for uptime checks."
}

variable "alert_email" {
  type        = string
  description = "Email address for monitoring alerts."
}

variable "billing_account" {
  type        = string
  description = "GCP billing account ID (format: XXXXXX-XXXXXX-XXXXXX)."
}

variable "monthly_budget_usd" {
  type        = number
  description = "Monthly budget ceiling in USD. Alerts fire at 50%, 90%, 100%."
  default     = 50
}
