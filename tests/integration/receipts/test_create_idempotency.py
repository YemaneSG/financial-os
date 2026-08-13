"""Integration tests for receipt create idempotency (A-01).

Contract: two concurrent POST /api/v1/receipts with the same client_submission_key
must both return 2xx, and exactly one receipt row must exist.

Requires DATABASE_URL env var pointing to a PostgreSQL instance.
These tests are skipped automatically when DATABASE_URL is not set.
"""
from __future__ import annotations

import asyncio
import os
import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from financial_os.adapters.extraction.fake import FakeExtractionAdapter
from financial_os.adapters.queue.fake import FakeQueueAdapter
from financial_os.adapters.storage.fake import FakeStorageAdapter
from financial_os.app_factory import create_test_app
from financial_os.auth.deps import get_verified_owner
from financial_os.auth.firebase import VerifiedOwner
from financial_os.config import Settings
from financial_os.models import Base
from financial_os.models.auth import AuthSubject
from financial_os.models.receipt import Receipt
from tests.fixtures.factories import make_create_receipt_payload

pytestmark = [
    pytest.mark.integration,
    pytest.mark.asyncio(loop_scope="module"),
]


TEST_SETTINGS = Settings(
    environment="test",
    firebase_project_id="",
    gcp_project_id="",
    gcs_evidence_bucket="",
    cloud_tasks_queue_path="",
    worker_oidc_audience="",
    owner_allowlist="",
    pipeline_version="test-pipeline-v1",
)

TEST_OWNER = VerifiedOwner(
    subject_id="google:test-subject-idempotency",
    auth_subject_id="",
    auth_time=9999999999,
)


@pytest.fixture(scope="module")
def db_url_module() -> str:
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        pytest.skip("DATABASE_URL not set — skipping integration tests")
    return url


@pytest_asyncio.fixture(scope="module")
async def test_engine(db_url_module: str):
    engine = create_async_engine(db_url_module, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="module")
async def session_factory(test_engine):
    factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        session.add(
            AuthSubject(
                provider="google",
                provider_subject=TEST_OWNER.subject_id,
                allowlisted=True,
            )
        )
        await session.commit()
    return factory


@pytest_asyncio.fixture(scope="module")
async def app_module(session_factory):
    storage = FakeStorageAdapter()
    queue = FakeQueueAdapter()
    extractor = FakeExtractionAdapter()

    app = create_test_app(
        settings=TEST_SETTINGS,
        storage=storage,
        queue=queue,
        extractor=extractor,
        session_factory=session_factory,
    )
    app.dependency_overrides[get_verified_owner] = lambda: TEST_OWNER
    async with app.router.lifespan_context(app):
        yield app


@pytest_asyncio.fixture(loop_scope="module")
async def client(app_module):
    async with AsyncClient(
        transport=ASGITransport(app=app_module), base_url="http://test"
    ) as c:
        yield c


@pytest_asyncio.fixture(loop_scope="module")
async def clean_session(session_factory):
    """Session that rolls back after each test."""
    async with session_factory() as session:
        yield session
        await session.rollback()


class TestReceiptCreateIdempotency:
    async def test_single_create_returns_201(self, client: AsyncClient):
        payload = make_create_receipt_payload()
        response = await client.post("/api/v1/receipts", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert "receipt_id" in data
        assert data["processing_status"] == "reserved"
        assert len(data["upload_capabilities"]) == 1

    async def test_duplicate_key_returns_200(self, client: AsyncClient):
        """Two posts with the same key → first 201, second 200, same receipt_id."""
        key = uuid.uuid4()
        payload = make_create_receipt_payload(client_submission_key=key)

        r1 = await client.post("/api/v1/receipts", json=payload)
        r2 = await client.post("/api/v1/receipts", json=payload)

        assert r1.status_code == 201
        assert r2.status_code == 200
        assert r1.json()["receipt_id"] == r2.json()["receipt_id"]

    async def test_concurrent_duplicate_keys_both_2xx(self, client: AsyncClient):
        """Concurrent POSTs with the same key must both return 2xx (A-01)."""
        key = uuid.uuid4()
        payload = make_create_receipt_payload(client_submission_key=key)

        async def post() -> int:
            r = await client.post("/api/v1/receipts", json=payload)
            return r.status_code

        statuses = await asyncio.gather(post(), post())
        assert all(s in (200, 201) for s in statuses), f"Expected 2xx, got {statuses}"

    async def test_different_keys_create_different_receipts(self, client: AsyncClient):
        payload1 = make_create_receipt_payload()
        payload2 = make_create_receipt_payload()

        r1 = await client.post("/api/v1/receipts", json=payload1)
        r2 = await client.post("/api/v1/receipts", json=payload2)

        assert r1.status_code == 201
        assert r2.status_code == 201
        assert r1.json()["receipt_id"] != r2.json()["receipt_id"]

    async def test_upload_capabilities_returned_on_replay(self, client: AsyncClient):
        """Replay must return fresh upload capabilities."""
        key = uuid.uuid4()
        payload = make_create_receipt_payload(client_submission_key=key)

        r1 = await client.post("/api/v1/receipts", json=payload)
        r2 = await client.post("/api/v1/receipts", json=payload)

        caps1 = r1.json()["upload_capabilities"]
        caps2 = r2.json()["upload_capabilities"]
        assert len(caps1) == 1
        assert len(caps2) == 1
        assert caps1[0]["asset_id"] == caps2[0]["asset_id"]

    async def test_assets_count_must_match_expected(self, client: AsyncClient):
        """Mismatched expected_asset_count and assets length → 422."""
        payload = {
            "client_submission_key": str(uuid.uuid4()),
            "expected_asset_count": 2,
            "financial_context": "personal",
            "assets": [
                {"ordinal": 1, "declared_mime_type": "image/jpeg", "byte_size": 1000}
            ],
        }
        response = await client.post("/api/v1/receipts", json=payload)
        assert response.status_code == 422

    async def test_non_contiguous_ordinals_rejected(self, client: AsyncClient):
        """Ordinals must be contiguous starting from 1."""
        payload = {
            "client_submission_key": str(uuid.uuid4()),
            "expected_asset_count": 2,
            "financial_context": "personal",
            "assets": [
                {"ordinal": 1, "declared_mime_type": "image/jpeg", "byte_size": 1000},
                {"ordinal": 3, "declared_mime_type": "image/jpeg", "byte_size": 1000},
            ],
        }
        response = await client.post("/api/v1/receipts", json=payload)
        assert response.status_code == 422
