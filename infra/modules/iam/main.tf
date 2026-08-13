# ── Service accounts ──────────────────────────────────────────────────────────

resource "google_service_account" "api" {
  project      = var.project_id
  account_id   = "financial-os-${var.environment}-api"
  display_name = "Financial OS API (${var.environment})"
  description  = "Runtime identity for the public-facing API Cloud Run service."
}

resource "google_service_account" "worker" {
  project      = var.project_id
  account_id   = "financial-os-${var.environment}-worker"
  display_name = "Financial OS Worker (${var.environment})"
  description  = "Runtime identity for the private extraction worker Cloud Run service."
}

resource "google_service_account" "task_invoker" {
  project      = var.project_id
  account_id   = "financial-os-${var.environment}-tasks"
  display_name = "Financial OS Task Invoker (${var.environment})"
  description  = "Identity used by Cloud Tasks to sign OIDC tokens for worker delivery."
}

resource "google_service_account" "migrate" {
  project      = var.project_id
  account_id   = "financial-os-${var.environment}-migrate"
  display_name = "Financial OS Migration Job (${var.environment})"
  description  = "One-shot migration runner with DDL rights. Used in the pre-deploy step only."
}

resource "google_service_account" "deploy" {
  project      = var.project_id
  account_id   = "financial-os-${var.environment}-deploy"
  display_name = "Financial OS Deploy (${var.environment})"
  description  = "CI/CD deploy identity federated from GitHub Actions via WIF. No long-lived key."
}

# ── Workload Identity Federation pool + provider (GitHub Actions) ─────────────

resource "google_iam_workload_identity_pool" "github" {
  project                   = var.project_id
  workload_identity_pool_id = var.wif_pool_id
  display_name              = "GitHub Actions pool"
  description               = "WIF pool for GitHub Actions OIDC federation."
}

resource "google_iam_workload_identity_pool_provider" "github" {
  project                            = var.project_id
  workload_identity_pool_id          = google_iam_workload_identity_pool.github.workload_identity_pool_id
  workload_identity_pool_provider_id = var.wif_provider_id
  display_name                       = "GitHub Actions provider"

  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.repository" = "assertion.repository"
    "attribute.ref"        = "assertion.ref"
    "attribute.actor"      = "assertion.actor"
  }

  # Only the specific repository may use this provider.
  attribute_condition = "assertion.repository == '${var.github_org}/${var.github_repo}' && assertion.ref == 'refs/heads/main'"

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

# Allow GitHub Actions (main branch pushes and manual workflow_dispatch) to
# impersonate the deploy service account. Restrict to the main branch.
resource "google_service_account_iam_member" "deploy_wif_main" {
  service_account_id = google_service_account.deploy.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github.name}/attribute.repository/${var.github_org}/${var.github_repo}"
}

# ── API service account IAM bindings ──────────────────────────────────────────

resource "google_project_iam_member" "api_sql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.api.email}"
}

resource "google_project_iam_member" "api_sql_instance_user" {
  project = var.project_id
  role    = "roles/cloudsql.instanceUser"
  member  = "serviceAccount:${google_service_account.api.email}"
}

resource "google_project_iam_member" "api_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.api.email}"
}

resource "google_project_iam_member" "api_tasks_enqueuer" {
  project = var.project_id
  role    = "roles/cloudtasks.enqueuer"
  member  = "serviceAccount:${google_service_account.api.email}"
}

# Creating an OIDC task requires the enqueuer to act as the task identity.
resource "google_service_account_iam_member" "api_acts_as_task_invoker" {
  service_account_id = google_service_account.task_invoker.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.api.email}"
}

resource "google_project_iam_member" "api_log_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.api.email}"
}

resource "google_project_iam_member" "api_metric_writer" {
  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.api.email}"
}

# ── Worker service account IAM bindings ───────────────────────────────────────

resource "google_project_iam_member" "worker_sql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.worker.email}"
}

resource "google_project_iam_member" "worker_sql_instance_user" {
  project = var.project_id
  role    = "roles/cloudsql.instanceUser"
  member  = "serviceAccount:${google_service_account.worker.email}"
}

resource "google_project_iam_member" "worker_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.worker.email}"
}

resource "google_project_iam_member" "worker_vertex_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.worker.email}"
}

resource "google_project_iam_member" "worker_log_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.worker.email}"
}

resource "google_project_iam_member" "worker_metric_writer" {
  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.worker.email}"
}

# ── Task invoker: may call Cloud Run invoker on the worker service ────────────
# Bound at the service level after cloudrun module creates the worker service.
# The caller passes worker_service_url; binding is conditional on it being set.

resource "google_project_iam_member" "task_invoker_sa_user" {
  project = var.project_id
  role    = "roles/iam.serviceAccountTokenCreator"
  member  = "serviceAccount:${google_service_account.task_invoker.email}"
}

# ── Migrate service account ───────────────────────────────────────────────────

resource "google_project_iam_member" "migrate_sql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.migrate.email}"
}

resource "google_project_iam_member" "migrate_sql_instance_user" {
  project = var.project_id
  role    = "roles/cloudsql.instanceUser"
  member  = "serviceAccount:${google_service_account.migrate.email}"
}

# ── Deploy service account ────────────────────────────────────────────────────
# Narrow roles: push images to AR, update Cloud Run services, impersonate
# runtime SAs (to set them on Cloud Run revisions).

resource "google_project_iam_member" "deploy_run_admin" {
  project = var.project_id
  role    = "roles/run.admin"
  member  = "serviceAccount:${google_service_account.deploy.email}"
}

resource "google_project_iam_member" "deploy_ar_writer" {
  project = var.project_id
  role    = "roles/artifactregistry.writer"
  member  = "serviceAccount:${google_service_account.deploy.email}"
}

resource "google_project_iam_member" "deploy_firebase_hosting_admin" {
  project = var.project_id
  role    = "roles/firebasehosting.admin"
  member  = "serviceAccount:${google_service_account.deploy.email}"
}

# Deploy SA must be able to act as the runtime SAs when assigning them to revisions.
resource "google_service_account_iam_member" "deploy_acts_as_api" {
  service_account_id = google_service_account.api.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.deploy.email}"
}

resource "google_service_account_iam_member" "deploy_acts_as_worker" {
  service_account_id = google_service_account.worker.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.deploy.email}"
}

resource "google_service_account_iam_member" "deploy_acts_as_migrate" {
  service_account_id = google_service_account.migrate.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.deploy.email}"
}
