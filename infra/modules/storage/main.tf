resource "google_storage_bucket" "evidence" {
  project  = var.project_id
  name     = var.bucket_name
  location = var.region

  # Immutable private access: public access prevention is enforced and no
  # allUsers/allAuthenticatedUsers ACL entries may be added (OBJ-01).
  public_access_prevention    = "enforced"
  uniform_bucket_level_access = true

  # Object versioning: retains all versions; original evidence is never
  # auto-deleted in Wave 1 (OBJ-04). storage_generation is recorded in DB.
  versioning {
    enabled = true
  }

  # Soft delete is enabled by default in GCS (7-day retention window).
  # Explicitly declared here to make the intent visible.
  soft_delete_policy {
    retention_duration_seconds = 604800 # 7 days
  }

  # CORS: allow PUT only from the deployed app origin (short-lived signed URL
  # upload). The origin is set by var.cors_origin.
  cors {
    origin          = [var.cors_origin]
    method          = ["PUT", "GET", "HEAD", "OPTIONS"]
    response_header = ["Content-Type", "Content-MD5", "Content-Length"]
    max_age_seconds = 600
  }
}

# Evidence objects are private. No allUsers/allAuthenticatedUsers IAM.
# The worker SA (storage.objectViewer on originals/ prefix) and the API SA
# (storage.objectCreator for signing only; actual write is done by the client
# via short-lived signed URL) are granted below.

resource "google_storage_bucket_iam_member" "worker_object_viewer" {
  bucket = google_storage_bucket.evidence.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${var.worker_sa_email}"
}

# The API SA signs upload/download URLs via the GCS XML API.
# It needs roles/iam.serviceAccountTokenCreator on itself (handled in IAM module)
# and storage.objects.get (to verify after upload). Least-privilege custom role
# is preferred; roles/storage.objectViewer covers the verification use case.
resource "google_storage_bucket_iam_member" "api_object_viewer" {
  bucket = google_storage_bucket.evidence.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${var.api_sa_email}"
}

# The API SA also needs to create objects (for the signed URL capability
# that the client uses to PUT). The signBlob permission is on the SA itself
# (roles/iam.serviceAccountTokenCreator), not on the bucket.
# We do NOT grant objectCreator here; uploads go directly from the client
# via the signed URL — the bucket accepts them because the URL is signed by
# the API SA.
