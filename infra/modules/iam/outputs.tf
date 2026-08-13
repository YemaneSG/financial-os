output "api_sa_email" {
  value       = google_service_account.api.email
  description = "API service account email."
}

output "worker_sa_email" {
  value       = google_service_account.worker.email
  description = "Worker service account email."
}

output "task_invoker_sa_email" {
  value       = google_service_account.task_invoker.email
  description = "Cloud Tasks invoker service account email."
}

output "migrate_sa_email" {
  value       = google_service_account.migrate.email
  description = "Migration job service account email."
}

output "deploy_sa_email" {
  value       = google_service_account.deploy.email
  description = "CI/CD deploy service account email (federated via WIF, no key)."
}

output "wif_provider_name" {
  value       = google_iam_workload_identity_pool_provider.github.name
  description = "Full resource name of the WIF provider, used in GitHub Actions auth step."
}
