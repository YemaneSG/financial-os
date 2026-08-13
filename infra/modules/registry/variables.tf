variable "project_id" {
  type        = string
  description = "GCP project ID."
}

variable "region" {
  type        = string
  description = "Artifact Registry location."
}

variable "deploy_sa_email" {
  type        = string
  description = "CI/CD deploy service account email."
}

variable "api_sa_email" {
  type        = string
  description = "API service account email."
}

variable "worker_sa_email" {
  type        = string
  description = "Worker service account email."
}
