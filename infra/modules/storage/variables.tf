variable "project_id" {
  type        = string
  description = "GCP project ID."
}

variable "region" {
  type        = string
  description = "GCS bucket location (multi-region e.g. US, or region e.g. us-central1)."
}

variable "bucket_name" {
  type        = string
  description = "Globally unique name for the private evidence bucket."
}

variable "api_sa_email" {
  type        = string
  description = "API service account email granted read access for verification."
}

variable "worker_sa_email" {
  type        = string
  description = "Worker service account email granted read access for extraction."
}

variable "cors_origin" {
  type        = string
  description = "Primary Firebase web.app origin; its exact firebaseapp.com alias is also allowed."
  default     = "https://example.invalid"
}
