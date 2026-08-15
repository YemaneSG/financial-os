"""Integration tests for human revision creation (Sprint 2A).

Contract: POST /api/v1/receipts/{receipt_id}/human-revisions on an extracted receipt
creates an immutable human revision and transitions to human_verified.

Requires DATABASE_URL env var pointing to a PostgreSQL instance.
Tests are skipped automatically when DATABASE_URL is not set.
"""

from __future__ import annotations

import os
import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
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
from financial_os.models.extraction import ReceiptRevision
from financial_os.models.receipt import Receipt

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
    subject_id="google:test-subject-human-revision",
    auth_subject_id="",
    auth_time=9999999999,
)

TEST_OWNER_2 = VerifiedOwner(
    subject_id="google:test-subject-human-revision-2",
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
        session.add(
            AuthSubject(
                provider="google",
                provider_subject=TEST_OWNER_2.subject_id,
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
    async with AsyncClient(transport=ASGITransport(app=app_module), base_url="http://test") as c:
        yield c


# ── helpers ───────────────────────────────────────────────────────────────────


async def _lookup_owner_id(session_factory, subject_id: str) -> uuid.UUID:
    """Resolve provider_subject to internal owner UUID."""
    async with session_factory() as session:
        result = await session.execute(
            select(AuthSubject).where(AuthSubject.provider_subject == subject_id)
        )
        subject = result.scalar_one()
        return subject.id


async def _create_extracted_receipt(
    session_factory,
    owner_subject_id: str = TEST_OWNER.subject_id,
    *,
    processing_status: str = "extracted",
    verification_status: str = "needs_review",
) -> tuple[uuid.UUID, uuid.UUID | None]:
    """Insert a synthetic receipt and (when extracted) an extractor revision directly.

    Returns (receipt_id, revision_id). revision_id is None when processing_status
    is not 'extracted'. Synthetic data only — no real receipt content.
    """
    owner_id = await _lookup_owner_id(session_factory, owner_subject_id)

    async with session_factory() as session:
        receipt_id = uuid.uuid4()
        receipt = Receipt(
            id=receipt_id,
            owner_id=owner_id,
            client_submission_id=uuid.uuid4(),
            financial_context="personal",
            processing_status=processing_status,
            verification_status=verification_status,
            current_revision_id=None,
            expected_asset_count=1,
        )
        session.add(receipt)
        await session.flush()

        revision_id: uuid.UUID | None = None

        if processing_status == "extracted":
            revision_id = uuid.uuid4()
            revision = ReceiptRevision(
                id=revision_id,
                receipt_id=receipt_id,
                parent_revision_id=None,
                source_type="extractor",
                extraction_run_id=None,
                merchant_raw=None,
                merchant_normalized=None,
                purchase_datetime=None,
                purchase_timezone=None,
                currency="USD",
                subtotal_minor=500,
                tax_minor=None,
                tip_minor=None,
                discount_minor=None,
                total_minor=500,
                payment_method_hint=None,
                overall_confidence=None,
            )
            session.add(revision)
            await session.flush()

            receipt.current_revision_id = revision_id
            session.add(receipt)

        await session.commit()

    return receipt_id, revision_id


def _make_human_revision_body(
    expected_parent_revision_id: uuid.UUID,
    *,
    currency: str = "USD",
    total_minor: int = 500,
    subtotal_minor: int | None = None,
    tax_minor: int | None = None,
    line_items: list | None = None,
) -> dict:
    body: dict = {
        "expected_parent_revision_id": str(expected_parent_revision_id),
        "currency": currency,
        "total_minor": total_minor,
    }
    if subtotal_minor is not None:
        body["subtotal_minor"] = subtotal_minor
    if tax_minor is not None:
        body["tax_minor"] = tax_minor
    if line_items is not None:
        body["line_items"] = line_items
    return body


# ── test class ────────────────────────────────────────────────────────────────


class TestHumanRevision:
    async def test_human_revision_success_needs_review(self, client: AsyncClient, session_factory):
        """POST human-revision on a needs_review extracted receipt → 200, human_verified."""
        receipt_id, revision_id = await _create_extracted_receipt(
            session_factory, verification_status="needs_review"
        )
        assert revision_id is not None

        body = _make_human_revision_body(revision_id)
        response = await client.post(f"/api/v1/receipts/{receipt_id}/human-revisions", json=body)

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["verification_status"] == "human_verified"
        assert data["processing_status"] == "extracted"
        assert data["current_revision"]["source_type"] == "human"

    async def test_human_revision_success_system_validated(
        self, client: AsyncClient, session_factory
    ):
        """POST human-revision on a system_validated extracted receipt → 200, human_verified."""
        receipt_id, revision_id = await _create_extracted_receipt(
            session_factory, verification_status="system_validated"
        )
        assert revision_id is not None

        body = _make_human_revision_body(revision_id)
        response = await client.post(f"/api/v1/receipts/{receipt_id}/human-revisions", json=body)

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["verification_status"] == "human_verified"
        assert data["current_revision"]["source_type"] == "human"

    async def test_human_revision_stale_parent_returns_409(
        self, client: AsyncClient, session_factory
    ):
        """Sending wrong expected_parent_revision_id → 409 STALE_PARENT_REVISION."""
        receipt_id, _revision_id = await _create_extracted_receipt(session_factory)

        wrong_parent_id = uuid.uuid4()  # does not match current_revision_id
        body = _make_human_revision_body(wrong_parent_id)
        response = await client.post(f"/api/v1/receipts/{receipt_id}/human-revisions", json=body)

        assert response.status_code == 409, response.text
        assert response.json()["error_code"] == "STALE_PARENT_REVISION"

    async def test_human_revision_replay_returns_409(self, client: AsyncClient, session_factory):
        """First request succeeds; second with same parent_id → 409 STALE_PARENT_REVISION."""
        receipt_id, revision_id = await _create_extracted_receipt(session_factory)
        assert revision_id is not None

        body = _make_human_revision_body(revision_id)

        r1 = await client.post(f"/api/v1/receipts/{receipt_id}/human-revisions", json=body)
        assert r1.status_code == 200, r1.text

        r2 = await client.post(f"/api/v1/receipts/{receipt_id}/human-revisions", json=body)
        assert r2.status_code == 409, r2.text
        assert r2.json()["error_code"] == "STALE_PARENT_REVISION"

    async def test_human_revision_invalid_state_reserved_returns_409(
        self, client: AsyncClient, session_factory
    ):
        """POST on a reserved receipt → 409 INVALID_RECEIPT_STATE."""
        receipt_id, _ = await _create_extracted_receipt(
            session_factory,
            processing_status="reserved",
            verification_status="unreviewed",
        )

        # State check fires before stale-parent check so any UUID works here.
        body = _make_human_revision_body(uuid.uuid4())
        response = await client.post(f"/api/v1/receipts/{receipt_id}/human-revisions", json=body)

        assert response.status_code == 409, response.text
        assert response.json()["error_code"] == "INVALID_RECEIPT_STATE"

    async def test_human_revision_invalid_verification_transition_returns_409(
        self, client: AsyncClient, session_factory
    ):
        receipt_id, revision_id = await _create_extracted_receipt(
            session_factory,
            processing_status="extracted",
            verification_status="unreviewed",
        )
        assert revision_id is not None

        response = await client.post(
            f"/api/v1/receipts/{receipt_id}/human-revisions",
            json=_make_human_revision_body(revision_id),
        )

        assert response.status_code == 409, response.text
        assert response.json()["error_code"] == "INVALID_RECEIPT_STATE"

    async def test_human_revision_currency_must_match_parent(
        self, client: AsyncClient, session_factory
    ):
        receipt_id, revision_id = await _create_extracted_receipt(session_factory)
        assert revision_id is not None

        response = await client.post(
            f"/api/v1/receipts/{receipt_id}/human-revisions",
            json=_make_human_revision_body(revision_id, currency="EUR"),
        )

        assert response.status_code == 422, response.text
        assert response.json()["error_code"] == "VALIDATION_ERROR"

    async def test_human_revision_extractor_revision_unchanged(
        self, client: AsyncClient, session_factory
    ):
        """After a human revision the original extractor revision row is unchanged."""
        receipt_id, original_revision_id = await _create_extracted_receipt(session_factory)
        assert original_revision_id is not None

        body = _make_human_revision_body(original_revision_id)
        response = await client.post(f"/api/v1/receipts/{receipt_id}/human-revisions", json=body)
        assert response.status_code == 200, response.text

        # Load the original revision directly from the DB and verify it is unchanged.
        async with session_factory() as session:
            result = await session.execute(
                select(ReceiptRevision).where(ReceiptRevision.id == original_revision_id)
            )
            original = result.scalar_one()

        assert original.source_type == "extractor"
        assert original.currency == "USD"
        assert original.total_minor == 500

    async def test_human_revision_creates_exactly_one_revision(
        self, client: AsyncClient, session_factory
    ):
        """After correction exactly one new revision (human type) is added to the receipt."""
        receipt_id, revision_id = await _create_extracted_receipt(session_factory)
        assert revision_id is not None

        async with session_factory() as session:
            pre_revisions = (
                (
                    await session.execute(
                        select(ReceiptRevision).where(ReceiptRevision.receipt_id == receipt_id)
                    )
                )
                .scalars()
                .all()
            )

        body = _make_human_revision_body(revision_id)
        response = await client.post(f"/api/v1/receipts/{receipt_id}/human-revisions", json=body)
        assert response.status_code == 200, response.text

        async with session_factory() as session:
            post_revisions = (
                (
                    await session.execute(
                        select(ReceiptRevision).where(ReceiptRevision.receipt_id == receipt_id)
                    )
                )
                .scalars()
                .all()
            )

        assert len(post_revisions) == len(pre_revisions) + 1
        source_types = {r.source_type for r in post_revisions}
        assert "human" in source_types
        assert "extractor" in source_types

    async def test_human_revision_wrong_owner_returns_404(
        self, client: AsyncClient, app_module, session_factory
    ):
        """Accessing a receipt owned by TEST_OWNER using TEST_OWNER_2 identity → 404."""
        receipt_id, revision_id = await _create_extracted_receipt(
            session_factory, TEST_OWNER.subject_id
        )
        assert revision_id is not None

        # Temporarily authenticate as the second (non-owner) identity.
        original_override = app_module.dependency_overrides[get_verified_owner]
        app_module.dependency_overrides[get_verified_owner] = lambda: TEST_OWNER_2
        try:
            body = _make_human_revision_body(revision_id)
            response = await client.post(
                f"/api/v1/receipts/{receipt_id}/human-revisions", json=body
            )
            assert response.status_code == 404, response.text
        finally:
            app_module.dependency_overrides[get_verified_owner] = original_override

    async def test_human_revision_arithmetic_fail_returns_422(
        self, client: AsyncClient, session_factory
    ):
        """Inconsistent totals → 422 VALIDATION_ERROR; no new revision row is written."""
        receipt_id, revision_id = await _create_extracted_receipt(session_factory)
        assert revision_id is not None

        # subtotal=1000 + tax=80 = 1080, but total=9999: arithmetic fails.
        body = {
            "expected_parent_revision_id": str(revision_id),
            "currency": "USD",
            "subtotal_minor": 1000,
            "tax_minor": 80,
            "total_minor": 9999,
        }
        response = await client.post(f"/api/v1/receipts/{receipt_id}/human-revisions", json=body)

        assert response.status_code == 422, response.text
        assert response.json()["error_code"] == "VALIDATION_ERROR"

        # Confirm no new revision was persisted.
        async with session_factory() as session:
            revisions = (
                (
                    await session.execute(
                        select(ReceiptRevision).where(ReceiptRevision.receipt_id == receipt_id)
                    )
                )
                .scalars()
                .all()
            )

        assert len(revisions) == 1
        assert revisions[0].source_type == "extractor"
