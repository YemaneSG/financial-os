# ── Log-based metrics ─────────────────────────────────────────────────────────

resource "google_logging_metric" "acknowledged_receipts" {
  project     = var.project_id
  name        = "financial_os/acknowledged_receipts_total"
  description = "Count of durably acknowledged receipts."
  filter      = "jsonPayload.event=\"receipt.acknowledged\" AND resource.type=\"cloud_run_revision\""
  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
    labels {
      key         = "environment"
      value_type  = "STRING"
      description = "Deployment environment."
    }
  }
  label_extractors = {
    "environment" = "EXTRACT(jsonPayload.environment)"
  }
}

resource "google_logging_metric" "processing_terminal_failures" {
  project     = var.project_id
  name        = "financial_os/processing_terminal_failures_total"
  description = "Count of terminal-failed extraction attempts."
  filter      = "jsonPayload.event=\"processing.failed\" AND resource.type=\"cloud_run_revision\""
  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
    labels {
      key         = "safe_error_code"
      value_type  = "STRING"
      description = "Safe error code from the terminal failure."
    }
  }
  label_extractors = {
    "safe_error_code" = "EXTRACT(jsonPayload.safe_error_code)"
  }
}

resource "google_logging_metric" "lost_acknowledged_receipt_invariant" {
  project     = var.project_id
  name        = "financial_os/invariant_violation_rel001_total"
  description = "REL-001 invariant violation count. Any value > 0 is an incident."
  filter      = "jsonPayload.event=\"invariant.violation\" AND jsonPayload.invariant=\"REL-001\" AND resource.type=\"cloud_run_revision\""
  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
  }
}

resource "google_logging_metric" "cost_ceiling_exceeded" {
  project     = var.project_id
  name        = "financial_os/cost_ceiling_exceeded_total"
  description = "Count of extractions that hit the terminal cost circuit breaker."
  filter      = "jsonPayload.event=\"processing.cost_ceiling_exceeded\" AND resource.type=\"cloud_run_revision\""
  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
  }
}

# ── Uptime checks ─────────────────────────────────────────────────────────────

resource "google_monitoring_uptime_check_config" "api_live" {
  project      = var.project_id
  display_name = "Financial OS API liveness (${var.environment})"
  timeout      = "10s"
  period       = "60s"

  http_check {
    path           = "/health/live"
    port           = 443
    use_ssl        = true
    validate_ssl   = true
    request_method = "GET"
  }

  monitored_resource {
    type = "uptime_url"
    labels = {
      project_id = var.project_id
      host       = var.api_host
    }
  }

  content_matchers {
    content = "\"ok\""
    matcher = "CONTAINS_STRING"
  }
}

resource "google_monitoring_uptime_check_config" "api_ready" {
  project      = var.project_id
  display_name = "Financial OS API readiness (${var.environment})"
  timeout      = "10s"
  period       = "300s"

  http_check {
    path           = "/health/ready"
    port           = 443
    use_ssl        = true
    validate_ssl   = true
    request_method = "GET"
  }

  monitored_resource {
    type = "uptime_url"
    labels = {
      project_id = var.project_id
      host       = var.api_host
    }
  }

  content_matchers {
    content = "\"ok\""
    matcher = "CONTAINS_STRING"
  }
}

# ── Notification channel placeholder ─────────────────────────────────────────

resource "google_monitoring_notification_channel" "email" {
  project      = var.project_id
  display_name = "Financial OS Owner Email"
  type         = "email"
  labels = {
    email_address = var.alert_email
  }
}

# ── Alerting policies ─────────────────────────────────────────────────────────

resource "google_monitoring_alert_policy" "api_down" {
  project      = var.project_id
  display_name = "API liveness failure (${var.environment})"
  combiner     = "OR"

  conditions {
    display_name = "Uptime check failing"
    condition_threshold {
      filter          = "metric.type=\"monitoring.googleapis.com/uptime_check/check_passed\" AND resource.type=\"uptime_url\" AND metric.labels.check_id=\"${google_monitoring_uptime_check_config.api_live.uptime_check_id}\""
      comparison      = "COMPARISON_LT"
      threshold_value = 1
      duration        = "120s"
      aggregations {
        alignment_period     = "60s"
        per_series_aligner   = "ALIGN_NEXT_OLDER"
        cross_series_reducer = "REDUCE_COUNT_FALSE"
        group_by_fields      = ["resource.label.project_id"]
      }
    }
  }

  notification_channels = [google_monitoring_notification_channel.email.name]
  severity              = "CRITICAL"
}

resource "google_monitoring_alert_policy" "rel001_violation" {
  project      = var.project_id
  display_name = "REL-001 acknowledged-receipt loss invariant violated"
  combiner     = "OR"

  conditions {
    display_name = "REL-001 invariant violation detected"
    condition_threshold {
      filter          = "metric.type=\"logging.googleapis.com/user/financial_os/invariant_violation_rel001_total\" AND resource.type=\"cloud_run_revision\""
      comparison      = "COMPARISON_GT"
      threshold_value = 0
      duration        = "0s"
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_SUM"
      }
    }
  }

  notification_channels = [google_monitoring_notification_channel.email.name]
  severity              = "CRITICAL"

  documentation {
    content = "An acknowledged receipt has been detected as lost. This is a P0 incident. See runbook: docs/operations/runbooks/restore.md"
  }
}

resource "google_monitoring_alert_policy" "processing_failures" {
  project      = var.project_id
  display_name = "High terminal processing failure rate (${var.environment})"
  combiner     = "OR"

  conditions {
    display_name = "Terminal failures > 5 in 10 min"
    condition_threshold {
      filter          = "metric.type=\"logging.googleapis.com/user/financial_os/processing_terminal_failures_total\" AND resource.type=\"cloud_run_revision\""
      comparison      = "COMPARISON_GT"
      threshold_value = 5
      duration        = "0s"
      aggregations {
        alignment_period   = "600s"
        per_series_aligner = "ALIGN_SUM"
      }
    }
  }

  notification_channels = [google_monitoring_notification_channel.email.name]
  severity              = "WARNING"
}

resource "google_monitoring_alert_policy" "cost_circuit_breaker" {
  project      = var.project_id
  display_name = "Extraction cost circuit breaker triggered (${var.environment})"
  combiner     = "OR"

  conditions {
    display_name = "Any cost ceiling exceeded event"
    condition_threshold {
      filter          = "metric.type=\"logging.googleapis.com/user/financial_os/cost_ceiling_exceeded_total\" AND resource.type=\"cloud_run_revision\""
      comparison      = "COMPARISON_GT"
      threshold_value = 0
      duration        = "0s"
      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_SUM"
      }
    }
  }

  notification_channels = [google_monitoring_notification_channel.email.name]
  severity              = "WARNING"

  documentation {
    content = "An extraction attempt exceeded the MAX_EXTRACTION_COST_CENTS ceiling. The attempt is terminal. Manual review required."
  }
}

# ── Billing budget ─────────────────────────────────────────────────────────────

resource "google_billing_budget" "monthly" {
  billing_account = var.billing_account
  display_name    = "Financial OS ${var.environment} monthly budget"

  budget_filter {
    projects = ["projects/${var.project_number}"]
  }

  amount {
    specified_amount {
      currency_code = "USD"
      units         = tostring(var.monthly_budget_usd)
    }
  }

  threshold_rules {
    threshold_percent = 0.5
    spend_basis       = "CURRENT_SPEND"
  }

  threshold_rules {
    threshold_percent = 0.9
    spend_basis       = "CURRENT_SPEND"
  }

  threshold_rules {
    threshold_percent = 1.0
    spend_basis       = "CURRENT_SPEND"
  }

}
