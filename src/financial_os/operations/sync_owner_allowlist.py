"""Synchronize the single-owner allowlist into the authorization table.

The encrypted OWNER_ALLOWLIST secret is the source of truth. This command is
intended for a controlled, one-shot Cloud Run job and never logs subject IDs.
"""

from __future__ import annotations

import asyncio
import re
import uuid

from sqlalchemy import func, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from financial_os.config import Settings
from financial_os.database import build_engine, build_session_factory
from financial_os.models.auth import AuthSubject

_GOOGLE_SUBJECT = re.compile(r"google:[A-Za-z0-9_-]{1,128}\Z")


def parse_single_owner(raw_allowlist: str) -> tuple[str]:
    """Validate and return the one stable Firebase subject allowed in MVP."""
    subjects = tuple(
        dict.fromkeys(part.strip() for part in raw_allowlist.split(",") if part.strip())
    )
    if len(subjects) != 1:
        raise ValueError("Exactly one owner subject is required")
    if not _GOOGLE_SUBJECT.fullmatch(subjects[0]):
        raise ValueError("Owner subject has an unexpected format")
    return (subjects[0],)


async def sync_owner_subjects(session: AsyncSession, subjects: tuple[str]) -> None:
    """Upsert the approved owner and revoke any stale authorization rows."""
    for subject in subjects:
        statement = (
            insert(AuthSubject)
            .values(
                id=uuid.uuid4(),
                provider="google",
                provider_subject=subject,
                allowlisted=True,
            )
            .on_conflict_do_update(
                index_elements=[AuthSubject.provider_subject],
                set_={
                    "provider": "google",
                    "allowlisted": True,
                    "updated_at": func.now(),
                },
            )
        )
        await session.execute(statement)

    await session.execute(
        update(AuthSubject)
        .where(AuthSubject.provider_subject.not_in(subjects))
        .values(allowlisted=False, updated_at=func.now())
    )


async def sync_owner_allowlist() -> None:
    """Synchronize the secret-backed allowlist over a private IAM DB connection."""
    settings = Settings()
    subjects = parse_single_owner(settings.owner_allowlist)
    runtime = build_engine(settings)
    session_factory = build_session_factory(runtime.engine)
    try:
        async with session_factory() as session, session.begin():
            await sync_owner_subjects(session, subjects)
    finally:
        await runtime.close()


def main() -> None:
    asyncio.run(sync_owner_allowlist())
    print("Owner allowlist synchronization completed.")


if __name__ == "__main__":
    main()
