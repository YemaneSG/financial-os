"""Bootstrap PostgreSQL privileges for the passwordless runtime identities.

Run only as a one-shot private deployment job. The built-in administrator
password is delivered through Secret Manager and is never logged.
"""

from __future__ import annotations

import asyncio
import os
import re
from typing import Protocol, cast

from google.cloud.sql.connector import Connector, IPTypes

_SAFE_DATABASE_ROLE = re.compile(r"[A-Za-z0-9_.@-]{1,63}\Z")


class AsyncAdminConnection(Protocol):
    async def execute(self, query: str) -> str: ...

    async def close(self) -> None: ...


def _required_environment(name: str) -> str:
    value = os.environ.get(name, "")
    if not value:
        raise RuntimeError(f"{name} is required")
    return value


def _quote_role(role: str) -> str:
    """Validate and quote a Cloud SQL IAM PostgreSQL role identifier."""
    if not _SAFE_DATABASE_ROLE.fullmatch(role):
        raise ValueError("Database role has an unexpected format")
    return f'"{role}"'


def build_access_sql(*, migrate_role: str, api_role: str, worker_role: str) -> str:
    """Return the idempotent privilege bootstrap transaction."""
    migrate = _quote_role(migrate_role)
    api = _quote_role(api_role)
    worker = _quote_role(worker_role)

    return f"""
BEGIN;

GRANT CONNECT ON DATABASE financialos TO {migrate}, {api}, {worker};
GRANT USAGE, CREATE ON SCHEMA public TO {migrate};
GRANT USAGE ON SCHEMA public TO {api}, {worker};

ALTER ROLE {migrate} IN DATABASE financialos SET search_path = public, pg_catalog;
ALTER ROLE {api} IN DATABASE financialos SET search_path = public, pg_catalog;
ALTER ROLE {worker} IN DATABASE financialos SET search_path = public, pg_catalog;

COMMIT;
"""


def build_migration_default_privileges_sql(*, api_role: str, worker_role: str) -> str:
    """Return grants executed by the migration identity for its own objects."""
    api = _quote_role(api_role)
    worker = _quote_role(worker_role)
    return f"""
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO {api}, {worker};
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT USAGE, SELECT ON SEQUENCES TO {api}, {worker};
"""


async def bootstrap_database_access() -> None:
    """Connect privately as the built-in admin and grant runtime privileges."""
    connector = Connector(
        loop=asyncio.get_running_loop(),
        refresh_strategy="LAZY",
    )
    connection: AsyncAdminConnection | None = None
    try:
        raw_connection = await connector.connect_async(
            _required_environment("CLOUD_SQL_INSTANCE_CONNECTION_NAME"),
            "asyncpg",
            user="postgres",
            password=_required_environment("DB_ADMIN_PASSWORD"),
            enable_iam_auth=False,
            db="financialos",
            ip_type=IPTypes.PRIVATE,
        )
        connection = cast(AsyncAdminConnection, raw_connection)
        sql = build_access_sql(
            migrate_role=_required_environment("MIGRATE_DATABASE_USER"),
            api_role=_required_environment("API_DATABASE_USER"),
            worker_role=_required_environment("WORKER_DATABASE_USER"),
        )
        await connection.execute(sql)
    finally:
        if connection is not None:
            await connection.close()
        await connector.close_async()


def main() -> None:
    asyncio.run(bootstrap_database_access())
    print("Database access bootstrap completed.")


if __name__ == "__main__":
    main()
