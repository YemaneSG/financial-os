"""Deterministic fake extraction adapter for tests.

Returns pre-configured synthetic results without calling any external service.
Never returns real receipt content — only synthetic fixture data.
"""

from __future__ import annotations

from typing import Any

from financial_os.adapters.extraction.base import (
    AssetForExtraction,
    ExtractionAdapter,
    ExtractionResult,
)

_DEFAULT_RESULT: dict[str, Any] = {
    "schema_version": "v1",
    "merchant_raw": "ACME TEST STORE",
    "merchant_normalized": "Acme Test Store",
    "purchase_date": "2026-08-01",
    "purchase_time": "14:30:00",
    "purchase_timezone": None,
    "currency": "USD",
    "subtotal_minor": 1000,
    "tax_minor": 80,
    "tip_minor": None,
    "discount_minor": None,
    "total_minor": 1080,
    "payment_method_hint": None,
    "overall_confidence": 0.95,
    "line_items": [
        {
            "ordinal": 1,
            "raw_description": "TEST ITEM A",
            "normalized_description": "Test Item A",
            "quantity": "1",
            "unit": "each",
            "unit_price_decimal": "10.00",
            "line_total_minor": 1000,
            "discount_minor": None,
            "category_suggestion": None,
            "field_confidence": {},
        }
    ],
    "provider_notes": None,
}


class FakeExtractionAdapter(ExtractionAdapter):
    """Test double that returns synthetic extraction results."""

    def __init__(
        self,
        result: dict[str, Any] | None = None,
        latency_ms: int = 100,
        raise_on_call: Exception | None = None,
    ) -> None:
        self._result = result if result is not None else _DEFAULT_RESULT.copy()
        self._latency_ms = latency_ms
        self._raise_on_call = raise_on_call
        self.call_count = 0

    @property
    def provider_name(self) -> str:
        return "fake"

    @property
    def model_id(self) -> str:
        return "fake-model-v1"

    @property
    def prompt_version(self) -> str:
        return "v1"

    @property
    def schema_version(self) -> str:
        return "v1"

    async def extract(self, assets: list[AssetForExtraction]) -> ExtractionResult:
        self.call_count += 1
        if self._raise_on_call is not None:
            raise self._raise_on_call
        return ExtractionResult(
            raw=self._result.copy(),
            provider_request_id=f"fake-req-{self.call_count}",
            latency_ms=self._latency_ms,
            estimated_cost_cents=None,
        )
