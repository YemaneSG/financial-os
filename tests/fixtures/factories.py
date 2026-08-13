"""Synthetic data factories for Financial OS tests.

All data is entirely synthetic. No real receipt images, financial content,
or owner PII appears in these factories (OPS-02, AGENTS.md §7).
"""

from __future__ import annotations

import hashlib
import uuid
from typing import Any

# ── Minimal synthetic JPEG (1×1 pixel) ───────────────────────────────────────
# Hand-crafted minimal valid JPEG bytes — not a real receipt image.
MINIMAL_JPEG = (
    b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
    b"\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c"
    b"\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c"
    b"\x1c $.' \",#\x1c\x1c(7),01444\x1f'9=82<.342\x1edL\x0b\xff\xc0\x00\x0b"
    b"\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01"
    b"\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05"
    b"\x06\x07\x08\t\n\x0b\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xfb\xd5\xff\xd9"
)

MINIMAL_PNG = (
    b"\x89PNG\r\n\x1a\n"  # magic
    b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02"
    b"\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00"
    b"\x00\x01\x01\x00\x18\xdd\x8d\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


def make_owner_id() -> uuid.UUID:
    return uuid.uuid4()


def make_receipt_id() -> uuid.UUID:
    return uuid.uuid4()


def make_asset_id() -> uuid.UUID:
    return uuid.uuid4()


def make_client_submission_key() -> uuid.UUID:
    return uuid.uuid4()


def make_object_key(owner_id: uuid.UUID, receipt_id: uuid.UUID, asset_id: uuid.UUID) -> str:
    return f"originals/{owner_id}/{receipt_id}/{asset_id}"


def make_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def make_synthetic_extraction_result(
    *,
    currency: str = "USD",
    total_minor: int = 1080,
    subtotal_minor: int = 1000,
    tax_minor: int = 80,
    schema_version: str = "v1",
) -> dict[str, Any]:
    """Return a synthetc extraction result that passes schema and arithmetic checks."""
    return {
        "schema_version": schema_version,
        "merchant_raw": "SYNTHETIC TEST STORE",
        "merchant_normalized": "Synthetic Test Store",
        "purchase_date": "2026-08-01",
        "purchase_time": "12:00:00",
        "purchase_timezone": None,
        "currency": currency,
        "subtotal_minor": subtotal_minor,
        "tax_minor": tax_minor,
        "tip_minor": None,
        "discount_minor": None,
        "total_minor": total_minor,
        "payment_method_hint": None,
        "overall_confidence": 0.95,
        "line_items": [
            {
                "ordinal": 1,
                "raw_description": "SYNTHETIC ITEM A",
                "normalized_description": "Synthetic Item A",
                "quantity": "1",
                "unit": "each",
                "unit_price_decimal": "10.00",
                "line_total_minor": subtotal_minor,
                "discount_minor": None,
                "category_suggestion": None,
                "field_confidence": {},
            }
        ],
        "provider_notes": None,
    }


def make_create_receipt_payload(
    *,
    client_submission_key: uuid.UUID | None = None,
    expected_asset_count: int = 1,
    financial_context: str = "personal",
) -> dict[str, Any]:
    return {
        "client_submission_key": str(client_submission_key or make_client_submission_key()),
        "expected_asset_count": expected_asset_count,
        "financial_context": financial_context,
        "captured_at": None,
        "assets": [
            {
                "ordinal": i + 1,
                "declared_mime_type": "image/jpeg",
                "byte_size": len(MINIMAL_JPEG),
            }
            for i in range(expected_asset_count)
        ],
    }
