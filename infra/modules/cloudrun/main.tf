# ── Public-facing API service ─────────────────────────────────────────────────

resource "google_cloud_run_v2_service" "api" {
  project  = var.project_id
  name     = "financial-os-${var.environment}-api"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL" # Public; authenticated by Firebase JWT (IAM-01).

  template {
    service_account = var.api_sa_email

    vpc_access {
      egress = "PRIVATE_RANGES_ONLY"
      network_interfaces {
        network    = var.vpc_network_name
        subnetwork = var.vpc_subnetwork_name
        tags       = ["financial-os-api"]
      }
    }

    scaling {
      min_instance_count = var.api_min_instances
      max_instance_count = var.api_max_instances # Protects Cloud SQL connections (OPS-01).
    }

    # Startup probe: wait for readiness before sending traffic.
    containers {
      name  = "api"
      image = var.image_with_digest

      ports {
        name           = "http1"
        container_port = 8080
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
        cpu_idle = true # Scale to zero between requests.
      }

      # All configuration comes from Secret Manager (DB-01, no credential in source).
      env {
        name  = "ENVIRONMENT"
        value = var.environment
      }
      env {
        name  = "SERVICE_NAME"
        value = "financial-os-api"
      }
      env {
        name  = "PIPELINE_VERSION"
        value = var.image_tag
      }
      env {
        name  = "GCP_PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "GCP_REGION"
        value = var.region
      }
      env {
        name  = "CLOUD_SQL_INSTANCE_CONNECTION_NAME"
        value = var.sql_instance_connection_name
      }
      env {
        name  = "DATABASE_IAM_USER"
        value = trimsuffix(var.api_sa_email, ".gserviceaccount.com")
      }
      env {
        name  = "CLOUD_TASKS_QUEUE_PATH"
        value = "projects/${var.project_id}/locations/${var.region}/queues/receipt-processing"
      }

      # Secrets: each item binds one Secret Manager version to an env var.
      dynamic "env" {
        for_each = var.api_secrets
        content {
          name = env.value.env_var
          value_source {
            secret_key_ref {
              secret  = env.value.secret_id
              version = "latest"
            }
          }
        }
      }

      # Cloud Run adds this mount automatically when a Cloud SQL volume is
      # declared. Keep it explicit so the provider does not report drift.
      volume_mounts {
        name       = "cloudsql"
        mount_path = "/cloudsql"
      }

      startup_probe {
        http_get {
          path = "/health/live"
          port = 8080
        }
        initial_delay_seconds = 5
        period_seconds        = 5
        failure_threshold     = 10
      }

      liveness_probe {
        http_get {
          path = "/health/live"
          port = 8080
        }
        period_seconds    = 30
        failure_threshold = 3
      }
    }

    # Cloud SQL connector (IAM auth, no password).
    volumes {
      name = "cloudsql"
      cloud_sql_instance {
        instances = [var.sql_instance_connection_name]
      }
    }
  }

  lifecycle {
    # Prevent Terraform from downgrading a revision that was already deployed
    # with traffic. Traffic switching is done explicitly by the deploy workflow.
    ignore_changes = [
      client,
      client_version,
      scaling,
      template[0].containers[0].image,
      traffic,
    ]
  }
}

# Allow unauthenticated callers to reach the API (Firebase JWT is validated at
# the application layer, not by Cloud Run IAM — IAM-01).
resource "google_cloud_run_v2_service_iam_member" "api_public" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.api.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# ── Private worker service ────────────────────────────────────────────────────

resource "google_cloud_run_v2_service" "worker" {
  project  = var.project_id
  name     = "financial-os-${var.environment}-worker"
  location = var.region

  # Internal ingress: only Cloud Tasks and Cloud Scheduler can reach this.
  # Direct public invocation fails (NET-01, QUE-01).
  ingress = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"

  template {
    service_account = var.worker_sa_email

    vpc_access {
      egress = "PRIVATE_RANGES_ONLY"
      network_interfaces {
        network    = var.vpc_network_name
        subnetwork = var.vpc_subnetwork_name
        tags       = ["financial-os-worker"]
      }
    }

    scaling {
      min_instance_count = 0
      max_instance_count = var.worker_max_instances
    }

    containers {
      name  = "worker"
      image = var.image_with_digest

      ports {
        name           = "http1"
        container_port = 8080
      }

      resources {
        limits = {
          cpu    = "2"
          memory = "2Gi"
        }
        # Keep CPU allocated during request processing (extraction is CPU-bound).
        cpu_idle = false
      }

      env {
        name  = "ENVIRONMENT"
        value = var.environment
      }
      env {
        name  = "SERVICE_NAME"
        value = "financial-os-worker"
      }
      env {
        name  = "PIPELINE_VERSION"
        value = var.image_tag
      }
      env {
        name  = "GCP_PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "GCP_REGION"
        value = var.region
      }
      env {
        name  = "CLOUD_SQL_INSTANCE_CONNECTION_NAME"
        value = var.sql_instance_connection_name
      }
      env {
        name  = "DATABASE_IAM_USER"
        value = trimsuffix(var.worker_sa_email, ".gserviceaccount.com")
      }
      env {
        name  = "CLOUD_TASKS_QUEUE_PATH"
        value = "projects/${var.project_id}/locations/${var.region}/queues/receipt-processing"
      }

      dynamic "env" {
        for_each = var.worker_secrets
        content {
          name = env.value.env_var
          value_source {
            secret_key_ref {
              secret  = env.value.secret_id
              version = "latest"
            }
          }
        }
      }

      volume_mounts {
        name       = "cloudsql"
        mount_path = "/cloudsql"
      }

      startup_probe {
        http_get {
          path = "/health/live"
          port = 8080
        }
        initial_delay_seconds = 5
        period_seconds        = 5
        failure_threshold     = 10
      }
    }

    volumes {
      name = "cloudsql"
      cloud_sql_instance {
        instances = [var.sql_instance_connection_name]
      }
    }
  }

  lifecycle {
    ignore_changes = [
      client,
      client_version,
      scaling,
      template[0].containers[0].image,
      traffic,
    ]
  }
}

# Only the task invoker SA may call the worker (QUE-01).
resource "google_cloud_run_v2_service_iam_member" "worker_task_invoker" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.worker.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${var.task_invoker_sa_email}"
}

# ── Migration job (pre-deploy, one-shot) ──────────────────────────────────────

resource "google_cloud_run_v2_job" "migrate" {
  project             = var.project_id
  name                = "financial-os-${var.environment}-migrate"
  location            = var.region
  deletion_protection = false # Disposable runner; the database remains protected.

  template {
    template {
      service_account = var.migrate_sa_email
      max_retries     = 0 # Never retry a migration. Fail fast.

      vpc_access {
        egress = "PRIVATE_RANGES_ONLY"
        network_interfaces {
          network    = var.vpc_network_name
          subnetwork = var.vpc_subnetwork_name
          tags       = ["financial-os-migrate"]
        }
      }

      containers {
        name  = "migrate"
        image = var.image_with_digest

        command = ["alembic"]
        args    = ["upgrade", "head"]

        env {
          name  = "CLOUD_SQL_INSTANCE_CONNECTION_NAME"
          value = var.sql_instance_connection_name
        }
        env {
          name  = "DATABASE_IAM_USER"
          value = trimsuffix(var.migrate_sa_email, ".gserviceaccount.com")
        }
        env {
          name  = "API_DATABASE_USER"
          value = trimsuffix(var.api_sa_email, ".gserviceaccount.com")
        }
        env {
          name  = "WORKER_DATABASE_USER"
          value = trimsuffix(var.worker_sa_email, ".gserviceaccount.com")
        }

        resources {
          limits = {
            cpu    = "1"
            memory = "512Mi"
          }
        }

        dynamic "env" {
          for_each = var.migrate_secrets
          content {
            name = env.value.env_var
            value_source {
              secret_key_ref {
                secret  = env.value.secret_id
                version = "latest"
              }
            }
          }
        }


        volume_mounts {
          name       = "cloudsql"
          mount_path = "/cloudsql"
        }
      }

      volumes {
        name = "cloudsql"
        cloud_sql_instance {
          instances = [var.sql_instance_connection_name]
        }
      }
    }
  }

  lifecycle {
    ignore_changes = [
      client,
      client_version,
      template[0].template[0].containers[0].image,
    ]
  }
}
