"""Unit tests for the dedup classification service using an in-memory async session.

All data is entirely synthetic. No real receipt content or PII (AGENTS.md §7).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from financial_os.domain.states import DeduplicationStatus
from financial_os.models.receipt import Receipt, ReceiptAsset


def _make_asset(
    receipt_id: uuid.UUID,
    ordinal: int = 1,
    sha256: str | None = None,
) -> ReceiptAsset:
    asset = MagicMock(spec=ReceiptAsset)
    asset.id = uuid.uuid4()
    asset.receipt_id = receipt_id
    asset.ordinal = ordinal
    asset.sha256 = sha256 or ("a" * 64)
    asset.upload_status = "verified"
    asset.object_key = f"originals/owner/{receipt_id}/{asset.id}"
    return asset


def _make_receipt(
    *,
    owner_id: uuid.UUID | None = None,
    acknowledged_at: datetime | None = None,
    dedup_status: str = "unchecked",
) -> Receipt:
    r = MagicMock(spec=Receipt)
    r.id = uuid.uuid4()
    r.owner_id = owner_id or uuid.uuid4()
    r.acknowledged_at = acknowledged_at or datetime.now(UTC)
    r.deduplication_status = dedup_status
    r.canonical_receipt_id = None
    r.current_revision_id = None
    r.processing_status = "extracted"
    r.evidence_fingerprint = None
    r.semantic_fingerprint = None
    return r


def _make_async_scalars(rows: list[object]) -> MagicMock:
    result = MagicMock()
    result.scalars.return_value.all.return_value = rows
    result.scalar_one_or_none.return_value = rows[0] if rows else None
    return result


@pytest.mark.unit
class TestClassifyReceiptUnit:
    """Lightweight unit tests using mock sessions.

    Integration tests (with real DB) cover the full round-trip in test_dedup.py.
    """

    @pytest.mark.asyncio
    async def test_no_assets_classifies_unique(self) -> None:
        """A receipt with no verified assets gets evidence_fp=None → unique."""
        from financial_os.services.dedup import classify_receipt

        owner_id = uuid.uuid4()
        receipt = _make_receipt(owner_id=owner_id)

        session = AsyncMock()
        # No assets, no revision matches.
        session.execute.return_value = _make_async_scalars([])
        session.flush = AsyncMock()
        session.add = MagicMock()
        session.refresh = AsyncMock()

        status = await classify_receipt(
            session=session, receipt=receipt, correlation_id="test-corr"
        )
        assert status == DeduplicationStatus.UNIQUE

    @pytest.mark.asyncio
    async def test_evidence_match_makes_duplicate(self) -> None:
        """When a matching evidence fingerprint exists, receipt is CONFIRMED_DUPLICATE."""
        from financial_os.services.dedup import classify_receipt

        owner_id = uuid.uuid4()
        earlier_dt = datetime(2026, 8, 1, 10, 0, tzinfo=UTC)
        later_dt = datetime(2026, 8, 1, 11, 0, tzinfo=UTC)

        receipt = _make_receipt(owner_id=owner_id, acknowledged_at=later_dt)
        # No current_revision_id → skips revision/line-item queries.
        matching_receipt = _make_receipt(owner_id=owner_id, acknowledged_at=earlier_dt)
        asset = _make_asset(receipt.id)

        call_count = 0

        async def _mock_execute(stmt: object) -> MagicMock:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # Assets query (no current_revision_id → no revision query follows)
                return _make_async_scalars([asset])
            if call_count == 2:
                # Evidence fingerprint match query
                result = MagicMock()
                result.scalars.return_value.all.return_value = [matching_receipt]
                return result
            return _make_async_scalars([])

        session = AsyncMock()
        session.execute = _mock_execute
        session.flush = AsyncMock()
        session.add = MagicMock()

        status = await classify_receipt(
            session=session, receipt=receipt, correlation_id="test-corr"
        )
        assert status == DeduplicationStatus.CONFIRMED_DUPLICATE
        assert receipt.canonical_receipt_id == (
            matching_receipt.canonical_receipt_id or matching_receipt.id
        )
