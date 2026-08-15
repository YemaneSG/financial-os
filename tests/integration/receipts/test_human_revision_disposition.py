"""Integration tests for review_disposition in human revision creation (Sprint 2B).

Contract: POST /api/v1/receipts/{receipt_id}/human-revisions supports two dispositions:
  - "corrected" (default): all material arithmetic findings must pass
  - "confirmed_as_shown": snapshot must equal the current parent; failed arithmetic allowed;
    event reason_code = "human_confirmed_exception" (any fail) or "human_confirmed_as_shown"

These tests verify the implemented confirmed-as-shown service path and the
backward-compatible corrected-default behavior.

Requires DATABASE_URL env var pointing to a PostgreSQL instance.
Tests are skipped automatically when DATABASE_URL is not set.

All test data is entirely synthetic (OPS-02, AGENTS.md §7).
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
from financial_os.models.events import StateEvent
from financial_os.models.extraction import ReceiptRevision
from financial_os.models.findings import ValidationFinding
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
    subject_id="google:test-subject-disposition-2b",
    auth_subject_id="",
    auth_time=9999999999,
)


# ── Module-scoped DB and app fixtures ─────────────────────────────────────────


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
    app = create_test_app(
        settings=TEST_SETTINGS,
        storage=FakeStorageAdapter(),
        queue=FakeQueueAdapter(),
        extractor=FakeExtractionAdapter(),
        session_factory=session_factory,
    )
    app.dependency_overrides[get_verified_owner] = lambda: TEST_OWNER
    async with app.router.lifespan_context(app):
        yield app


@pytest_asyncio.fixture(loop_scope="module")
async def client(app_module):
    async with AsyncClient(transport=ASGITransport(app=app_module), base_url="http://test") as c:
        yield c


# ── Helpers ───────────────────────────────────────────────────────────────────


async def _lookup_owner_id(session_factory, subject_id: str) -> uuid.UUID:
    async with session_factory() as session:
        result = await session.execute(
            select(AuthSubject).where(AuthSubject.provider_subject == subject_id)
        )
        subject = result.scalar_one()
        return subject.id


async def _create_failing_extracted_receipt(
    session_factory,
    *,
    subtotal_minor: int = 1000,
    tax_minor: int = 80,
    total_minor: int = 1100,  # Arithmetic failure: 1000+80=1080 ≠ 1100
) -> tuple[uuid.UUID, uuid.UUID]:
    """Create an extracted receipt whose extractor revision has an arithmetic failure.

    Inserts a Receipt, a ReceiptRevision with inconsistent arithmetic, and a
    ValidationFinding row recording the failure. Synthetic data only.

    Returns (receipt_id, revision_id).
    """
    owner_id = await _lookup_owner_id(session_factory, TEST_OWNER.subject_id)

    async with session_factory() as session:
        receipt_id = uuid.uuid4()
        receipt = Receipt(
            id=receipt_id,
            owner_id=owner_id,
            client_submission_id=uuid.uuid4(),
            financial_context="personal",
            processing_status="extracted",
            verification_status="needs_review",
            current_revision_id=None,
            expected_asset_count=1,
        )
        session.add(receipt)
        await session.flush()

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
            subtotal_minor=subtotal_minor,
            tax_minor=tax_minor,
            tip_minor=None,
            discount_minor=None,
            total_minor=total_minor,
            payment_method_hint=None,
            overall_confidence=None,
        )
        session.add(revision)
        await session.flush()

        # Record the arithmetic failure on the extractor revision.
        computed = subtotal_minor + tax_minor
        delta = total_minor - computed
        finding = ValidationFinding(
            id=uuid.uuid4(),
            receipt_revision_id=revision_id,
            check_code="TOTALS_ARITHMETIC_V1",
            outcome="fail",
            observed={
                "total_minor": total_minor,
                "computed_minor": computed,
                "delta_minor": delta,
            },
            expected={"tolerance_minor": 1},
            rule_version="1",
        )
        session.add(finding)

        receipt.current_revision_id = revision_id
        session.add(receipt)
        await session.commit()

    return receipt_id, revision_id


def _confirmed_as_shown_body(
    parent_revision_id: uuid.UUID,
    *,
    subtotal_minor: int = 1000,
    tax_minor: int = 80,
    total_minor: int = 1100,
    currency: str = "USD",
    line_items: list | None = None,
) -> dict:
    """Build a confirmed_as_shown body that exactly mirrors the parent revision."""
    body: dict = {
        "expected_parent_revision_id": str(parent_revision_id),
        "currency": currency,
        "subtotal_minor": subtotal_minor,
        "tax_minor": tax_minor,
        "total_minor": total_minor,
        "review_disposition": "confirmed_as_shown",
        "line_items": line_items or [],
    }
    return body


# ── Tests ─────────────────────────────────────────────────────────────────────


class TestConfirmedAsShownDisposition:
    """Sprint 2B confirmed_as_shown flow integration tests."""

    async def test_confirmed_as_shown_with_failed_finding_retained(
        self, client: AsyncClient, session_factory
    ):
        """confirmed_as_shown with matching snapshot succeeds even with arithmetic failure.

        The new human revision retains the arithmetic finding as an acknowledged
        exception, and the state event uses reason_code "human_confirmed_exception".
        """
        receipt_id, revision_id = await _create_failing_extracted_receipt(session_factory)
        body = _confirmed_as_shown_body(revision_id)

        response = await client.post(f"/api/v1/receipts/{receipt_id}/human-revisions", json=body)

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["verification_status"] == "human_verified"
        assert data["processing_status"] == "extracted"
        assert data["current_revision"]["source_type"] == "human"

        # The new human revision must carry validation findings (including the failure).
        assert data.get("validation_findings") is not None
        human_findings = data["validation_findings"]
        totals_findings = [f for f in human_findings if f["check_code"] == "TOTALS_ARITHMETIC_V2"]
        assert len(totals_findings) >= 1, (
            "human revision should have a TOTALS_ARITHMETIC_V2 finding"
        )
        # At least one of those findings should be 'fail' (exception preserved)
        fail_findings = [f for f in totals_findings if f["outcome"] == "fail"]
        assert len(fail_findings) >= 1, (
            "confirmed_as_shown should preserve the arithmetic failure in findings"
        )

        # The state event reason_code must reflect the human exception.
        async with session_factory() as session:
            events_result = await session.execute(
                select(StateEvent)
                .where(StateEvent.receipt_id == receipt_id)
                .order_by(StateEvent.created_at.desc())
            )
            latest_event = events_result.scalars().first()

        assert latest_event is not None
        assert latest_event.reason_code in (
            "human_confirmed_exception",
            "human_confirmed_as_shown",
        ), f"Expected confirmed_as_shown event reason, got {latest_event.reason_code!r}"

    async def test_confirmed_as_shown_rejected_when_payload_differs(
        self, client: AsyncClient, session_factory
    ):
        """confirmed_as_shown is rejected when any field differs from the parent.

        Even though confirmed_as_shown allows failed arithmetic, the snapshot
        must semantically equal the parent. A changed total_minor → 4xx error.
        """
        receipt_id, revision_id = await _create_failing_extracted_receipt(session_factory)

        # Change total_minor by 100 cents — snapshot no longer equals parent
        body = _confirmed_as_shown_body(revision_id, total_minor=1200)  # parent has 1100

        response = await client.post(f"/api/v1/receipts/{receipt_id}/human-revisions", json=body)

        # Must be rejected — not 2xx
        assert response.status_code in (400, 422), (
            f"Expected 400 or 422 for differing snapshot, got {response.status_code}"
        )

        # Confirm no new revision was written
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

    async def test_corrected_default_still_rejects_failed_arithmetic(
        self, client: AsyncClient, session_factory
    ):
        """Regression: "corrected" disposition (default) still rejects inconsistent arithmetic.

        This test exercises the existing behavior and must pass independently of
        any Sprint 2B implementation.
        """
        receipt_id, revision_id = await _create_failing_extracted_receipt(session_factory)

        # Submit a body with mismatched arithmetic and NO review_disposition field
        # (defaults to "corrected")
        body = {
            "expected_parent_revision_id": str(revision_id),
            "currency": "USD",
            "subtotal_minor": 1000,
            "tax_minor": 80,
            "total_minor": 9999,  # 1000+80=1080 ≠ 9999 → arithmetic failure
            # review_disposition intentionally absent → defaults to "corrected"
        }

        response = await client.post(f"/api/v1/receipts/{receipt_id}/human-revisions", json=body)

        assert response.status_code == 422, response.text
        assert response.json()["error_code"] == "VALIDATION_ERROR"

        # No new revision written
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

    async def test_stale_write_protection_unchanged_for_confirmed_as_shown(
        self, client: AsyncClient, session_factory
    ):
        """Stale-parent protection fires before disposition logic.

        Sending confirmed_as_shown with a mismatched expected_parent_revision_id
        must return 409 STALE_PARENT_REVISION regardless of the disposition value.
        """
        receipt_id, _revision_id = await _create_failing_extracted_receipt(session_factory)

        # Use a random UUID as expected_parent — does not match current_revision_id
        wrong_parent_id = uuid.uuid4()
        body = _confirmed_as_shown_body(wrong_parent_id)

        response = await client.post(f"/api/v1/receipts/{receipt_id}/human-revisions", json=body)

        assert response.status_code == 409, response.text
        assert response.json()["error_code"] == "STALE_PARENT_REVISION"

    async def test_immutability_parent_revision_unchanged_after_confirmed_as_shown(
        self, client: AsyncClient, session_factory
    ):
        """After confirmed_as_shown success, the parent extractor revision is unchanged.

        The new human revision must reference the parent via parent_revision_id,
        and the original extractor revision must retain its original values.
        """
        receipt_id, revision_id = await _create_failing_extracted_receipt(
            session_factory,
            subtotal_minor=1000,
            tax_minor=80,
            total_minor=1100,
        )
        body = _confirmed_as_shown_body(revision_id)

        response = await client.post(f"/api/v1/receipts/{receipt_id}/human-revisions", json=body)

        assert response.status_code == 200, response.text
        data = response.json()
        new_revision_id = uuid.UUID(data["current_revision"]["revision_id"])

        async with session_factory() as session:
            # Verify the PARENT (extractor) revision is unchanged.
            parent_result = await session.execute(
                select(ReceiptRevision).where(ReceiptRevision.id == revision_id)
            )
            parent = parent_result.scalar_one()

            # Verify the CHILD (human) revision has correct lineage.
            child_result = await session.execute(
                select(ReceiptRevision).where(ReceiptRevision.id == new_revision_id)
            )
            child = child_result.scalar_one()

        # Parent must be untouched.
        assert parent.source_type == "extractor"
        assert parent.subtotal_minor == 1000
        assert parent.tax_minor == 80
        assert parent.total_minor == 1100

        # Child must have correct lineage.
        assert child.source_type == "human"
        assert child.parent_revision_id == revision_id
        assert child.receipt_id == receipt_id
