"""Auth subjects — allowlisted owner identities."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from financial_os.models.base import Base


class AuthSubject(Base):
    """Single-owner identity, stored by stable provider subject ID.

    Authorization binds to provider_subject (stable UID), not display email.
    valid_after enables session-version invalidation (IAM-02).
    """

    __tablename__ = "auth_subjects"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    provider: Mapped[str] = mapped_column(String, nullable=False)
    provider_subject: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    allowlisted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    valid_after: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<AuthSubject provider={self.provider} allowlisted={self.allowlisted}>"
