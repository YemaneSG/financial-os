"""Receipt, ReceiptAsset, and ProcessingAttempt models."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from financial_os.models.base import Base


class Receipt(Base):
    """Core receipt aggregate.

    processing_status and verification_status advance independently.
    row_version provides optimistic concurrency for the worker lease.
    Unique on (owner_id, client_submission_id) enforces idempotent creation.
    """

    __tablename__ = "receipts"
    __table_args__ = (
        UniqueConstraint("owner_id", "client_submission_id", name="uq_receipt_owner_submission"),
        CheckConstraint(
            "processing_status IN ("
            "'reserved','uploading','uploaded','queued','processing',"
            "'extracted','retryable_failed','failed','abandoned')",
            name="ck_receipt_processing_status",
        ),
        CheckConstraint(
            "verification_status IN ("
            "'unreviewed','system_validated','needs_review','human_verified')",
            name="ck_receipt_verification_status",
        ),
        CheckConstraint(
            "financial_context IN ('personal','rental_property')",
            name="ck_receipt_financial_context",
        ),
        CheckConstraint("expected_asset_count > 0", name="ck_receipt_expected_asset_count"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    client_submission_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    financial_context: Mapped[str] = mapped_column(Text, nullable=False, default="personal")
    processing_status: Mapped[str] = mapped_column(Text, nullable=False, default="reserved")
    verification_status: Mapped[str] = mapped_column(Text, nullable=False, default="unreviewed")
    current_revision_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("receipt_revisions.id", use_alter=True, name="fk_receipt_current_revision"),
        nullable=True,
    )
    expected_asset_count: Mapped[int] = mapped_column(Integer, nullable=False)
    captured_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    row_version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    assets: Mapped[list[ReceiptAsset]] = relationship(
        "ReceiptAsset", back_populates="receipt", order_by="ReceiptAsset.ordinal"
    )
    processing_attempts: Mapped[list[ProcessingAttempt]] = relationship(
        "ProcessingAttempt", back_populates="receipt"
    )

    def __repr__(self) -> str:
        return f"<Receipt id={self.id} status={self.processing_status}>"


class ReceiptAsset(Base):
    """Individual image within a receipt.

    storage_generation pins the exact GCS object version after finalization (S-01).
    sha256 is computed from downloaded bytes during finalization/worker processing.
    upload_status transitions: reserved → uploaded → verified | rejected.
    """

    __tablename__ = "receipt_assets"
    __table_args__ = (
        UniqueConstraint("receipt_id", "ordinal", name="uq_asset_receipt_ordinal"),
        CheckConstraint("ordinal >= 1", name="ck_asset_ordinal"),
        CheckConstraint(
            "upload_status IN ('reserved','uploaded','verified','rejected')",
            name="ck_asset_upload_status",
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
    ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    object_key: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    storage_generation: Mapped[str | None] = mapped_column(Text, nullable=True)
    declared_mime_type: Mapped[str] = mapped_column(Text, nullable=False)
    verified_mime_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    byte_size: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    upload_status: Mapped[str] = mapped_column(Text, nullable=False, default="reserved")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    receipt: Mapped[Receipt] = relationship("Receipt", back_populates="assets")

    def __repr__(self) -> str:
        return f"<ReceiptAsset ordinal={self.ordinal} status={self.upload_status}>"


class ProcessingAttempt(Base):
    """One extraction attempt for a receipt.

    UNIQUE on (receipt_id, pipeline_version, attempt_number) ensures idempotent
    duplicate task delivery cannot create duplicate attempt rows (A-01).
    """

    __tablename__ = "processing_attempts"
    __table_args__ = (
        UniqueConstraint(
            "receipt_id",
            "pipeline_version",
            "attempt_number",
            name="uq_attempt_receipt_pipeline_attempt",
        ),
        CheckConstraint(
            "status IN ('queued','running','retryable_failed','terminal_failed','succeeded')",
            name="ck_attempt_status",
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
    pipeline_version: Mapped[str] = mapped_column(Text, nullable=False)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    queue_task_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="queued")
    safe_error_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    receipt: Mapped[Receipt] = relationship("Receipt", back_populates="processing_attempts")

    def __repr__(self) -> str:
        return (
            f"<ProcessingAttempt receipt={self.receipt_id} "
            f"attempt={self.attempt_number} status={self.status}>"
        )
