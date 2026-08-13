# Private services access (VPC peering for Cloud SQL private IP).
resource "google_compute_global_address" "sql_private_ip" {
  project       = var.project_id
  name          = "financial-os-${var.environment}-sql-ip"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 20
  network       = var.vpc_network_id
}

resource "google_service_networking_connection" "sql_vpc_peering" {
  network                 = var.vpc_network_id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.sql_private_ip.name]
}

# ── Cloud SQL PostgreSQL 15 ────────────────────────────────────────────────────

resource "google_sql_database_instance" "main" {
  project             = var.project_id
  name                = "financial-os-${var.environment}"
  database_version    = "POSTGRES_15"
  region              = var.region
  deletion_protection = true

  settings {
    tier              = var.tier
    availability_type = var.availability_type # REGIONAL for production
    disk_type         = "PD_SSD"
    disk_autoresize   = true

    # Private IP only — no public IP (DB-01).
    ip_configuration {
      ipv4_enabled    = false
      private_network = var.vpc_network_id

      # IAM database authentication required for all runtime SAs (DB-01).
      enable_private_path_for_google_cloud_services = true
    }

    # Automated daily backups with 7-day retention and PITR enabled (DB-03).
    backup_configuration {
      enabled                        = true
      start_time                     = "03:00"
      point_in_time_recovery_enabled = true
      transaction_log_retention_days = 7
      backup_retention_settings {
        retained_backups = 7
        retention_unit   = "COUNT"
      }
    }

    # Cloud SQL Insights for query visibility without exposing data.
    insights_config {
      query_insights_enabled  = true
      query_string_length     = 256
      record_application_tags = false
      record_client_address   = false
    }

    database_flags {
      name  = "cloudsql.iam_authentication"
      value = "on"
    }
  }

  depends_on = [google_service_networking_connection.sql_vpc_peering]
}

# ── Databases ─────────────────────────────────────────────────────────────────

resource "google_sql_database" "app" {
  project  = var.project_id
  instance = google_sql_database_instance.main.name
  name     = "financialos"
}

# ── IAM database users (no passwords) ────────────────────────────────────────

resource "google_sql_user" "api_iam" {
  project  = var.project_id
  instance = google_sql_database_instance.main.name
  name     = trimsuffix(var.api_sa_email, ".gserviceaccount.com")
  type     = "CLOUD_IAM_SERVICE_ACCOUNT"
}

resource "google_sql_user" "worker_iam" {
  project  = var.project_id
  instance = google_sql_database_instance.main.name
  name     = trimsuffix(var.worker_sa_email, ".gserviceaccount.com")
  type     = "CLOUD_IAM_SERVICE_ACCOUNT"
}

resource "google_sql_user" "migrate_iam" {
  project  = var.project_id
  instance = google_sql_database_instance.main.name
  name     = trimsuffix(var.migrate_sa_email, ".gserviceaccount.com")
  type     = "CLOUD_IAM_SERVICE_ACCOUNT"
}
