terraform {
  required_version = ">= 1.9"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }

  # GCS backend configured via -backend-config on first init.
  # Never commit terraform.tfbackend or .terraform/ to source control.
  backend "gcs" {}
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# ── 1. Enable required GCP APIs ───────────────────────────────────────────────
module "apis" {
  source     = "../../modules/apis"
  project_id = var.project_id
}

# ── 2. Service accounts + WIF (all module resources depend on APIs) ───────────
module "iam" {
  source = "../../modules/iam"

  project_id  = var.project_id
  region      = var.region
  environment = var.environment
  github_org  = var.github_org
  github_repo = var.github_repo

  depends_on = [module.apis]
}

# ── 3. Private evidence bucket ────────────────────────────────────────────────
module "storage" {
  source = "../../modules/storage"

  project_id      = var.project_id
  region          = var.gcs_location
  bucket_name     = var.evidence_bucket_name
  api_sa_email    = module.iam.api_sa_email
  worker_sa_email = module.iam.worker_sa_email
  cors_origin     = var.cors_origin

  depends_on = [module.apis]
}

# ── 4. Cloud SQL PostgreSQL with PITR ─────────────────────────────────────────
module "sql" {
  source = "../../modules/sql"

  project_id        = var.project_id
  region            = var.region
  environment       = var.environment
  tier              = var.sql_tier
  availability_type = var.sql_availability_type
  vpc_network_id    = var.vpc_network_id
  api_sa_email      = module.iam.api_sa_email
  worker_sa_email   = module.iam.worker_sa_email
  migrate_sa_email  = module.iam.migrate_sa_email

  depends_on = [module.apis]
}

# ── 5. Secret Manager placeholders ────────────────────────────────────────────
module "secrets" {
  source = "../../modules/secrets"

  project_id  = var.project_id
  environment = var.environment

  depends_on = [module.apis]
}

# ── 6. Artifact Registry ──────────────────────────────────────────────────────
module "registry" {
  source = "../../modules/registry"

  project_id      = var.project_id
  region          = var.region
  deploy_sa_email = module.iam.deploy_sa_email
  api_sa_email    = module.iam.api_sa_email
  worker_sa_email = module.iam.worker_sa_email

  depends_on = [module.apis]
}

# ── 7. Cloud Run services + migration job ─────────────────────────────────────
# IMAGE is set to a placeholder; the deploy workflow substitutes the immutable
# digest before applying traffic (the lifecycle.ignore_changes block above
# prevents Terraform from reverting it). On the initial apply, Terraform
# creates the service; subsequent image updates are managed by the deploy workflow.
module "cloudrun" {
  source = "../../modules/cloudrun"

  project_id                   = var.project_id
  region                       = var.region
  environment                  = var.environment
  image_with_digest            = var.initial_image
  image_tag                    = "initial"
  api_sa_email                 = module.iam.api_sa_email
  worker_sa_email              = module.iam.worker_sa_email
  migrate_sa_email             = module.iam.migrate_sa_email
  task_invoker_sa_email        = module.iam.task_invoker_sa_email
  sql_instance_connection_name = module.sql.instance_connection_name
  vpc_network_name             = var.vpc_network_name
  vpc_subnetwork_name          = var.vpc_subnetwork_name
  api_min_instances            = var.api_min_instances
  api_max_instances            = var.api_max_instances
  worker_max_instances         = var.worker_max_instances

  api_secrets = [
    { env_var = "DATABASE_URL", secret_id = module.secrets.secret_ids["database-url"] },
    { env_var = "OWNER_ALLOWLIST", secret_id = module.secrets.secret_ids["owner-allowlist"] },
    { env_var = "SESSION_VERSION", secret_id = module.secrets.secret_ids["session-version"] },
    { env_var = "CORS_ALLOWED_ORIGIN", secret_id = module.secrets.secret_ids["cors-allowed-origin"] },
    { env_var = "GCS_EVIDENCE_BUCKET", secret_id = module.secrets.secret_ids["gcs-evidence-bucket"] },
    { env_var = "CLOUD_TASKS_SERVICE_ACCOUNT_EMAIL", secret_id = module.secrets.secret_ids["cloud-tasks-sa-email"] },
    { env_var = "CLOUD_TASKS_WORKER_URL", secret_id = module.secrets.secret_ids["cloud-tasks-worker-url"] },
    { env_var = "FIREBASE_PROJECT_ID", secret_id = module.secrets.secret_ids["firebase-project-id"] },
    { env_var = "SIGNED_URL_LIFETIME_SECONDS", secret_id = module.secrets.secret_ids["signed-url-lifetime-seconds"] },
  ]

  worker_secrets = [
    { env_var = "DATABASE_URL", secret_id = module.secrets.secret_ids["database-url"] },
    { env_var = "GCS_EVIDENCE_BUCKET", secret_id = module.secrets.secret_ids["gcs-evidence-bucket"] },
    { env_var = "FIREBASE_PROJECT_ID", secret_id = module.secrets.secret_ids["firebase-project-id"] },
    { env_var = "VERTEX_MODEL_ID", secret_id = module.secrets.secret_ids["vertex-model-id"] },
    { env_var = "EXTRACTION_PROMPT_VERSION", secret_id = module.secrets.secret_ids["extraction-prompt-version"] },
    { env_var = "EXTRACTION_SCHEMA_VERSION", secret_id = module.secrets.secret_ids["extraction-schema-version"] },
    { env_var = "CLOUD_TASKS_SERVICE_ACCOUNT_EMAIL", secret_id = module.secrets.secret_ids["cloud-tasks-sa-email"] },
    { env_var = "CLOUD_TASKS_WORKER_URL", secret_id = module.secrets.secret_ids["cloud-tasks-worker-url"] },
    { env_var = "WORKER_OIDC_AUDIENCE", secret_id = module.secrets.secret_ids["worker-oidc-audience"] },
  ]

  migrate_secrets = [
    { env_var = "DATABASE_URL", secret_id = module.secrets.secret_ids["database-url"] },
  ]

  depends_on = [module.sql, module.registry, module.secrets, module.iam]
}

# ── 8. Cloud Tasks queue + Scheduler ─────────────────────────────────────────
module "queue" {
  source = "../../modules/queue"

  project_id            = var.project_id
  region                = var.region
  environment           = var.environment
  worker_base_url       = module.cloudrun.worker_url
  task_invoker_sa_email = module.iam.task_invoker_sa_email

  depends_on = [module.cloudrun]
}

# ── 9. Monitoring, alerting, and budget ───────────────────────────────────────
module "monitoring" {
  source = "../../modules/monitoring"

  project_id         = var.project_id
  project_number     = var.project_number
  environment        = var.environment
  api_host           = trimprefix(module.cloudrun.api_url, "https://")
  alert_email        = var.alert_email
  billing_account    = var.billing_account
  monthly_budget_usd = var.monthly_budget_usd

  depends_on = [module.cloudrun]
}
