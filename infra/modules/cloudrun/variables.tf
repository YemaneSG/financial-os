variable "project_id" {
  type        = string
  description = "GCP project ID."
}

variable "region" {
  type        = string
  description = "Cloud Run service location."
}

variable "environment" {
  type        = string
  description = "Deployment environment."
}

variable "image_with_digest" {
  type        = string
  description = "Fully qualified container image reference with immutable SHA-256 digest (CICD-03)."
  # Example: us-central1-docker.pkg.dev/PROJECT/financial-os/app@sha256:abc123...
}

variable "image_tag" {
  type        = string
  description = "Human-readable image tag (git SHA) recorded as PIPELINE_VERSION."
}

variable "api_sa_email" {
  type        = string
  description = "API runtime service account email."
}

variable "worker_sa_email" {
  type        = string
  description = "Worker runtime service account email."
}

variable "migrate_sa_email" {
  type        = string
  description = "Migration job service account email."
}

variable "task_invoker_sa_email" {
  type        = string
  description = "Cloud Tasks invoker service account email (bound as run.invoker on worker)."
}

variable "sql_instance_connection_name" {
  type        = string
  description = "Cloud SQL instance connection name (PROJECT:REGION:INSTANCE)."
}

variable "vpc_network_name" {
  type        = string
  description = "VPC network name for Direct VPC egress to private Cloud SQL."
}

variable "vpc_subnetwork_name" {
  type        = string
  description = "Regional subnet name for Direct VPC egress to private Cloud SQL."
}

variable "api_min_instances" {
  type        = number
  description = "Minimum warm API instances. Set to 1 if cold-start evidence requires it (A-04)."
  default     = 0
}

variable "api_max_instances" {
  type        = number
  description = "Maximum API instances (guards Cloud SQL connection capacity)."
  default     = 5
}

variable "worker_max_instances" {
  type        = number
  description = "Maximum worker instances."
  default     = 3
}

variable "api_secrets" {
  type = list(object({
    env_var   = string
    secret_id = string
  }))
  description = "Secret Manager secrets to inject as environment variables into the API container."
  default     = []
}

variable "worker_secrets" {
  type = list(object({
    env_var   = string
    secret_id = string
  }))
  description = "Secret Manager secrets to inject as environment variables into the worker container."
  default     = []
}

variable "migrate_secrets" {
  type = list(object({
    env_var   = string
    secret_id = string
  }))
  description = "Secret Manager secrets to inject into the migration job container."
  default     = []
}
