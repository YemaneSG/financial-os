"""Add deduplication state axis to receipts; extend state_events dimension.

Revision ID: 002
Revises: 001
Create Date: 2026-08-15

Additive only — no existing columns, data, or indexes are removed or modified.
The state_events dimension check constraint is replaced with an extended version
that adds 'deduplication' to the allowed values.

Services never call alembic upgrade head at startup (A-02).
The migration user has DDL rights; API/worker runtime roles have DML only (DB-01).
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002"
down_revision: str | None = "001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── Deduplication columns on receipts ─────────────────────────────────────
    op.add_column(
        "receipts",
        sa.Column(
            "deduplication_status",
            sa.Text,
            nullable=False,
            server_default=sa.text("'unchecked'"),
        ),
    )
    op.add_column(
        "receipts",
        sa.Column("canonical_receipt_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "receipts",
        sa.Column("evidence_fingerprint", sa.String(64), nullable=True),
    )
    op.add_column(
        "receipts",
        sa.Column("semantic_fingerprint", sa.String(64), nullable=True),
    )
    op.add_column(
        "receipts",
        sa.Column("deduplication_method", sa.Text, nullable=True),
    )
    op.add_column(
        "receipts",
        sa.Column("deduplication_rule_version", sa.Text, nullable=True),
    )
    op.add_column(
        "receipts",
        sa.Column("deduplication_checked_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ── CHECK constraint for deduplication_status ─────────────────────────────
    op.create_check_constraint(
        "ck_receipt_deduplication_status",
        "receipts",
        "deduplication_status IN "
        "('unchecked','unique','suspected_duplicate','confirmed_duplicate')",
    )
    op.create_check_constraint(
        "ck_receipt_canonical_not_self",
        "receipts",
        "canonical_receipt_id IS NULL OR canonical_receipt_id <> id",
    )

    # ── Self-referential FK: canonical_receipt_id → receipts.id ──────────────
    op.create_foreign_key(
        "fk_receipt_canonical",
        "receipts",
        "receipts",
        ["canonical_receipt_id"],
        ["id"],
        use_alter=True,
        ondelete="RESTRICT",
    )

    # ── Partial indexes for fast owner-scoped fingerprint lookups ─────────────
    op.create_index(
        "ix_receipts_owner_evidence_fp",
        "receipts",
        ["owner_id", "evidence_fingerprint"],
        postgresql_where=sa.text("evidence_fingerprint IS NOT NULL"),
    )
    op.create_index(
        "ix_receipts_owner_semantic_fp",
        "receipts",
        ["owner_id", "semantic_fingerprint"],
        postgresql_where=sa.text("semantic_fingerprint IS NOT NULL"),
    )
    op.create_index(
        "ix_receipts_owner_dedup_status",
        "receipts",
        ["owner_id", "deduplication_status"],
    )

    # ── Extend ck_event_dimension to include 'deduplication' ─────────────────
    # Drop the Wave 1 constraint and recreate with the new value.
    op.drop_constraint("ck_event_dimension", "state_events", type_="check")
    op.create_check_constraint(
        "ck_event_dimension",
        "state_events",
        "dimension IN ('processing','verification','financial_context','deduplication')",
    )


def downgrade() -> None:
    # Restore original dimension constraint.
    op.drop_constraint("ck_event_dimension", "state_events", type_="check")
    op.create_check_constraint(
        "ck_event_dimension",
        "state_events",
        "dimension IN ('processing','verification','financial_context')",
    )

    op.drop_index("ix_receipts_owner_dedup_status", table_name="receipts")
    op.drop_index("ix_receipts_owner_semantic_fp", table_name="receipts")
    op.drop_index("ix_receipts_owner_evidence_fp", table_name="receipts")

    op.drop_constraint("fk_receipt_canonical", "receipts", type_="foreignkey")
    op.drop_constraint("ck_receipt_canonical_not_self", "receipts", type_="check")
    op.drop_constraint("ck_receipt_deduplication_status", "receipts", type_="check")

    op.drop_column("receipts", "deduplication_checked_at")
    op.drop_column("receipts", "deduplication_rule_version")
    op.drop_column("receipts", "deduplication_method")
    op.drop_column("receipts", "semantic_fingerprint")
    op.drop_column("receipts", "evidence_fingerprint")
    op.drop_column("receipts", "canonical_receipt_id")
    op.drop_column("receipts", "deduplication_status")
