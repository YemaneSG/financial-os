"""Deterministic receipt deduplication — fingerprinting and canonical selection.

Pure functions only. No database access, no I/O, no language model calls.
Fingerprints are opaque SHA-256 hex strings; no merchant text, amounts, or
owner identifiers are logged or returned by public APIs (AGENTS.md §7).

Evidence fingerprint: SHA-256 over versioned ordered (ordinal, sha256) manifest.
  Object paths/storage keys are excluded — only content hashes matter.

Semantic fingerprint: SHA-256 over versioned normalized (merchant, purchase
  instant, currency, total, sorted line-item multiset). Returns None when any
  required field is absent, making the signature incomplete.

Canonical selection: earliest acknowledged_at wins; UUID lexicographic
  tie-break for simultaneous acknowledgement.
"""

from __future__ import annotations

import hashlib
import json
import unicodedata
from datetime import UTC, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import uuid

_EVIDENCE_VERSION = "evidence-v1"
_SEMANTIC_VERSION = "semantic-v1"


def _coerce_int(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise ValueError(f"{field_name} must be an integer.")
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an integer.") from exc


def compute_evidence_fingerprint(asset_entries: list[dict[str, object]]) -> str:
    """SHA-256 over the versioned ordered asset-hash manifest.

    Each entry must have 'ordinal' (int) and 'sha256' (str).
    Storage object paths are excluded to keep the fingerprint path-independent.
    """
    if not asset_entries:
        raise ValueError("At least one verified asset is required.")
    entries = sorted(
        asset_entries,
        key=lambda asset: _coerce_int(asset.get("ordinal"), "Asset ordinal"),
    )
    for entry in entries:
        sha256 = entry.get("sha256")
        if not isinstance(sha256, str) or len(sha256) != 64:
            raise ValueError("Each verified asset must have a SHA-256 digest.")
        try:
            int(sha256, 16)
        except ValueError as exc:
            raise ValueError("Each verified asset must have a SHA-256 digest.") from exc
    manifest = json.dumps(
        [
            {
                "ordinal": _coerce_int(entry.get("ordinal"), "Asset ordinal"),
                "sha256": str(entry["sha256"]),
            }
            for entry in entries
        ],
        separators=(",", ":"),
        sort_keys=True,
    )
    raw = f"{_EVIDENCE_VERSION}:{manifest}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _normalize_text(raw: str | None) -> str | None:
    if not raw:
        return None
    normalized = unicodedata.normalize("NFC", raw.strip().casefold())
    return normalized or None


def compute_semantic_fingerprint(
    merchant_normalized: str | None,
    purchase_datetime: datetime | None,
    currency: str | None,
    total_minor: int | None,
    line_items: list[dict[str, object]],
) -> str | None:
    """SHA-256 over the versioned normalized semantic receipt signature.

    Returns None when any required field is absent (merchant, purchase instant,
    currency, total) or when any line item is missing normalized_description or
    line_total_minor — making the semantic signature incomplete.

    line_items: list of dicts with 'normalized_description' and 'line_total_minor'.
    """
    merchant_norm = _normalize_text(merchant_normalized)
    if merchant_norm is None:
        return None
    if purchase_datetime is None:
        return None
    if not currency:
        return None
    if total_minor is None:
        return None

    # Normalize purchase instant to UTC ISO-8601.
    if purchase_datetime.tzinfo is not None:
        purchase_utc = purchase_datetime.astimezone(UTC).isoformat()
    else:
        purchase_utc = purchase_datetime.replace(tzinfo=UTC).isoformat()

    # A semantic signature is complete only when the receipt has item evidence.
    if not line_items:
        return None

    # All line items must have both fields for a complete signature.
    normalized_items: list[dict[str, object]] = []
    for li in line_items:
        desc = li.get("normalized_description")
        total = li.get("line_total_minor")
        normalized_description = _normalize_text(str(desc)) if desc is not None else None
        if normalized_description is None or total is None:
            return None
        normalized_items.append(
            {"d": normalized_description, "t": _coerce_int(total, "Line total")}
        )

    # Sort line-item multiset deterministically (description then total).
    normalized_items.sort(key=lambda x: (x["d"], x["t"]))

    payload = json.dumps(
        {
            "currency": currency.upper(),
            "instant": purchase_utc,
            "items": normalized_items,
            "merchant": merchant_norm,
            "total": int(total_minor),
        },
        separators=(",", ":"),
        sort_keys=True,
    )
    raw = f"{_SEMANTIC_VERSION}:{payload}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def select_canonical_receipt_id(
    receipt_a_id: uuid.UUID,
    receipt_a_acknowledged_at: datetime | None,
    receipt_b_id: uuid.UUID,
    receipt_b_acknowledged_at: datetime | None,
) -> uuid.UUID:
    """Return the canonical receipt ID: earliest acknowledged, UUID tie-break.

    Acknowledged receipts always beat unacknowledged ones.
    When both share the same instant, lexicographically smallest UUID wins.
    Never produces a self-link (caller must ensure a_id != b_id).
    """
    a_acked = receipt_a_acknowledged_at is not None
    b_acked = receipt_b_acknowledged_at is not None

    if a_acked and b_acked:
        if receipt_a_acknowledged_at < receipt_b_acknowledged_at:  # type: ignore[operator]
            return receipt_a_id
        if receipt_b_acknowledged_at < receipt_a_acknowledged_at:  # type: ignore[operator]
            return receipt_b_id
        # Same instant: UUID tie-break.
        return receipt_a_id if str(receipt_a_id) < str(receipt_b_id) else receipt_b_id

    if a_acked:
        return receipt_a_id
    if b_acked:
        return receipt_b_id
    # Neither acknowledged: UUID tie-break.
    return receipt_a_id if str(receipt_a_id) < str(receipt_b_id) else receipt_b_id
