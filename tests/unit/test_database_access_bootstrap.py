import asyncio

import pytest

from financial_os.operations import bootstrap_database_access as bootstrap_module
from financial_os.operations.bootstrap_database_access import (
    bootstrap_database_access,
    build_access_sql,
    build_migration_default_privileges_sql,
)


def test_bootstrap_sql_grants_only_expected_runtime_rights() -> None:
    sql = build_access_sql(
        migrate_role="financial-os-dev-migrate@example.iam",
        api_role="financial-os-dev-api@example.iam",
        worker_role="financial-os-dev-worker@example.iam",
    )

    assert "GRANT USAGE, CREATE ON SCHEMA public" in sql
    assert "GRANT CONNECT ON DATABASE" in sql
    assert "GRANT USAGE, CREATE ON SCHEMA" in sql
    assert "SUPERUSER" not in sql
    assert "PASSWORD" not in sql


def test_migration_identity_configures_its_own_default_privileges() -> None:
    sql = build_migration_default_privileges_sql(
        api_role="financial-os-dev-api@example.iam",
        worker_role="financial-os-dev-worker@example.iam",
    )

    assert "ALTER DEFAULT PRIVILEGES IN SCHEMA public" in sql
    assert "GRANT SELECT, INSERT, UPDATE, DELETE" in sql
    assert "GRANT USAGE, SELECT ON SEQUENCES" in sql
    assert "FOR ROLE" not in sql


@pytest.mark.parametrize(
    "unsafe_role",
    ["role; DROP DATABASE financialos", 'role"name', "role name", ""],
)
def test_bootstrap_sql_rejects_unsafe_role_identifiers(unsafe_role: str) -> None:
    with pytest.raises(ValueError, match="unexpected format"):
        build_access_sql(
            migrate_role=unsafe_role,
            api_role="financial-os-dev-api@example.iam",
            worker_role="financial-os-dev-worker@example.iam",
        )


async def test_bootstrap_connector_uses_the_running_event_loop(monkeypatch) -> None:
    observed: dict[str, object] = {}

    class FakeConnection:
        async def execute(self, query: str) -> str:
            observed["query"] = query
            return "OK"

        async def close(self) -> None:
            observed["connection_closed"] = True

    class FakeConnector:
        def __init__(self, *, loop, refresh_strategy: str) -> None:
            observed["loop"] = loop
            observed["refresh_strategy"] = refresh_strategy

        async def connect_async(self, *args, **kwargs):
            observed["connect_args"] = args
            observed["connect_kwargs"] = kwargs
            return FakeConnection()

        async def close_async(self) -> None:
            observed["connector_closed"] = True

    monkeypatch.setattr(bootstrap_module, "Connector", FakeConnector)
    for key, value in {
        "CLOUD_SQL_INSTANCE_CONNECTION_NAME": "project:region:instance",
        "DB_ADMIN_PASSWORD": "not-a-real-password",
        "MIGRATE_DATABASE_USER": "financial-os-dev-migrate@example.iam",
        "API_DATABASE_USER": "financial-os-dev-api@example.iam",
        "WORKER_DATABASE_USER": "financial-os-dev-worker@example.iam",
    }.items():
        monkeypatch.setenv(key, value)

    await bootstrap_database_access()

    assert observed["loop"] is asyncio.get_running_loop()
    assert observed["refresh_strategy"] == "LAZY"
    assert observed["connection_closed"] is True
    assert observed["connector_closed"] is True
