"""Initial schema — all Wave 1 tables.

Revision ID: 001
Revises: (none)
Create Date: 2026-08-12

Migration strategy: additive only. No breaking changes in Wave 1.
Services must never call alembic upgrade head at startup (A-02).

The migration user has DDL rights; API/worker runtime roles have DML only (DB-01).
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── auth_subjects ──────────────────────────────────────────────────────────
    op.create_table(
        "auth_subjects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("provider", sa.Text, nullable=False),
        sa.Column("provider_subject", sa.Text, nullable=False, unique=True),
        sa.Column("allowlisted", sa.Boolean, nullable=False, default=False),
        sa.Column("valid_after", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_auth_subjects_provider_subject", "auth_subjects", ["provider_subject"])

    # ── receipts (with deferred FK for current_revision_id) ───────────────────
    op.create_table(
        "receipts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("client_submission_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("financial_context", sa.Text, nullable=False, server_default="personal"),
        sa.Column("processing_status", sa.Text, nullable=False, server_default="reserved"),
        sa.Column("verification_status", sa.Text, nullable=False, server_default="unreviewed"),
        sa.Column("current_revision_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("expected_asset_count", sa.Integer, nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("row_version", sa.Integer, nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "processing_status IN ("
            "'reserved','uploading','uploaded','queued','processing',"
            "'extracted','retryable_failed','failed','abandoned')",
            name="ck_receipt_processing_status",
        ),
        sa.CheckConstraint(
            "verification_status IN ("
            "'unreviewed','system_validated','needs_review','human_verified')",
            name="ck_receipt_verification_status",
        ),
        sa.CheckConstraint(
            "financial_context IN ('personal','rental_property')",
            name="ck_receipt_financial_context",
        ),
        sa.CheckConstraint("expected_asset_count > 0", name="ck_receipt_expected_asset_count"),
        sa.UniqueConstraint("owner_id", "client_submission_id", name="uq_receipt_owner_submission"),
    )
    op.create_index("ix_receipts_owner_id", "receipts", ["owner_id"])

    # ── receipt_assets ─────────────────────────────────────────────────────────
    op.create_table(
        "receipt_assets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "receipt_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("receipts.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("ordinal", sa.Integer, nullable=False),
        sa.Column("object_key", sa.Text, nullable=False, unique=True),
        sa.Column("storage_generation", sa.Text, nullable=True),
        sa.Column("declared_mime_type", sa.Text, nullable=False),
        sa.Column("verified_mime_type", sa.Text, nullable=True),
        sa.Column("byte_size", sa.BigInteger, nullable=True),
        sa.Column("sha256", sa.String(64), nullable=True),
        sa.Column("upload_status", sa.Text, nullable=False, server_default="reserved"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("ordinal >= 1", name="ck_asset_ordinal"),
        sa.CheckConstraint(
            "upload_status IN ('reserved','uploaded','verified','rejected')",
            name="ck_asset_upload_status",
        ),
        sa.UniqueConstraint("receipt_id", "ordinal", name="uq_asset_receipt_ordinal"),
    )
    op.create_index("ix_receipt_assets_receipt_id", "receipt_assets", ["receipt_id"])

    # ── processing_attempts ────────────────────────────────────────────────────
    op.create_table(
        "processing_attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "receipt_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("receipts.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("pipeline_version", sa.Text, nullable=False),
        sa.Column("attempt_number", sa.Integer, nullable=False),
        sa.Column("queue_task_name", sa.Text, nullable=True),
        sa.Column("status", sa.Text, nullable=False, server_default="queued"),
        sa.Column("safe_error_code", sa.Text, nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('queued','running','retryable_failed','terminal_failed','succeeded')",
            name="ck_attempt_status",
        ),
        sa.UniqueConstraint(
            "receipt_id",
            "pipeline_version",
            "attempt_number",
            name="uq_attempt_receipt_pipeline_attempt",
        ),
    )
    op.create_index("ix_processing_attempts_receipt_id", "processing_attempts", ["receipt_id"])

    # ── receipt_revisions ──────────────────────────────────────────────────────
    op.create_table(
        "receipt_revisions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "receipt_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("receipts.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("parent_revision_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("source_type", sa.Text, nullable=False),
        sa.Column("extraction_run_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("merchant_raw", sa.Text, nullable=True),
        sa.Column("merchant_normalized", sa.Text, nullable=True),
        sa.Column("purchase_datetime", sa.DateTime(timezone=True), nullable=True),
        sa.Column("purchase_timezone", sa.Text, nullable=True),
        sa.Column("currency", sa.Text, nullable=False),
        sa.Column("subtotal_minor", sa.BigInteger, nullable=True),
        sa.Column("tax_minor", sa.BigInteger, nullable=True),
        sa.Column("tip_minor", sa.BigInteger, nullable=True),
        sa.Column("discount_minor", sa.BigInteger, nullable=True),
        sa.Column("total_minor", sa.BigInteger, nullable=True),
        sa.Column("payment_method_hint", sa.Text, nullable=True),
        sa.Column("overall_confidence", sa.Numeric(5, 4), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "source_type IN ('extractor','human','import')",
            name="ck_revision_source_type",
        ),
    )
    op.create_index("ix_receipt_revisions_receipt_id", "receipt_revisions", ["receipt_id"])

    # ── extraction_runs ────────────────────────────────────────────────────────
    op.create_table(
        "extraction_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "receipt_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("receipts.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "processing_attempt_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("processing_attempts.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("provider", sa.Text, nullable=False),
        sa.Column("model_id", sa.Text, nullable=False),
        sa.Column("prompt_version", sa.Text, nullable=False),
        sa.Column("schema_version", sa.Text, nullable=False),
        sa.Column("asset_manifest_hash", sa.Text, nullable=False),
        sa.Column("raw_response", postgresql.JSONB, nullable=True),
        sa.Column("provider_request_id", sa.Text, nullable=True),
        sa.Column("status", sa.Text, nullable=False, server_default="started"),
        sa.Column(
            "input_metadata",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("latency_ms", sa.Integer, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('started','succeeded','invalid','failed')",
            name="ck_extraction_run_status",
        ),
    )
    op.create_index("ix_extraction_runs_receipt_id", "extraction_runs", ["receipt_id"])
    op.create_index("ix_extraction_runs_manifest_hash", "extraction_runs", ["asset_manifest_hash"])

    # ── line_item_revisions ────────────────────────────────────────────────────
    op.create_table(
        "line_item_revisions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "receipt_revision_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("receipt_revisions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("ordinal", sa.Integer, nullable=False),
        sa.Column("raw_description", sa.Text, nullable=False),
        sa.Column("normalized_description", sa.Text, nullable=True),
        sa.Column("quantity", sa.Numeric(18, 6), nullable=True),
        sa.Column("unit", sa.Text, nullable=True),
        sa.Column("unit_price_decimal", sa.Numeric(18, 6), nullable=True),
        sa.Column("line_total_minor", sa.BigInteger, nullable=True),
        sa.Column("discount_minor", sa.BigInteger, nullable=True),
        sa.Column("category_suggestion", sa.Text, nullable=True),
        sa.Column(
            "field_confidence",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.CheckConstraint("ordinal >= 1", name="ck_line_item_ordinal"),
        sa.UniqueConstraint("receipt_revision_id", "ordinal", name="uq_line_item_revision_ordinal"),
    )
    op.create_index(
        "ix_line_item_revisions_revision_id", "line_item_revisions", ["receipt_revision_id"]
    )

    # ── validation_findings ────────────────────────────────────────────────────
    op.create_table(
        "validation_findings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "receipt_revision_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("receipt_revisions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("check_code", sa.Text, nullable=False),
        sa.Column("outcome", sa.Text, nullable=False),
        sa.Column(
            "observed",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("expected", postgresql.JSONB, nullable=True),
        sa.Column("rule_version", sa.Text, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "outcome IN ('pass','warn','fail','not_applicable')",
            name="ck_finding_outcome",
        ),
    )
    op.create_index(
        "ix_validation_findings_revision_id", "validation_findings", ["receipt_revision_id"]
    )

    # ── state_events ───────────────────────────────────────────────────────────
    op.create_table(
        "state_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "receipt_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("receipts.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("dimension", sa.Text, nullable=False),
        sa.Column("from_state", sa.Text, nullable=True),
        sa.Column("to_state", sa.Text, nullable=False),
        sa.Column("actor_type", sa.Text, nullable=False),
        sa.Column("reason_code", sa.Text, nullable=False),
        sa.Column("correlation_id", sa.Text, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "dimension IN ('processing','verification','financial_context')",
            name="ck_event_dimension",
        ),
        sa.CheckConstraint(
            "actor_type IN ('user','api','worker','scheduler','import')",
            name="ck_event_actor_type",
        ),
    )
    op.create_index("ix_state_events_receipt_id", "state_events", ["receipt_id"])

    # ── Deferred FKs for circular references ──────────────────────────────────
    # receipts.current_revision_id → receipt_revisions.id
    op.create_foreign_key(
        "fk_receipt_current_revision",
        "receipts",
        "receipt_revisions",
        ["current_revision_id"],
        ["id"],
        use_alter=True,
    )
    # receipt_revisions.extraction_run_id → extraction_runs.id
    op.create_foreign_key(
        "fk_revision_extraction_run",
        "receipt_revisions",
        "extraction_runs",
        ["extraction_run_id"],
        ["id"],
        use_alter=True,
    )
    # receipt_revisions.parent_revision_id → receipt_revisions.id
    op.create_foreign_key(
        "fk_revision_parent",
        "receipt_revisions",
        "receipt_revisions",
        ["parent_revision_id"],
        ["id"],
        use_alter=True,
    )


def downgrade() -> None:
    # Drop in reverse dependency order.
    op.drop_constraint("fk_revision_parent", "receipt_revisions", type_="foreignkey")
    op.drop_constraint("fk_revision_extraction_run", "receipt_revisions", type_="foreignkey")
    op.drop_constraint("fk_receipt_current_revision", "receipts", type_="foreignkey")

    op.drop_table("state_events")
    op.drop_table("validation_findings")
    op.drop_table("line_item_revisions")
    op.drop_table("extraction_runs")
    op.drop_table("receipt_revisions")
    op.drop_table("processing_attempts")
    op.drop_table("receipt_assets")
    op.drop_table("receipts")
    op.drop_table("auth_subjects")
