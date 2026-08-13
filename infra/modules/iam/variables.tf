variable "project_id" {
  type        = string
  description = "GCP project ID."
}

variable "region" {
  type        = string
  description = "Primary GCP region."
}

variable "environment" {
  type        = string
  description = "Deployment environment (dev, staging, prod)."
}

variable "worker_service_url" {
  type        = string
  description = "Cloud Run URL of the private worker service (used to bind the invoker role)."
  default     = ""
}

variable "github_org" {
  type        = string
  description = "GitHub organisation or user name owning the repository."
}

variable "github_repo" {
  type        = string
  description = "GitHub repository name (without org prefix)."
}

variable "wif_pool_id" {
  type        = string
  description = "Workload Identity Pool ID for GitHub Actions federation."
  default     = "github-actions-pool"
}

variable "wif_provider_id" {
  type        = string
  description = "Workload Identity Provider ID within the pool."
  default     = "github-actions-provider"
}
