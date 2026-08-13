"""StateEvent model — append-only audit of processing and verification changes."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from financial_os.models.base import Base


class StateEvent(Base):
    """Append-only audit record for processing and verification state transitions.

    No state event is ever deleted. dimension identifies which axis changed.
    reason_code and correlation_id are privacy-safe operational references.
    No receipt content, signed URLs, or PII may appear in any field here.
    """

    __tablename__ = "state_events"
    __table_args__ = (
        CheckConstraint(
            "dimension IN ('processing','verification','financial_context')",
            name="ck_event_dimension",
        ),
        CheckConstraint(
            "actor_type IN ('user','api','worker','scheduler','import')",
            name="ck_event_actor_type",
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
    dimension: Mapped[str] = mapped_column(Text, nullable=False)
    from_state: Mapped[str | None] = mapped_column(Text, nullable=True)
    to_state: Mapped[str] = mapped_column(Text, nullable=False)
    actor_type: Mapped[str] = mapped_column(Text, nullable=False)
    reason_code: Mapped[str] = mapped_column(Text, nullable=False)
    correlation_id: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"<StateEvent receipt={self.receipt_id} "
            f"{self.dimension} {self.from_state}→{self.to_state}>"
        )
