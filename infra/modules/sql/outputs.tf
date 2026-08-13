output "instance_name" {
  value       = google_sql_database_instance.main.name
  description = "Cloud SQL instance name."
}

output "instance_connection_name" {
  value       = google_sql_database_instance.main.connection_name
  description = "Cloud SQL instance connection name (PROJECT:REGION:INSTANCE)."
}

output "database_name" {
  value       = google_sql_database.app.name
  description = "Application database name."
}

output "private_ip" {
  value       = google_sql_database_instance.main.private_ip_address
  description = "Private IP address of the Cloud SQL instance."
}
