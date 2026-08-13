output "api_url" {
  value       = google_cloud_run_v2_service.api.uri
  description = "Cloud Run API service URL."
}

output "worker_url" {
  value       = google_cloud_run_v2_service.worker.uri
  description = "Cloud Run worker service URL (internal only)."
}

output "migrate_job_name" {
  value       = google_cloud_run_v2_job.migrate.name
  description = "Migration Cloud Run Job name."
}
