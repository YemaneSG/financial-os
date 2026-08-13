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
  description = "Deployment environment."
}

variable "worker_base_url" {
  type        = string
  description = "Base URL of the worker Cloud Run service (without trailing slash)."
}

variable "task_invoker_sa_email" {
  type        = string
  description = "Service account email used to sign OIDC tokens for Cloud Tasks delivery."
}
