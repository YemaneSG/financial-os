output "api_url" {
  value       = module.cloudrun.api_url
  description = "Cloud Run API service URL."
}

output "worker_url" {
  value       = module.cloudrun.worker_url
  description = "Cloud Run worker service URL (internal only — not publicly reachable)."
  sensitive   = true
}

output "evidence_bucket" {
  value       = module.storage.bucket_name
  description = "Private evidence bucket name."
}

output "sql_instance_connection_name" {
  value       = module.sql.instance_connection_name
  description = "Cloud SQL instance connection name for Cloud SQL connector."
}

output "artifact_registry_url" {
  value       = module.registry.repository_url
  description = "Artifact Registry base URL for container images."
}

output "wif_provider_name" {
  value       = module.iam.wif_provider_name
  description = "Full WIF provider resource name — paste into GitHub Actions workflow."
}

output "deploy_sa_email" {
  value       = module.iam.deploy_sa_email
  description = "Deploy service account email — paste into GitHub Actions workflow."
}

output "api_database_user" {
  value       = trimsuffix(module.iam.api_sa_email, ".gserviceaccount.com")
  description = "PostgreSQL IAM username for the API runtime."
  sensitive   = true
}

output "worker_database_user" {
  value       = trimsuffix(module.iam.worker_sa_email, ".gserviceaccount.com")
  description = "PostgreSQL IAM username for the worker runtime."
  sensitive   = true
}

output "migrate_database_user" {
  value       = trimsuffix(module.iam.migrate_sa_email, ".gserviceaccount.com")
  description = "PostgreSQL IAM username for the migration job."
  sensitive   = true
}
