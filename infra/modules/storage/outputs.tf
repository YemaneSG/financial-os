output "bucket_name" {
  value       = google_storage_bucket.evidence.name
  description = "Evidence bucket name."
}

output "bucket_url" {
  value       = google_storage_bucket.evidence.url
  description = "gs:// URL of the evidence bucket."
}
