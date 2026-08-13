"""Async database engine and session factory.

Production uses Cloud SQL connector with IAM authentication (DB-01).
Local development uses a direct asyncpg connection via DATABASE_URL.

Services never call alembic upgrade head at startup (A-02).
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol, cast

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

if TYPE_CHECKING:
    from google.cloud.sql.connector import Connector

    from financial_os.config import Settings


class AsyncDatabaseConnection(Protocol):
    """Structural marker for connections returned by an async DB creator."""


@dataclass
class DatabaseRuntime:
    """Own the SQLAlchemy engine and optional Cloud SQL connector lifecycle."""

    engine: AsyncEngine
    connector: Connector | None = None

    async def close(self) -> None:
        await self.engine.dispose()
        if self.connector is not None:
            await self.connector.close_async()


def build_engine(settings: Settings) -> DatabaseRuntime:
    """Create the async SQLAlchemy engine from settings.

    When CLOUD_SQL_INSTANCE_CONNECTION_NAME is set, uses the Cloud SQL Python
    Connector for IAM-authenticated access (DB-01). Otherwise uses DATABASE_URL
    directly (local dev / CI).
    """
    if settings.use_cloud_sql:
        from google.cloud.sql.connector import Connector, IPTypes

        if not settings.database_iam_user:
            raise ValueError("DATABASE_IAM_USER is required when Cloud SQL is enabled")

        connector = Connector(refresh_strategy="LAZY")

        async def getconn() -> AsyncDatabaseConnection:
            connection = await connector.connect_async(
                settings.cloud_sql_instance_connection_name,
                "asyncpg",
                user=settings.database_iam_user,
                enable_iam_auth=True,
                db="financialos",
                ip_type=IPTypes.PRIVATE,
            )
            return cast(AsyncDatabaseConnection, connection)

        engine = create_async_engine(
            "postgresql+asyncpg://",
            async_creator=getconn,
            echo=settings.environment == "development",
            pool_size=5,
            max_overflow=10,
        )
        return DatabaseRuntime(engine=engine, connector=connector)
    else:
        engine = create_async_engine(
            settings.database_url,
            echo=settings.environment == "development",
            pool_size=5,
            max_overflow=10,
        )
        return DatabaseRuntime(engine=engine)


def build_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — yields an async DB session and rolls back on error."""
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
