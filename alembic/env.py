"""Alembic environment configuration.

Migrations run as a one-shot pre-deploy step (A-02).
Services must never call alembic upgrade head at startup.

Uses asyncio with asyncpg driver. The migration role has DDL rights;
the API/worker runtime roles have DML rights only (DB-01).
"""

from __future__ import annotations

import asyncio
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy.engine import Connection
from sqlalchemy.sql import text

from financial_os.config import get_settings
from financial_os.database import build_engine

# Import the declarative base so Alembic can see all models.
from financial_os.models import Base  # noqa: F401 — registers all models
from financial_os.models.auth import AuthSubject  # noqa: F401
from financial_os.models.events import StateEvent  # noqa: F401
from financial_os.models.extraction import (  # noqa: F401
    ExtractionRun,
    LineItemRevision,
    ReceiptRevision,
)
from financial_os.models.findings import ValidationFinding  # noqa: F401
from financial_os.models.receipt import ProcessingAttempt, Receipt, ReceiptAsset  # noqa: F401
from financial_os.operations.bootstrap_database_access import (
    build_migration_default_privileges_sql,
)

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_database_url() -> str:
    """Read DATABASE_URL from environment; fail loudly if missing."""
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        raise RuntimeError("DATABASE_URL environment variable is required for Alembic migrations.")
    # Migrations use asyncpg by default; accept both sync and async URL forms.
    if url.startswith("postgresql://") or url.startswith("postgres://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    return url


def do_run_migrations(connection: Connection) -> None:
    # The migration identity owns all objects it creates, so PostgreSQL requires
    # it—not the built-in administrator—to define future-object privileges.
    privilege_sql = build_migration_default_privileges_sql(
        api_role=os.environ.get("API_DATABASE_USER", ""),
        worker_role=os.environ.get("WORKER_DATABASE_USER", ""),
    )
    for statement in privilege_sql.split(";"):
        if statement.strip():
            connection.execute(text(statement))
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations using an async connection."""
    database = build_engine(get_settings())
    # The default-privilege statements start PostgreSQL's implicit transaction
    # before Alembic enters its context manager. Own the outer transaction here
    # so a successful migration is committed instead of rolled back on close.
    async with database.engine.begin() as conn:
        await conn.run_sync(do_run_migrations)
    await database.close()


def run_migrations_offline() -> None:
    """Run migrations without a database connection (generates SQL)."""
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
