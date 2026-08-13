"""Pytest configuration and shared fixtures.

All test infrastructure uses in-memory fakes or local databases.
No real GCP credentials, bucket names, signed URLs, or Firebase tokens
appear in this file or any tests (OPS-02, AGENTS.md §7).

Integration tests require DATABASE_URL env var and are skipped when absent.
Unit tests have no external dependencies.
"""

from __future__ import annotations

import os

import pytest

from financial_os.adapters.extraction.fake import FakeExtractionAdapter
from financial_os.adapters.queue.fake import FakeQueueAdapter
from financial_os.adapters.storage.fake import FakeStorageAdapter
from financial_os.auth.firebase import VerifiedOwner
from financial_os.config import Settings

# ── Test settings ─────────────────────────────────────────────────────────────

TEST_SETTINGS = Settings(
    environment="test",
    firebase_project_id="",
    gcp_project_id="",
    gcs_evidence_bucket="",
    cloud_tasks_queue_path="",
    worker_oidc_audience="",  # disabled in test
    owner_allowlist="",
    session_version=1,
)

TEST_OWNER = VerifiedOwner(
    subject_id="google:test-subject-123",
    auth_subject_id="",
    auth_time=9999999999,  # far future
)


# ── Database fixtures (integration tests only) ────────────────────────────────


@pytest.fixture(scope="session")
def db_url() -> str:
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        pytest.skip("DATABASE_URL not set — skipping integration test")
    return url


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


# ── Fake adapter fixtures ──────────────────────────────────────────────────────


@pytest.fixture
def fake_storage() -> FakeStorageAdapter:
    return FakeStorageAdapter()


@pytest.fixture
def fake_queue() -> FakeQueueAdapter:
    return FakeQueueAdapter()


@pytest.fixture
def fake_extractor() -> FakeExtractionAdapter:
    return FakeExtractionAdapter()
