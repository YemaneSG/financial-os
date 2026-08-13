resource "google_artifact_registry_repository" "app" {
  project       = var.project_id
  location      = var.region
  repository_id = "financial-os"
  description   = "Financial OS container images."
  format        = "DOCKER"

  # Immutable tags are NOT enforced at registry level; immutability is enforced
  # by the deploy workflow which pins images by digest (CICD-03).

  # Vulnerability scanning is on by default in Artifact Registry.
  # Container scanning alerts are wired in the monitoring module.
}

# Deploy SA may push images; runtime SAs may only pull.
resource "google_artifact_registry_repository_iam_member" "deploy_writer" {
  project    = var.project_id
  location   = var.region
  repository = google_artifact_registry_repository.app.name
  role       = "roles/artifactregistry.writer"
  member     = "serviceAccount:${var.deploy_sa_email}"
}

resource "google_artifact_registry_repository_iam_member" "api_reader" {
  project    = var.project_id
  location   = var.region
  repository = google_artifact_registry_repository.app.name
  role       = "roles/artifactregistry.reader"
  member     = "serviceAccount:${var.api_sa_email}"
}

resource "google_artifact_registry_repository_iam_member" "worker_reader" {
  project    = var.project_id
  location   = var.region
  repository = google_artifact_registry_repository.app.name
  role       = "roles/artifactregistry.reader"
  member     = "serviceAccount:${var.worker_sa_email}"
}
