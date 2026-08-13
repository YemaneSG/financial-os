#!/usr/bin/env zsh
# Derive private deployment inputs from the active gcloud account. This file
# contains no deployment identifiers or credentials and is safe to version.
# Source it before Terraform commands; never print the exported values.

set -euo pipefail

export TF_VAR_project_id="$(gcloud config get-value project 2>/dev/null)"
if [[ -z "${TF_VAR_project_id}" || "${TF_VAR_project_id}" == "(unset)" ]]; then
  print -u2 "No active gcloud project is configured."
  return 1
fi

export GOOGLE_OAUTH_ACCESS_TOKEN="$(gcloud auth print-access-token)"
export TF_VAR_project_number="$(
  gcloud projects describe "${TF_VAR_project_id}" --format='value(projectNumber)'
)"
export TF_VAR_billing_account="$(
  gcloud billing accounts list --filter='open=true' --limit=1 --format='value(name)'
)"
export TF_VAR_alert_email="$(
  gcloud auth list --filter='status:ACTIVE' --limit=1 --format='value(account)'
)"

export TF_VAR_region="us-central1"
export TF_VAR_environment="dev"
export TF_VAR_gcs_location="us-central1"
export TF_VAR_evidence_bucket_name="${TF_VAR_project_id}-financial-os-evidence-dev"
export TF_VAR_cors_origin="https://${TF_VAR_project_id}.web.app"
export TF_VAR_vpc_network_id="projects/${TF_VAR_project_id}/global/networks/default"
export TF_VAR_vpc_network_name="default"
export TF_VAR_vpc_subnetwork_name="default"
export TF_VAR_sql_tier="db-g1-small"
export TF_VAR_sql_availability_type="ZONAL"
export TF_VAR_github_org="YemaneSG"
export TF_VAR_github_repo="FinancialOs"
export TF_VAR_api_min_instances="0"
export TF_VAR_api_max_instances="5"
export TF_VAR_worker_max_instances="3"
export TF_VAR_monthly_budget_usd="50"

export FINOS_STATE_BUCKET="${TF_VAR_project_id}-financial-os-tfstate"
export FINOS_REGISTRY="${TF_VAR_region}-docker.pkg.dev/${TF_VAR_project_id}/financial-os"
export TF_VAR_initial_image="${FINOS_IMAGE_REF:-${FINOS_REGISTRY}/app@sha256:0000000000000000000000000000000000000000000000000000000000000000}"
