output "secret_ids" {
  value = {
    for k, v in google_secret_manager_secret.app : k => v.secret_id
  }
  description = "Map of logical name → Secret Manager secret ID."
}
