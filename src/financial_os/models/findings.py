"""ValidationFinding model — deterministic arithmetic check results."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from financial_os.models.base import Base


class ValidationFinding(Base):
    """Result of one deterministic validation rule against an immutable revision.

    check_code is a versioned, stable rule identifier (e.g. "TOTALS_ARITHMETIC_V1").
    observed and expected store non-secret numeric values for auditability.
    No receipt content (text, images, PII) may appear in observed or expected.
    """

    __tablename__ = "validation_findings"
    __table_args__ = (
        CheckConstraint(
            "outcome IN ('pass','warn','fail','not_applicable')",
            name="ck_finding_outcome",
        ),
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
    check_code: Mapped[str] = mapped_column(Text, nullable=False)
    outcome: Mapped[str] = mapped_column(Text, nullable=False)
    observed: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)
    expected: Mapped[dict[str, object] | None] = mapped_column(JSONB, nullable=True)
    rule_version: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<ValidationFinding check={self.check_code} outcome={self.outcome}>"
