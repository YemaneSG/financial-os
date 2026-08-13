# ── Secret Manager placeholder secrets ───────────────────────────────────────
# Secrets are created with an initial placeholder version.
# Real values are set by the operator via `gcloud secrets versions add`
# or via the Console — never via Terraform (to avoid state containing secrets).

locals {
  secrets = {
    "database-url"                = "PLACEHOLDER — set via: gcloud secrets versions add database-url --data-file=-"
    "owner-allowlist"             = "PLACEHOLDER — google:<your-subject-id>"
    "session-version"             = "1"
    "cors-allowed-origin"         = "PLACEHOLDER — https://your-project.web.app"
    "cloud-tasks-sa-email"        = "PLACEHOLDER — set after IAM module output"
    "cloud-tasks-worker-url"      = "PLACEHOLDER — set after Cloud Run module output"
    "worker-oidc-audience"        = "PLACEHOLDER — set after Cloud Run module output"
    "vertex-model-id"             = "gemini-2.0-flash-001"
    "extraction-prompt-version"   = "v1"
    "extraction-schema-version"   = "v1"
    "firebase-project-id"         = "PLACEHOLDER — your firebase project id"
    "signed-url-lifetime-seconds" = "900"
    "gcs-evidence-bucket"         = "PLACEHOLDER — your-project-id-financial-os-evidence-dev"
  }
}

resource "google_secret_manager_secret" "app" {
  for_each  = local.secrets
  project   = var.project_id
  secret_id = "financial-os-${var.environment}-${each.key}"

  replication {
    auto {}
  }

  labels = {
    environment = var.environment
    managed_by  = "terraform"
  }
}

# Placeholder versions — operators replace with real values before first deploy.
resource "google_secret_manager_secret_version" "app_placeholder" {
  for_each    = local.secrets
  secret      = google_secret_manager_secret.app[each.key].id
  secret_data = each.value

  # Prevent Terraform from tracking or rotating the real value after the first apply.
  lifecycle {
    ignore_changes = [secret_data]
  }
}
