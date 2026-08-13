variable "project_id" {
  type        = string
  description = "GCP project ID. Never commit a real production project ID."
}

variable "project_number" {
  type        = string
  description = "GCP project number."
}

variable "region" {
  type        = string
  description = "Primary GCP region."
  default     = "us-central1"
}

variable "environment" {
  type        = string
  description = "Deployment environment label."
  default     = "dev"
}

variable "gcs_location" {
  type        = string
  description = "GCS bucket location (US for multi-region, or region for single-region)."
  default     = "US"
}

variable "evidence_bucket_name" {
  type        = string
  description = "Globally unique name for the private evidence bucket. Include project ID to ensure uniqueness."
}

variable "cors_origin" {
  type        = string
  description = "Firebase Hosting origin allowed for signed-URL upload CORS."
}

variable "vpc_network_id" {
  type        = string
  description = "Self-link of the VPC network for Cloud SQL private IP peering. Use default network for dev."
  default     = "projects/PLACEHOLDER/global/networks/default"
}

variable "vpc_network_name" {
  type        = string
  description = "VPC network name used by Cloud Run Direct VPC egress."
  default     = "default"
}

variable "vpc_subnetwork_name" {
  type        = string
  description = "Regional VPC subnet name used by Cloud Run Direct VPC egress."
  default     = "default"
}

variable "sql_tier" {
  type        = string
  description = "Cloud SQL machine tier."
  default     = "db-g1-small"
}

variable "sql_availability_type" {
  type        = string
  description = "ZONAL (dev) or REGIONAL (production)."
  default     = "ZONAL"
}

variable "github_org" {
  type        = string
  description = "GitHub organisation or user name."
}

variable "github_repo" {
  type        = string
  description = "GitHub repository name."
}

variable "initial_image" {
  type        = string
  description = "Immutable application image used for the first Cloud Run revision."

  validation {
    condition     = can(regex("@sha256:[0-9a-f]{64}$", var.initial_image))
    error_message = "initial_image must be an immutable image reference ending in @sha256:<64 hex chars>."
  }
}

variable "api_min_instances" {
  type        = number
  description = "Minimum warm API instances. Set to 1 if A-04 cold-start evidence requires it."
  default     = 0
}

variable "api_max_instances" {
  type        = number
  description = "Maximum API instances (protects Cloud SQL connection capacity)."
  default     = 5
}

variable "worker_max_instances" {
  type        = number
  description = "Maximum worker instances."
  default     = 3
}

variable "alert_email" {
  type        = string
  description = "Email address for monitoring alert notifications."
}

variable "billing_account" {
  type        = string
  description = "GCP billing account ID (XXXXXX-XXXXXX-XXXXXX)."
}

variable "monthly_budget_usd" {
  type        = number
  description = "Monthly GCP budget ceiling in USD."
  default     = 50
}
