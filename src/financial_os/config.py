"""Application settings loaded from environment variables.

All secrets in production come from Secret Manager via the runtime environment.
Never hard-code values here.
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Environment ───────────────────────────────────────────────────────────
    environment: str = "development"
    log_level: str = "INFO"
    service_name: str = "financial-os-api"
    pipeline_version: str = "local-dev"

    # ── GCP ───────────────────────────────────────────────────────────────────
    gcp_project_id: str = ""
    gcp_region: str = "us-central1"

    # ── Firebase ──────────────────────────────────────────────────────────────
    firebase_project_id: str = ""

    # ── Database ──────────────────────────────────────────────────────────────
    database_url: str = Field(
        default="postgresql+asyncpg://financialos:changeme@localhost:5432/financialos_dev"
    )
    database_iam_user: str = ""
    cloud_sql_instance_connection_name: str = ""

    # ── Storage ───────────────────────────────────────────────────────────────
    gcs_evidence_bucket: str = "dev-evidence-bucket"
    signed_url_lifetime_seconds: int = 900

    # ── Cloud Tasks ───────────────────────────────────────────────────────────
    cloud_tasks_queue_name: str = "receipt-processing"
    cloud_tasks_location: str = "us-central1"
    cloud_tasks_queue_path: str = ""
    cloud_tasks_worker_url: str = "http://localhost:8001/internal/v1/receipts/{receipt_id}/process"
    cloud_tasks_service_account_email: str = ""

    # ── Worker ────────────────────────────────────────────────────────────────
    worker_oidc_audience: str = "http://localhost:8001"
    worker_max_concurrent_extractions: int = 4

    # ── Extraction ────────────────────────────────────────────────────────────
    extraction_provider: str = "financial_os.adapters.extraction.vertex.VertexExtractionAdapter"
    vertex_model_id: str = "gemini-2.0-flash-001"
    vertex_location: str = "us-central1"
    extraction_prompt_version: str = "v1"
    extraction_schema_version: str = "v1"

    # ── Worker input ceilings (implementation-contracts.md §8) ────────────────
    worker_max_assets_per_extraction: int = 10
    worker_max_asset_bytes: int = 10_485_760  # 10 MiB
    worker_max_total_extraction_bytes: int = 52_428_800  # 50 MiB
    worker_max_prompt_tokens: int = 32_768  # placeholder; calibrate after P-01 benchmark
    worker_max_extraction_cost_cents: int = 50  # USD cents

    # ── Auth / allowlist ──────────────────────────────────────────────────────
    owner_allowlist: str = ""  # comma-separated "google:<subject_id>"
    session_version: int = 1

    # ── Security ──────────────────────────────────────────────────────────────
    cors_allowed_origin: str = "http://localhost:5173"
    max_image_byte_size: int = 10_485_760
    max_assets_per_receipt: int = 10
    rate_limit_rpm: int = 60

    # ── Reconciliation ────────────────────────────────────────────────────────
    reconcile_uploading_stale_seconds: int = 1800
    reconcile_queued_stale_seconds: int = 600
    reconcile_processing_stale_seconds: int = 300

    @property
    def allowed_owner_subjects(self) -> frozenset[str]:
        """Return frozenset of allowlisted provider subject IDs."""
        return frozenset(s.strip() for s in self.owner_allowlist.split(",") if s.strip())

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def use_cloud_sql(self) -> bool:
        return bool(self.cloud_sql_instance_connection_name)


def get_settings() -> Settings:
    return Settings()
