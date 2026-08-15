"""Security tests for deduplication owner isolation.

Verifies that deduplication queries are always owner-scoped and cannot
match receipts belonging to a different owner.

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
from financial_os.models.extraction import LineItemRevision, ReceiptRevision
from financial_os.models.receipt import Receipt, ReceiptAsset
from financial_os.services.dedup import classify_receipt

pytestmark = [
    pytest.mark.security,
    pytest.mark.asyncio(loop_scope="module"),
]

_CORR = "security-test-corr"


@pytest.fixture(scope="module")
def db_url_module() -> str:
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        pytest.skip("DATABASE_URL not set — skipping security dedup tests")
    return url


@pytest_asyncio.fixture(scope="module")
async def engine(db_url_module: str):
    eng = create_async_engine(db_url_module, echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await eng.dispose()


@pytest_asyncio.fixture(scope="module")
async def factory(engine):
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture
async def session(factory):
    async with factory() as sess:
        yield sess
        await sess.rollback()


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


async def _insert_extracted_receipt(
    session: AsyncSession,
    owner_id: uuid.UUID,
    asset_data: bytes,
    *,
    merchant: str = "Synthetic Store",
    total_minor: int = 1080,
) -> Receipt:
    now = datetime.now(UTC)
    r = Receipt(
        id=uuid.uuid4(),
        owner_id=owner_id,
        client_submission_id=uuid.uuid4(),
        financial_context="personal",
        processing_status="extracted",
        verification_status="system_validated",
        expected_asset_count=1,
        captured_at=now,
        acknowledged_at=now,
        row_version=0,
    )
    session.add(r)
    await session.flush()

    asset = ReceiptAsset(
        id=uuid.uuid4(),
        receipt_id=r.id,
        ordinal=1,
        object_key=f"originals/{owner_id}/{r.id}/{uuid.uuid4()}",
        storage_generation="1",
        declared_mime_type="image/jpeg",
        verified_mime_type="image/jpeg",
        byte_size=len(asset_data),
        sha256=_sha256(asset_data),
        upload_status="verified",
    )
    session.add(asset)

    rev = ReceiptRevision(
        id=uuid.uuid4(),
        receipt_id=r.id,
        parent_revision_id=None,
        source_type="extractor",
        extraction_run_id=None,
        merchant_raw=merchant.upper(),
        merchant_normalized=merchant,
        purchase_datetime=datetime(2026, 8, 1, 12, 0, 0, tzinfo=UTC),
        purchase_timezone=None,
        currency="USD",
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

    li = LineItemRevision(
        id=uuid.uuid4(),
        receipt_revision_id=rev.id,
        ordinal=1,
        raw_description="SYNTHETIC ITEM A",
        normalized_description="Synthetic Item A",
        line_total_minor=total_minor - 80,
        discount_minor=None,
        field_confidence={},
    )
    session.add(li)

    r.current_revision_id = rev.id
    session.add(r)
    await session.flush()
    return r


class TestDedupOwnerIsolation:
    async def test_exact_evidence_cross_owner_yields_unique(self, session: AsyncSession) -> None:
        """Identical asset bytes uploaded by two different owners must each classify UNIQUE."""
        data = b"\xff\xd8\xff" + b"\xab" * 200

        owner_a = uuid.uuid4()
        owner_b = uuid.uuid4()

        receipt_a = await _insert_extracted_receipt(session, owner_a, data)
        await classify_receipt(session=session, receipt=receipt_a, correlation_id=_CORR)

        receipt_b = await _insert_extracted_receipt(session, owner_b, data)
        status_b = await classify_receipt(session=session, receipt=receipt_b, correlation_id=_CORR)

        assert status_b == DeduplicationStatus.UNIQUE, (
            "Cross-owner evidence fingerprint match must not produce CONFIRMED_DUPLICATE"
        )

    async def test_exact_semantic_cross_owner_yields_unique(self, session: AsyncSession) -> None:
        """Identical semantic signatures from different owners must each be UNIQUE."""
        data_a = b"\xff\xd8\xff" + b"\xcd" * 200
        data_b = b"\xff\xd8\xff" + b"\xef" * 200  # different bytes, same semantics

        owner_a = uuid.uuid4()
        owner_b = uuid.uuid4()

        receipt_a = await _insert_extracted_receipt(session, owner_a, data_a)
        await classify_receipt(session=session, receipt=receipt_a, correlation_id=_CORR)

        receipt_b = await _insert_extracted_receipt(session, owner_b, data_b)
        status_b = await classify_receipt(session=session, receipt=receipt_b, correlation_id=_CORR)

        assert status_b == DeduplicationStatus.UNIQUE, (
            "Cross-owner semantic fingerprint match must not produce CONFIRMED_DUPLICATE"
        )

    async def test_partial_match_cross_owner_yields_unique(self, session: AsyncSession) -> None:
        """Partial merchant+date+total match from a different owner must yield UNIQUE."""
        data_a = b"\xff\xd8\xff" + b"\x13" * 200
        data_b = b"\xff\xd8\xff" + b"\x57" * 200

        owner_a = uuid.uuid4()
        owner_b = uuid.uuid4()

        receipt_a = await _insert_extracted_receipt(
            session, owner_a, data_a, merchant="Shared Merchant", total_minor=999
        )
        await classify_receipt(session=session, receipt=receipt_a, correlation_id=_CORR)

        receipt_b = await _insert_extracted_receipt(
            session, owner_b, data_b, merchant="Shared Merchant", total_minor=999
        )
        status_b = await classify_receipt(session=session, receipt=receipt_b, correlation_id=_CORR)

        assert status_b == DeduplicationStatus.UNIQUE, (
            "Cross-owner partial match must not produce SUSPECTED_DUPLICATE"
        )

    async def test_canonical_receipt_id_never_crosses_owner(self, session: AsyncSession) -> None:
        """canonical_receipt_id for a confirmed duplicate must belong to the same owner."""
        data = b"\xff\xd8\xff" + b"\x99" * 200

        owner_a = uuid.uuid4()
        owner_b = uuid.uuid4()

        receipt_a = await _insert_extracted_receipt(session, owner_a, data)
        await classify_receipt(session=session, receipt=receipt_a, correlation_id=_CORR)

        receipt_b = await _insert_extracted_receipt(session, owner_b, data)
        await classify_receipt(session=session, receipt=receipt_b, correlation_id=_CORR)

        await session.refresh(receipt_b)
        # Receipt B must have no cross-owner canonical pointer.
        if receipt_b.canonical_receipt_id is not None:
            # Verify the canonical is owned by the same owner.
            canonical_result = await session.execute(
                select(Receipt).where(Receipt.id == receipt_b.canonical_receipt_id)
            )
            canonical = canonical_result.scalar_one_or_none()
            assert canonical is not None
            assert canonical.owner_id == receipt_b.owner_id, (
                "canonical_receipt_id must point to a receipt owned by the same owner"
            )
