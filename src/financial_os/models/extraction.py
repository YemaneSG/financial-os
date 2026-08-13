"""ExtractionRun, ReceiptRevision, and LineItemRevision models."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from financial_os.models.base import Base


class ExtractionRun(Base):
    """Record of one call to the ReceiptExtractor adapter.

    raw_response stores the original provider structured response after transport
    parsing. It is never used to update authoritative records directly; schema
    validation and deterministic checks gate promotion (VAL-001, AI-03).

    asset_manifest_hash uniquely identifies the exact evidence presented (A-03).
    """

    __tablename__ = "extraction_runs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('started','succeeded','invalid','failed')",
            name="ck_extraction_run_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    receipt_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("receipts.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    processing_attempt_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("processing_attempts.id", ondelete="RESTRICT"),
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(Text, nullable=False)
    model_id: Mapped[str] = mapped_column(Text, nullable=False)
    prompt_version: Mapped[str] = mapped_column(Text, nullable=False)
    schema_version: Mapped[str] = mapped_column(Text, nullable=False)
    asset_manifest_hash: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    raw_response: Mapped[dict[str, object] | None] = mapped_column(JSONB, nullable=True)
    provider_request_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="started")
    input_metadata: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return (
            f"<ExtractionRun receipt={self.receipt_id} model={self.model_id} status={self.status}>"
        )


class ReceiptRevision(Base):
    """Immutable structured interpretation of a receipt's evidence.

    Each extraction or human correction creates a new revision.
    current_revision_id on Receipt points to exactly one revision after extraction.

    Money fields use integer minor units (bigint). Never float.
    Quantities and unit prices on LineItemRevision use NUMERIC.
    """

    __tablename__ = "receipt_revisions"
    __table_args__ = (
        CheckConstraint(
            "source_type IN ('extractor','human','import')",
            name="ck_revision_source_type",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    receipt_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("receipts.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    parent_revision_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("receipt_revisions.id", use_alter=True, name="fk_revision_parent"),
        nullable=True,
    )
    source_type: Mapped[str] = mapped_column(Text, nullable=False)
    extraction_run_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("extraction_runs.id", use_alter=True, name="fk_revision_extraction_run"),
        nullable=True,
    )
    merchant_raw: Mapped[str | None] = mapped_column(Text, nullable=True)
    merchant_normalized: Mapped[str | None] = mapped_column(Text, nullable=True)
    purchase_datetime: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    purchase_timezone: Mapped[str | None] = mapped_column(Text, nullable=True)
    currency: Mapped[str] = mapped_column(Text, nullable=False)
    subtotal_minor: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    tax_minor: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    tip_minor: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    discount_minor: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    total_minor: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    payment_method_hint: Mapped[str | None] = mapped_column(Text, nullable=True)
    overall_confidence: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    line_items: Mapped[list[LineItemRevision]] = relationship(
        "LineItemRevision",
        back_populates="revision",
        order_by="LineItemRevision.ordinal",
    )

    def __repr__(self) -> str:
        return f"<ReceiptRevision receipt={self.receipt_id} source={self.source_type}>"


class LineItemRevision(Base):
    """One extracted line item within an immutable receipt revision.

    UNIQUE on (receipt_revision_id, ordinal) prevents duplicates (A-01).
    line_total_minor and discount_minor are integer minor units.
    quantity and unit_price_decimal use NUMERIC for exact decimal arithmetic.
    """

    __tablename__ = "line_item_revisions"
    __table_args__ = (
        UniqueConstraint(
            "receipt_revision_id",
            "ordinal",
            name="uq_line_item_revision_ordinal",
        ),
        CheckConstraint("ordinal >= 1", name="ck_line_item_ordinal"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    receipt_revision_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("receipt_revisions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    raw_description: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    quantity: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)
    unit: Mapped[str | None] = mapped_column(Text, nullable=True)
    unit_price_decimal: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)
    line_total_minor: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    discount_minor: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    category_suggestion: Mapped[str | None] = mapped_column(Text, nullable=True)
    field_confidence: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)

    revision: Mapped[ReceiptRevision] = relationship("ReceiptRevision", back_populates="line_items")

    def __repr__(self) -> str:
        return f"<LineItemRevision ordinal={self.ordinal} revision={self.receipt_revision_id}>"
