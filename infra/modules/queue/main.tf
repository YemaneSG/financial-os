# ── Cloud Tasks queue ─────────────────────────────────────────────────────────

resource "google_cloud_tasks_queue" "receipt_processing" {
  project  = var.project_id
  location = var.region
  name     = "receipt-processing"

  retry_config {
    # Bounded exponential backoff (QUE-02). The API acknowledges durably before
    # enqueuing; these retries cover transient worker/infra failures only.
    max_attempts       = 5
    min_backoff        = "10s"
    max_backoff        = "300s"
    max_doublings      = 4
    max_retry_duration = "0s" # unlimited duration; attempt count governs
  }

  rate_limits {
    max_dispatches_per_second = 10
    max_concurrent_dispatches = 5
  }

  # Stackdriver logging for all task lifecycle events (LOG-02).
  stackdriver_logging_config {
    sampling_ratio = 1.0
  }
}

# ── Cloud Scheduler — reconciliation sweep ────────────────────────────────────

resource "google_cloud_scheduler_job" "reconcile" {
  project     = var.project_id
  region      = var.region
  name        = "financial-os-${var.environment}-reconcile"
  description = "Triggers the stale-work reconciliation sweep in the worker."
  schedule    = "*/5 * * * *" # Every 5 minutes.
  time_zone   = "UTC"

  attempt_deadline = "30s"

  http_target {
    http_method = "POST"
    uri         = "${var.worker_base_url}/internal/v1/reconcile-processing"
    body        = base64encode("{}")

    headers = {
      "Content-Type" = "application/json"
    }

    # OIDC token: scheduler presents a token signed by the task invoker SA.
    # Worker validates audience matches its own URL (QUE-01).
    oidc_token {
      service_account_email = var.task_invoker_sa_email
      audience              = var.worker_base_url
    }
  }
}
