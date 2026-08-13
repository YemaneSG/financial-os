output "repository_url" {
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/financial-os"
  description = "Base URL for images in this Artifact Registry repository."
}
