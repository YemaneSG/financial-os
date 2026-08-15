"""Unit tests for evidence and semantic fingerprinting functions.

All data is synthetic. No real receipt content or owner PII (AGENTS.md §7).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest

from financial_os.domain.dedup import (
    compute_evidence_fingerprint,
    compute_semantic_fingerprint,
    select_canonical_receipt_id,
)


@pytest.mark.unit
class TestEvidenceFingerprint:
    def test_deterministic(self) -> None:
        assets = [{"ordinal": 1, "sha256": "a" * 64}]
        assert compute_evidence_fingerprint(assets) == compute_evidence_fingerprint(assets)

    def test_different_sha256_yields_different_hash(self) -> None:
        a = [{"ordinal": 1, "sha256": "a" * 64}]
        b = [{"ordinal": 1, "sha256": "b" * 64}]
        assert compute_evidence_fingerprint(a) != compute_evidence_fingerprint(b)

    def test_ordinal_order_matters(self) -> None:
        ab = [{"ordinal": 1, "sha256": "a" * 64}, {"ordinal": 2, "sha256": "b" * 64}]
        ba = [{"ordinal": 2, "sha256": "b" * 64}, {"ordinal": 1, "sha256": "a" * 64}]
        # Same logical content but submitted in reverse order — must produce same hash
        # because we sort by ordinal.
        assert compute_evidence_fingerprint(ab) == compute_evidence_fingerprint(ba)

    def test_two_assets_vs_one(self) -> None:
        one = [{"ordinal": 1, "sha256": "a" * 64}]
        two = [{"ordinal": 1, "sha256": "a" * 64}, {"ordinal": 2, "sha256": "b" * 64}]
        assert compute_evidence_fingerprint(one) != compute_evidence_fingerprint(two)

    def test_excludes_object_path(self) -> None:
        a = [{"ordinal": 1, "sha256": "a" * 64, "object_key": "originals/owner-x/rx/a"}]
        b = [{"ordinal": 1, "sha256": "a" * 64, "object_key": "originals/owner-y/ry/b"}]
        assert compute_evidence_fingerprint(a) == compute_evidence_fingerprint(b)

    def test_returns_64_char_hex(self) -> None:
        fp = compute_evidence_fingerprint([{"ordinal": 1, "sha256": "c" * 64}])
        assert len(fp) == 64
        assert all(c in "0123456789abcdef" for c in fp)


@pytest.mark.unit
class TestSemanticFingerprint:
    _PURCHASE_DT = datetime(2026, 8, 1, 12, 0, 0, tzinfo=UTC)
    _LINE_ITEMS = [{"normalized_description": "Synthetic Item A", "line_total_minor": 1000}]

    def _fp(self, **kw: object) -> str | None:
        defaults: dict[str, object] = {
            "merchant_normalized": "Synthetic Store",
            "purchase_datetime": self._PURCHASE_DT,
            "currency": "USD",
            "total_minor": 1080,
            "line_items": self._LINE_ITEMS,
        }
        defaults.update(kw)
        return compute_semantic_fingerprint(**defaults)  # type: ignore[arg-type]

    def test_deterministic(self) -> None:
        assert self._fp() == self._fp()

    def test_none_merchant_returns_none(self) -> None:
        assert self._fp(merchant_normalized=None) is None

    def test_none_purchase_datetime_returns_none(self) -> None:
        assert self._fp(purchase_datetime=None) is None

    def test_none_currency_returns_none(self) -> None:
        assert self._fp(currency=None) is None

    def test_none_total_returns_none(self) -> None:
        assert self._fp(total_minor=None) is None

    def test_line_item_missing_description_returns_none(self) -> None:
        items = [{"normalized_description": None, "line_total_minor": 1000}]
        assert self._fp(line_items=items) is None

    def test_line_item_missing_total_returns_none(self) -> None:
        items = [{"normalized_description": "Item A", "line_total_minor": None}]
        assert self._fp(line_items=items) is None

    def test_merchant_case_insensitive(self) -> None:
        assert self._fp(merchant_normalized="STORE") == self._fp(merchant_normalized="store")

    def test_currency_case_insensitive(self) -> None:
        assert self._fp(currency="usd") == self._fp(currency="USD")

    def test_different_merchant_different_hash(self) -> None:
        assert self._fp(merchant_normalized="Store A") != self._fp(merchant_normalized="Store B")

    def test_different_total_different_hash(self) -> None:
        assert self._fp(total_minor=1080) != self._fp(total_minor=1090)

    def test_different_date_different_hash(self) -> None:
        dt2 = datetime(2026, 9, 1, 12, 0, 0, tzinfo=UTC)
        assert self._fp() != self._fp(purchase_datetime=dt2)

    def test_line_item_order_invariant(self) -> None:
        items_ab = [
            {"normalized_description": "Item A", "line_total_minor": 500},
            {"normalized_description": "Item B", "line_total_minor": 580},
        ]
        items_ba = [
            {"normalized_description": "Item B", "line_total_minor": 580},
            {"normalized_description": "Item A", "line_total_minor": 500},
        ]
        fp_ab = compute_semantic_fingerprint(
            merchant_normalized="Store",
            purchase_datetime=self._PURCHASE_DT,
            currency="USD",
            total_minor=1080,
            line_items=items_ab,
        )
        fp_ba = compute_semantic_fingerprint(
            merchant_normalized="Store",
            purchase_datetime=self._PURCHASE_DT,
            currency="USD",
            total_minor=1080,
            line_items=items_ba,
        )
        assert fp_ab == fp_ba

    def test_empty_line_items_are_incomplete(self) -> None:
        fp = compute_semantic_fingerprint(
            merchant_normalized="Store",
            purchase_datetime=self._PURCHASE_DT,
            currency="USD",
            total_minor=1080,
            line_items=[],
        )
        assert fp is None

    def test_blank_line_item_description_is_incomplete(self) -> None:
        assert (
            self._fp(line_items=[{"normalized_description": "  ", "line_total_minor": 1080}])
            is None
        )

    def test_returns_64_char_hex(self) -> None:
        fp = self._fp()
        assert fp is not None
        assert len(fp) == 64
        assert all(c in "0123456789abcdef" for c in fp)


@pytest.mark.unit
class TestSelectCanonical:
    _ID_A = uuid.UUID("00000000-0000-0000-0000-000000000001")
    _ID_B = uuid.UUID("00000000-0000-0000-0000-000000000002")
    _EARLIER = datetime(2026, 8, 1, 10, 0, tzinfo=UTC)
    _LATER = datetime(2026, 8, 1, 11, 0, tzinfo=UTC)

    def test_earlier_acknowledged_wins(self) -> None:
        result = select_canonical_receipt_id(
            receipt_a_id=self._ID_A,
            receipt_a_acknowledged_at=self._EARLIER,
            receipt_b_id=self._ID_B,
            receipt_b_acknowledged_at=self._LATER,
        )
        assert result == self._ID_A

    def test_later_acknowledged_loses(self) -> None:
        result = select_canonical_receipt_id(
            receipt_a_id=self._ID_A,
            receipt_a_acknowledged_at=self._LATER,
            receipt_b_id=self._ID_B,
            receipt_b_acknowledged_at=self._EARLIER,
        )
        assert result == self._ID_B

    def test_uuid_tiebreak_when_same_instant(self) -> None:
        result = select_canonical_receipt_id(
            receipt_a_id=self._ID_A,
            receipt_a_acknowledged_at=self._EARLIER,
            receipt_b_id=self._ID_B,
            receipt_b_acknowledged_at=self._EARLIER,
        )
        # _ID_A < _ID_B lexicographically → A wins.
        assert result == self._ID_A

    def test_acknowledged_beats_unacknowledged(self) -> None:
        result = select_canonical_receipt_id(
            receipt_a_id=self._ID_A,
            receipt_a_acknowledged_at=None,
            receipt_b_id=self._ID_B,
            receipt_b_acknowledged_at=self._EARLIER,
        )
        assert result == self._ID_B

    def test_neither_acknowledged_uuid_tiebreak(self) -> None:
        result = select_canonical_receipt_id(
            receipt_a_id=self._ID_B,
            receipt_a_acknowledged_at=None,
            receipt_b_id=self._ID_A,
            receipt_b_acknowledged_at=None,
        )
        # _ID_A < _ID_B → A (passed as b) wins.
        assert result == self._ID_A

    def test_deterministic_commutative(self) -> None:
        r1 = select_canonical_receipt_id(
            receipt_a_id=self._ID_A,
            receipt_a_acknowledged_at=self._EARLIER,
            receipt_b_id=self._ID_B,
            receipt_b_acknowledged_at=self._LATER,
        )
        r2 = select_canonical_receipt_id(
            receipt_a_id=self._ID_B,
            receipt_a_acknowledged_at=self._LATER,
            receipt_b_id=self._ID_A,
            receipt_b_acknowledged_at=self._EARLIER,
        )
        assert r1 == r2
