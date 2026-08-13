"""
Security test configuration.

These tests run against a deployed environment (staging or production-equivalent).
They require:
  - HOSTING_URL: Firebase Hosting base URL
  - API_URL: Cloud Run API base URL
  - VALID_OWNER_TOKEN: Firebase JWT for the allowlisted owner (from test identity)
  - NON_OWNER_TOKEN: Firebase JWT for a valid but non-allowlisted identity

All tokens must come from test/synthetic identities — never real owner credentials.
Real tokens must never enter CI artifacts, logs, or test output (LOG-01, OPS-02).
"""

import os

import httpx
import pytest


def _require_env(name: str) -> str:
    value = os.environ.get(name, "")
    if not value:
        pytest.skip(f"Environment variable {name!r} not set — skipping deployed tests.")
    return value


@pytest.fixture(scope="session")
def hosting_url() -> str:
    return _require_env("HOSTING_URL").rstrip("/")


@pytest.fixture(scope="session")
def api_url() -> str:
    return _require_env("API_URL").rstrip("/")


@pytest.fixture(scope="session")
def valid_owner_token() -> str:
    """Firebase JWT for the allowlisted test owner identity."""
    return _require_env("VALID_OWNER_TOKEN")


@pytest.fixture(scope="session")
def non_owner_token() -> str:
    """Firebase JWT for a valid but non-allowlisted identity."""
    return _require_env("NON_OWNER_TOKEN")


@pytest.fixture(scope="session")
def api_client(api_url: str, valid_owner_token: str) -> httpx.Client:
    return httpx.Client(
        base_url=api_url,
        headers={"Authorization": f"Bearer {valid_owner_token}"},
        timeout=30,
    )
