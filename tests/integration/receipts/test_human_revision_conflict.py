"""Integration tests for human-revision stale-write protection and state validation.

Verifies:
- Wrong expected_parent_revision_id → 409 STALE_PARENT_REVISION (no DB write)
- Correct expected_parent_revision_id → 200, verification_status=human_verified
- Second request with the ORIGINAL parent after a successful correction → 409
- Exactly one human revision exists after a successful correction
- Receipt in non-correctable state (reserved) → 409 INVALID_RECEIPT_STATE

Requires DATABASE_URL env var pointing to a PostgreSQL instance.
All tests are skipped automatically when DATABASE_URL is not set.

Receipt state is seeded directly via SQLAlchemy to avoid a dependency on the
extraction pipeline path and to keep tests self-contained.

These tests require the create_human_revision service function to be implemented
by Agent A. Until then, they will fail gracefully with assertion errors
(500 returned instead of 409/200) and serve as specification tests.

Tests in TestStaleParentProtection run in definition order (pytest default for
class methods). test_correct_parent_succeeds must complete before
test_second_request_with_old_parent_returns_409 and
test_exactly_one_revision_after_correction, which observe the advanced DB state.
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

# ── Test identity and settings ────────────────────────────────────────────────

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
    subject_id="google:test-humanrev-conflict-owner",
    auth_subject_id="",
    auth_time=9999999999,
)


# ── Request body helpers ──────────────────────────────────────────────────────


def _valid_hr_body(parent_revision_id: uuid.UUID) -> dict:
    """Arithmetically valid correction: 999 + 100 = 1099 (PASS)."""
    return {
        "expected_parent_revision_id": str(parent_revision_id),
        "currency": "USD",
        "total_minor": 1099,
        "subtotal_minor": 999,
        "tax_minor": 100,
        "line_items": [],
    }


# ── Module-scoped fixtures ────────────────────────────────────────────────────


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
    async with AsyncClient(transport=ASGITransport(app=app_module), base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture(scope="module")
async def owner_db_id(session_factory) -> uuid.UUID:
    """Return the internal DB UUID for TEST_OWNER."""
    async with session_factory() as session:
        result = await session.execute(
            select(AuthSubject).where(AuthSubject.provider_subject == TEST_OWNER.subject_id)
        )
        subject = result.scalar_one()
        return subject.id


async def _insert_extracted_receipt(
    session_factory,
    owner_db_id: uuid.UUID,
) -> tuple[uuid.UUID, uuid.UUID]:
    """Directly insert a receipt in 'extracted' state with one extractor revision.

    Handles the circular FK between receipts and receipt_revisions using
    flush → flush → commit ordering.

    Returns (receipt_id, revision_id).
    """
    async with session_factory() as session:
        receipt = Receipt(
            id=uuid.uuid4(),
            owner_id=owner_db_id,
            client_submission_id=uuid.uuid4(),
            processing_status="extracted",
            verification_status="needs_review",
            expected_asset_count=1,
            current_revision_id=None,  # set after revision is flushed
            row_version=0,
        )
        session.add(receipt)
        await session.flush()  # receipt.id is now DB-assigned

        revision = ReceiptRevision(
            id=uuid.uuid4(),
            receipt_id=receipt.id,
            parent_revision_id=None,
            source_type="extractor",
            extraction_run_id=None,
            currency="USD",
            total_minor=1099,
        )
        session.add(revision)
        await session.flush()  # revision.id is now DB-assigned

        receipt.current_revision_id = revision.id
        await session.commit()

        return receipt.id, revision.id


@pytest_asyncio.fixture(scope="module")
async def sequential_extracted_receipt(
    session_factory,
    owner_db_id: uuid.UUID,
) -> tuple[uuid.UUID, uuid.UUID]:
    """One extracted receipt shared by the sequential stale-write tests.

    test_correct_parent_succeeds modifies this receipt's current_revision_id.
    Subsequent tests (test_second_request_with_old_parent_returns_409,
    test_exactly_one_revision_after_correction) then observe the advanced state.

    Returns (receipt_id, initial_revision_id) where initial_revision_id is the
    extractor revision ID present before any human correction is applied.
    """
    return await _insert_extracted_receipt(session_factory, owner_db_id)


# ── Test classes ──────────────────────────────────────────────────────────────


class TestStaleParentProtection:
    """Stale-write protection: only a matching expected_parent_revision_id succeeds.

    Tests run in definition order (pytest default for class methods within a
    module-scoped event loop). The order dependency is:

      test_stale_parent_returns_409            — isolated receipt, no state change
      test_correct_parent_succeeds             — modifies sequential_extracted_receipt
      test_second_request_with_old_parent_…   — observes the advanced state
      test_exactly_one_revision_after_…       — queries DB for the advanced state

    NOTE: All tests require create_human_revision to be implemented.
    """

    async def test_stale_parent_returns_409(
        self,
        client: AsyncClient,
        session_factory,
        owner_db_id: uuid.UUID,
    ) -> None:
        """Wrong expected_parent_revision_id → 409 STALE_PARENT_REVISION, no write."""
        # Use a fresh isolated receipt — this test must not mutate shared state
        receipt_id, _actual_revision_id = await _insert_extracted_receipt(
            session_factory, owner_db_id
        )
        wrong_parent_id = uuid.uuid4()  # deliberate mismatch

        resp = await client.post(
            f"/api/v1/receipts/{receipt_id}/human-revisions",
            json={
                "expected_parent_revision_id": str(wrong_parent_id),
                "currency": "USD",
                "total_minor": 1099,
                "subtotal_minor": 999,
                "tax_minor": 100,
                "line_items": [],
            },
        )

        assert resp.status_code == 409, (
            f"Stale parent: expected 409, got {resp.status_code}. "
            "Requires create_human_revision service function."
        )
        data = resp.json()
        assert data.get("error_code") == "STALE_PARENT_REVISION", (
            f"Expected STALE_PARENT_REVISION, got: {data.get('error_code')!r}"
        )
        # Error message must not expose receipt content (LOG-01)
        body_lower = resp.text.lower()
        assert "merchant" not in body_lower
        assert "subtotal" not in body_lower

    async def test_correct_parent_succeeds(
        self,
        client: AsyncClient,
        sequential_extracted_receipt: tuple[uuid.UUID, uuid.UUID],
    ) -> None:
        """Matching expected_parent_revision_id → 200, verification_status=human_verified.

        This test advances sequential_extracted_receipt's current_revision_id.
        Subsequent tests in this class observe the mutated DB state.
        """
        receipt_id, initial_revision_id = sequential_extracted_receipt

        resp = await client.post(
            f"/api/v1/receipts/{receipt_id}/human-revisions",
            json=_valid_hr_body(initial_revision_id),
        )

        assert resp.status_code == 200, (
            f"Correct parent: expected 200, got {resp.status_code}. "
            "Requires create_human_revision service function."
        )
        data = resp.json()
        assert data.get("verification_status") == "human_verified", (
            f"Expected human_verified, got: {data.get('verification_status')!r}"
        )
        # processing_status must remain unchanged (extracted, not advanced)
        assert data.get("processing_status") == "extracted", (
            f"processing_status must stay 'extracted', got: {data.get('processing_status')!r}"
        )

    async def test_second_request_with_old_parent_returns_409(
        self,
        client: AsyncClient,
        sequential_extracted_receipt: tuple[uuid.UUID, uuid.UUID],
    ) -> None:
        """After a successful correction, the ORIGINAL parent_revision_id is now stale.

        Depends on test_correct_parent_succeeds having run first. The receipt's
        current_revision_id has advanced to the new human revision, so the original
        extractor revision ID is no longer the current parent.
        """
        receipt_id, initial_revision_id = sequential_extracted_receipt

        resp = await client.post(
            f"/api/v1/receipts/{receipt_id}/human-revisions",
            json=_valid_hr_body(initial_revision_id),  # same ID as first attempt
        )

        assert resp.status_code == 409, (
            f"Second request with stale parent: expected 409, got {resp.status_code}"
        )
        data = resp.json()
        assert data.get("error_code") == "STALE_PARENT_REVISION", (
            f"Expected STALE_PARENT_REVISION, got: {data.get('error_code')!r}"
        )

    async def test_exactly_one_revision_after_correction(
        self,
        session_factory,
        sequential_extracted_receipt: tuple[uuid.UUID, uuid.UUID],
    ) -> None:
        """After one successful correction, exactly one human revision must exist in the DB.

        Depends on test_correct_parent_succeeds having run first.
        Concurrent-write safety: if SELECT FOR UPDATE is missing, two
        concurrent corrections could both succeed, creating two human revisions.
        This test is the DB-level assertion that only one was written.
        """
        receipt_id, _initial_revision_id = sequential_extracted_receipt

        async with session_factory() as session:
            result = await session.execute(
                select(ReceiptRevision).where(
                    ReceiptRevision.receipt_id == receipt_id,
                    ReceiptRevision.source_type == "human",
                )
            )
            human_revisions = list(result.scalars().all())

        assert len(human_revisions) == 1, (
            f"Expected exactly 1 human revision after correction, "
            f"found {len(human_revisions)}. "
            "If > 1, concurrent stale-write protection is broken."
        )


class TestInvalidReceiptState:
    """Receipts not in 'extracted' state cannot receive human corrections.

    The service must check processing_status == 'extracted' AFTER the ownership
    check but BEFORE any write. A receipt in 'reserved', 'queued', 'failed',
    or any other non-extracted state must return 409 INVALID_RECEIPT_STATE.

    NOTE: Requires create_human_revision to be implemented by Agent A.
    """

    async def test_reserved_receipt_returns_invalid_state(
        self,
        client: AsyncClient,
        session_factory,
        owner_db_id: uuid.UUID,
    ) -> None:
        """POST human-revisions on a reserved receipt → 409 INVALID_RECEIPT_STATE."""
        async with session_factory() as session:
            receipt = Receipt(
                id=uuid.uuid4(),
                owner_id=owner_db_id,
                client_submission_id=uuid.uuid4(),
                processing_status="reserved",
                verification_status="unreviewed",
                expected_asset_count=1,
                current_revision_id=None,
                row_version=0,
            )
            session.add(receipt)
            await session.commit()
            reserved_receipt_id = receipt.id

        resp = await client.post(
            f"/api/v1/receipts/{reserved_receipt_id}/human-revisions",
            json={
                "expected_parent_revision_id": str(uuid.uuid4()),
                "currency": "USD",
                "total_minor": 1099,
                "line_items": [],
            },
        )

        assert resp.status_code == 409, (
            f"Reserved receipt: expected 409 INVALID_RECEIPT_STATE, got {resp.status_code}. "
            "Requires create_human_revision service function."
        )
        data = resp.json()
        assert data.get("error_code") == "INVALID_RECEIPT_STATE", (
            f"Expected INVALID_RECEIPT_STATE, got: {data.get('error_code')!r}"
        )
        # Error message must not expose internal state detail or receipt content
        body_lower = resp.text.lower()
        assert "traceback" not in body_lower
        assert "stack" not in body_lower
        assert "merchant" not in body_lower
