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

variable "tier" {
  type        = string
  description = "Cloud SQL machine tier."
  default     = "db-g1-small"
}

variable "availability_type" {
  type        = string
  description = "ZONAL or REGIONAL availability."
  default     = "ZONAL"
}

variable "vpc_network_id" {
  type        = string
  description = "Self-link of the VPC network for private IP peering."
}

variable "api_sa_email" {
  type        = string
  description = "API service account email for IAM DB user."
}

variable "worker_sa_email" {
  type        = string
  description = "Worker service account email for IAM DB user."
}

variable "migrate_sa_email" {
  type        = string
  description = "Migration service account email for IAM DB user (DDL rights granted via DB grants, not Terraform)."
}
