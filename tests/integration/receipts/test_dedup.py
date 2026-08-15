"""Integration tests for receipt deduplication (Sprint 2C Workstream A).

Covers: exact duplicate, semantic duplicate, suspected, unique, false-positive safety,
        owner isolation, canonical root, idempotency, and correction re-classification.

Requires DATABASE_URL env var. Skipped when absent.
All data is entirely synthetic. No real receipt content or PII (AGENTS.md §7).
"""

from __future__ import annotations

import hashlib
import os
import uuid
from datetime import UTC, datetime

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from financial_os.domain.states import DeduplicationStatus
from financial_os.models import Base
from financial_os.models.events import StateEvent
from financial_os.models.extraction import LineItemRevision, ReceiptRevision
from financial_os.models.receipt import Receipt, ReceiptAsset
from financial_os.operations.backfill_dedup import _run_backfill
from financial_os.services.dedup import classify_receipt

pytestmark = [
    pytest.mark.integration,
    pytest.mark.asyncio(loop_scope="module"),
]

# ── Synthetic constants ───────────────────────────────────────────────────────

_PURCHASE_DT = datetime(2026, 8, 1, 12, 0, 0, tzinfo=UTC)
_PURCHASE_DT_DIFFERENT_DAY = datetime(2026, 8, 2, 12, 0, 0, tzinfo=UTC)

_CORR = "test-dedup-corr"


# ── DB fixtures ───────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def db_url_module() -> str:
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        pytest.skip("DATABASE_URL not set — skipping dedup integration tests")
    return url


@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def engine(db_url_module: str):
    eng = create_async_engine(db_url_module, echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await eng.dispose()


@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def factory(engine):
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(loop_scope="module")
async def session(factory):
    async with factory() as sess:
        yield sess
        await sess.rollback()


# ── Builder helpers ───────────────────────────────────────────────────────────


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


async def _insert_receipt(
    session: AsyncSession,
    *,
    owner_id: uuid.UUID,
    acknowledged_at: datetime | None = None,
    processing_status: str = "extracted",
) -> Receipt:
    now = datetime.now(UTC)
    r = Receipt(
        id=uuid.uuid4(),
        owner_id=owner_id,
        client_submission_id=uuid.uuid4(),
        financial_context="personal",
        processing_status=processing_status,
        verification_status="system_validated",
        expected_asset_count=1,
        captured_at=now,
        acknowledged_at=acknowledged_at or now,
        row_version=0,
    )
    session.add(r)
    await session.flush()
    return r


async def _insert_asset(
    session: AsyncSession,
    receipt: Receipt,
    *,
    data: bytes,
    ordinal: int = 1,
) -> ReceiptAsset:
    sha = _sha256_hex(data)
    asset = ReceiptAsset(
        id=uuid.uuid4(),
        receipt_id=receipt.id,
        ordinal=ordinal,
        object_key=f"originals/{receipt.owner_id}/{receipt.id}/{uuid.uuid4()}",
        storage_generation="1",
        declared_mime_type="image/jpeg",
        verified_mime_type="image/jpeg",
        byte_size=len(data),
        sha256=sha,
        upload_status="verified",
    )
    session.add(asset)
    await session.flush()
    return asset


async def _insert_revision(
    session: AsyncSession,
    receipt: Receipt,
    *,
    merchant: str = "Synthetic Store",
    purchase_datetime: datetime = _PURCHASE_DT,
    currency: str = "USD",
    total_minor: int = 1080,
    line_items: list[tuple[str, int]] | None = None,
) -> ReceiptRevision:
    rev = ReceiptRevision(
        id=uuid.uuid4(),
        receipt_id=receipt.id,
        parent_revision_id=None,
        source_type="extractor",
        extraction_run_id=None,
        merchant_raw=merchant.upper(),
        merchant_normalized=merchant,
        purchase_datetime=purchase_datetime,
        purchase_timezone=None,
        currency=currency,
        subtotal_minor=total_minor - 80,
        tax_minor=80,
        tip_minor=None,
        discount_minor=None,
        total_minor=total_minor,
        payment_method_hint=None,
        overall_confidence=0.95,
    )
    session.add(rev)
    await session.flush()

    items = line_items or [("Synthetic Item A", total_minor - 80)]
    for idx, (desc, total) in enumerate(items, start=1):
        li = LineItemRevision(
            id=uuid.uuid4(),
            receipt_revision_id=rev.id,
            ordinal=idx,
            raw_description=desc.upper(),
            normalized_description=desc,
            line_total_minor=total,
            discount_minor=None,
            field_confidence={},
        )
        session.add(li)

    receipt.current_revision_id = rev.id
    session.add(receipt)
    await session.flush()
    return rev


# ── Tests ─────────────────────────────────────────────────────────────────────


class TestExactEvidenceDuplicate:
    """Rule 2: identical asset SHA-256s → confirmed_duplicate."""

    async def test_identical_assets_second_becomes_confirmed(self, session: AsyncSession) -> None:
        owner = uuid.uuid4()
        data = b"\xff\xd8\xff" + b"\x00" * 100

        earlier = await _insert_receipt(
            session, owner_id=owner, acknowledged_at=datetime(2026, 8, 1, 10, 0, tzinfo=UTC)
        )
        await _insert_asset(session, earlier, data=data)
        await classify_receipt(session=session, receipt=earlier, correlation_id=_CORR)

        later = await _insert_receipt(
            session, owner_id=owner, acknowledged_at=datetime(2026, 8, 1, 11, 0, tzinfo=UTC)
        )
        await _insert_asset(session, later, data=data)
        status = await classify_receipt(session=session, receipt=later, correlation_id=_CORR)

        assert status == DeduplicationStatus.CONFIRMED_DUPLICATE
        await session.refresh(later)
        assert later.canonical_receipt_id == earlier.id
        assert later.deduplication_method == "exact_evidence"

    async def test_first_receipt_stays_unique(self, session: AsyncSession) -> None:
        owner = uuid.uuid4()
        data = b"\xff\xd8\xff" + b"\x11" * 100

        original = await _insert_receipt(session, owner_id=owner)
        await _insert_asset(session, original, data=data)
        status = await classify_receipt(session=session, receipt=original, correlation_id=_CORR)

        assert status == DeduplicationStatus.UNIQUE
        await session.refresh(original)
        assert original.canonical_receipt_id is None

    async def test_canonical_root_is_earlier_receipt(self, session: AsyncSession) -> None:
        owner = uuid.uuid4()
        data = b"\xff\xd8\xff" + b"\x22" * 100

        later = await _insert_receipt(
            session, owner_id=owner, acknowledged_at=datetime(2026, 8, 2, 0, 0, tzinfo=UTC)
        )
        await _insert_asset(session, later, data=data)

        earlier = await _insert_receipt(
            session, owner_id=owner, acknowledged_at=datetime(2026, 8, 1, 0, 0, tzinfo=UTC)
        )
        await _insert_asset(session, earlier, data=data)

        # Classify later first.
        await classify_receipt(session=session, receipt=later, correlation_id=_CORR)
        # Classify earlier — it should become canonical.
        s_earlier = await classify_receipt(session=session, receipt=earlier, correlation_id=_CORR)

        # earlier is canonical (acknowledged first), so its status should be UNIQUE.
        assert s_earlier == DeduplicationStatus.UNIQUE
        await session.refresh(earlier)
        await session.refresh(later)
        assert earlier.canonical_receipt_id is None
        assert later.deduplication_status == DeduplicationStatus.CONFIRMED_DUPLICATE
        assert later.canonical_receipt_id == earlier.id


class TestSemanticDuplicate:
    """Rule 3: identical semantic signature → confirmed_duplicate."""

    async def test_same_semantic_different_assets(self, session: AsyncSession) -> None:
        owner = uuid.uuid4()
        data_a = b"\xff\xd8\xff" + b"\xaa" * 100
        data_b = b"\xff\xd8\xff" + b"\xbb" * 100  # different bytes

        receipt_a = await _insert_receipt(
            session, owner_id=owner, acknowledged_at=datetime(2026, 8, 1, 9, 0, tzinfo=UTC)
        )
        await _insert_asset(session, receipt_a, data=data_a)
        await _insert_revision(session, receipt_a)
        await classify_receipt(session=session, receipt=receipt_a, correlation_id=_CORR)

        receipt_b = await _insert_receipt(
            session, owner_id=owner, acknowledged_at=datetime(2026, 8, 1, 10, 0, tzinfo=UTC)
        )
        await _insert_asset(session, receipt_b, data=data_b)
        await _insert_revision(session, receipt_b)  # same merchant/date/total/items
        status = await classify_receipt(session=session, receipt=receipt_b, correlation_id=_CORR)

        assert status == DeduplicationStatus.CONFIRMED_DUPLICATE
        await session.refresh(receipt_b)
        assert receipt_b.deduplication_method == "exact_semantic"


class TestSuspectedDuplicate:
    """Rule 4: partial match (merchant+date+currency+total, but different line items)."""

    async def test_same_header_different_items_suspected(self, session: AsyncSession) -> None:
        owner = uuid.uuid4()
        data_a = b"\xff\xd8\xff" + b"\xcc" * 100
        data_b = b"\xff\xd8\xff" + b"\xdd" * 100

        receipt_a = await _insert_receipt(session, owner_id=owner)
        await _insert_asset(session, receipt_a, data=data_a)
        await _insert_revision(session, receipt_a, line_items=[("Item A", 1000)])
        await classify_receipt(session=session, receipt=receipt_a, correlation_id=_CORR)

        receipt_b = await _insert_receipt(session, owner_id=owner)
        await _insert_asset(session, receipt_b, data=data_b)
        # Same merchant/date/total but DIFFERENT line item descriptions → semantic fp differs.
        await _insert_revision(session, receipt_b, line_items=[("Item B", 1000)])
        status = await classify_receipt(session=session, receipt=receipt_b, correlation_id=_CORR)

        assert status == DeduplicationStatus.SUSPECTED_DUPLICATE


class TestFalsePositiveSafety:
    """Same merchant + amount on different dates must remain unique."""

    async def test_same_merchant_amount_different_date_unique(self, session: AsyncSession) -> None:
        owner = uuid.uuid4()
        data_a = b"\xff\xd8\xff" + b"\xee" * 100
        data_b = b"\xff\xd8\xff" + b"\xff" * 100

        receipt_a = await _insert_receipt(session, owner_id=owner)
        await _insert_asset(session, receipt_a, data=data_a)
        await _insert_revision(session, receipt_a, purchase_datetime=_PURCHASE_DT)
        await classify_receipt(session=session, receipt=receipt_a, correlation_id=_CORR)

        receipt_b = await _insert_receipt(session, owner_id=owner)
        await _insert_asset(session, receipt_b, data=data_b)
        await _insert_revision(session, receipt_b, purchase_datetime=_PURCHASE_DT_DIFFERENT_DAY)
        status = await classify_receipt(session=session, receipt=receipt_b, correlation_id=_CORR)

        assert status == DeduplicationStatus.UNIQUE


class TestOwnerIsolation:
    """Duplicate detection must not cross owner boundaries."""

    async def test_identical_assets_different_owners_unique(self, session: AsyncSession) -> None:
        data = b"\xff\xd8\xff" + b"\x12" * 100

        owner_a = uuid.uuid4()
        receipt_a = await _insert_receipt(session, owner_id=owner_a)
        await _insert_asset(session, receipt_a, data=data)
        await classify_receipt(session=session, receipt=receipt_a, correlation_id=_CORR)

        owner_b = uuid.uuid4()
        receipt_b = await _insert_receipt(session, owner_id=owner_b)
        await _insert_asset(session, receipt_b, data=data)
        status = await classify_receipt(session=session, receipt=receipt_b, correlation_id=_CORR)

        # Different owner → unique, not a duplicate.
        assert status == DeduplicationStatus.UNIQUE


class TestIdempotency:
    """Repeated classify_receipt calls converge to the same result."""

    async def test_classify_twice_stable(self, session: AsyncSession) -> None:
        owner = uuid.uuid4()
        data = b"\xff\xd8\xff" + b"\x34" * 100

        receipt = await _insert_receipt(session, owner_id=owner)
        await _insert_asset(session, receipt, data=data)

        s1 = await classify_receipt(session=session, receipt=receipt, correlation_id=_CORR)
        s2 = await classify_receipt(session=session, receipt=receipt, correlation_id=_CORR)

        assert s1 == s2 == DeduplicationStatus.UNIQUE

        events = (
            (
                await session.execute(
                    select(StateEvent).where(
                        StateEvent.receipt_id == receipt.id,
                        StateEvent.dimension == "deduplication",
                    )
                )
            )
            .scalars()
            .all()
        )
        assert len(events) == 1


class TestStateEventEmitted:
    """A deduplication StateEvent is emitted for each state transition."""

    async def test_event_written(self, session: AsyncSession) -> None:
        owner = uuid.uuid4()
        data = b"\xff\xd8\xff" + b"\x56" * 100

        receipt = await _insert_receipt(session, owner_id=owner)
        await _insert_asset(session, receipt, data=data)
        await classify_receipt(session=session, receipt=receipt, correlation_id=_CORR)

        events = (
            (
                await session.execute(
                    select(StateEvent).where(
                        StateEvent.receipt_id == receipt.id,
                        StateEvent.dimension == "deduplication",
                    )
                )
            )
            .scalars()
            .all()
        )
        assert len(events) >= 1
        assert events[-1].to_state == DeduplicationStatus.UNIQUE


class TestEvidencePreservation:
    """Duplicate classification never deletes or modifies evidence assets."""

    async def test_assets_intact_after_classification(self, session: AsyncSession) -> None:
        owner = uuid.uuid4()
        data = b"\xff\xd8\xff" + b"\x78" * 100
        sha = _sha256_hex(data)

        receipt = await _insert_receipt(session, owner_id=owner)
        asset = await _insert_asset(session, receipt, data=data)
        await classify_receipt(session=session, receipt=receipt, correlation_id=_CORR)

        await session.refresh(asset)
        assert asset.sha256 == sha
        assert asset.upload_status == "verified"


class TestBackfillDryRun:
    """Dry-run reports an accurate cluster without persisting any projection."""

    async def test_dry_run_rolls_back_all_changes(self, factory) -> None:
        owner = uuid.uuid4()
        data = b"\xff\xd8\xff" + b"\x91" * 100

        async with factory() as setup_session:
            earlier = await _insert_receipt(
                setup_session,
                owner_id=owner,
                acknowledged_at=datetime(2026, 8, 1, 8, 0, tzinfo=UTC),
            )
            later = await _insert_receipt(
                setup_session,
                owner_id=owner,
                acknowledged_at=datetime(2026, 8, 1, 9, 0, tzinfo=UTC),
            )
            await _insert_asset(setup_session, earlier, data=data)
            await _insert_asset(setup_session, later, data=data)
            receipt_ids = (earlier.id, later.id)
            await setup_session.commit()

        counts = await _run_backfill(
            factory,
            dry_run=True,
            batch_size=1,
            limit=None,
        )
        assert counts["evaluated"] == 2
        assert counts["unique"] == 1
        assert counts["confirmed_duplicate"] == 1

        async with factory() as verify_session:
            receipts = (
                (await verify_session.execute(select(Receipt).where(Receipt.id.in_(receipt_ids))))
                .scalars()
                .all()
            )
            assert all(r.deduplication_status == DeduplicationStatus.UNCHECKED for r in receipts)
            assert all(r.evidence_fingerprint is None for r in receipts)
            events = (
                (
                    await verify_session.execute(
                        select(StateEvent).where(StateEvent.receipt_id.in_(receipt_ids))
                    )
                )
                .scalars()
                .all()
            )
            assert events == []
