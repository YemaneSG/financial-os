"""Pydantic schemas for POST /api/v1/receipts/search.

Search terms are in the JSON body so they never appear in URL-based request logs
(see packet §5, control LOG-01).
Fingerprints, hashes, owner identifiers, and receipt content are never returned.
"""

from __future__ import annotations

import unicodedata
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from financial_os.schemas.receipt import ReceiptListItemSchema

_VALID_PROCESSING_STATUSES = frozenset(
    {
        "reserved",
        "uploading",
        "uploaded",
        "queued",
        "processing",
        "extracted",
        "retryable_failed",
        "failed",
        "abandoned",
    }
)

_VALID_VERIFICATION_STATUSES = frozenset(
    {"unreviewed", "system_validated", "needs_review", "human_verified"}
)

_VALID_DEDUPLICATION_STATUSES = frozenset(
    {"unchecked", "unique", "suspected_duplicate", "confirmed_duplicate"}
)

SortOrder = Literal[
    "effective_date_desc",
    "effective_date_asc",
    "amount_desc",
    "amount_asc",
]


def _normalize_query(raw: str) -> str:
    """Unicode-normalize and lowercase a search term."""
    return unicodedata.normalize("NFC", raw.strip().lower())


class SearchReceiptsRequest(BaseModel):
    """Body for POST /api/v1/receipts/search.

    The query field is matched case-insensitively against the normalized merchant
    name and normalized line-item descriptions.  Raw OCR / provider output is
    never searched (LOG-01: terms must not enter infrastructure request URL logs).
    """

    query: str | None = Field(default=None, min_length=1, max_length=200)
    date_from: datetime | None = None
    date_to: datetime | None = None
    amount_min_minor: int | None = Field(default=None, ge=0)
    amount_max_minor: int | None = Field(default=None, ge=0)
    processing_status: list[str] = Field(default_factory=list, max_length=10)
    verification_status: list[str] = Field(default_factory=list, max_length=5)
    deduplication_status: list[str] = Field(default_factory=list, max_length=5)
    sort: SortOrder = "effective_date_desc"
    cursor: str | None = Field(default=None, max_length=1000)
    limit: int = Field(default=20, ge=1, le=50)

    @field_validator("query", mode="before")
    @classmethod
    def validate_query(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = _normalize_query(value)
        if not normalized:
            raise ValueError("query must contain non-whitespace characters")
        return normalized

    @field_validator("processing_status", mode="before")
    @classmethod
    def validate_processing_statuses(cls, values: list[str]) -> list[str]:
        for v in values:
            if v not in _VALID_PROCESSING_STATUSES:
                raise ValueError(f"Unknown processing_status: {v!r}")
        return list(dict.fromkeys(values))  # dedup, preserve order

    @field_validator("verification_status", mode="before")
    @classmethod
    def validate_verification_statuses(cls, values: list[str]) -> list[str]:
        for v in values:
            if v not in _VALID_VERIFICATION_STATUSES:
                raise ValueError(f"Unknown verification_status: {v!r}")
        return list(dict.fromkeys(values))

    @field_validator("deduplication_status", mode="before")
    @classmethod
    def validate_deduplication_statuses(cls, values: list[str]) -> list[str]:
        for v in values:
            if v not in _VALID_DEDUPLICATION_STATUSES:
                raise ValueError(f"Unknown deduplication_status: {v!r}")
        return list(dict.fromkeys(values))

    @model_validator(mode="after")
    def validate_amount_range(self) -> SearchReceiptsRequest:
        if (
            self.amount_min_minor is not None
            and self.amount_max_minor is not None
            and self.amount_min_minor > self.amount_max_minor
        ):
            raise ValueError("amount_min_minor must be ≤ amount_max_minor")
        return self

    @model_validator(mode="after")
    def validate_date_range(self) -> SearchReceiptsRequest:
        if self.date_from is not None and self.date_to is not None:
            if self.date_from > self.date_to:
                raise ValueError("date_from must be ≤ date_to")
        return self

    @property
    def normalized_query(self) -> str | None:
        if self.query is None:
            return None
        return self.query


class MatchContext(BaseModel):
    """Optional context indicating what caused a search result to match."""

    source: Literal["merchant", "line_item"]
    matched_description: str | None = Field(default=None, max_length=500)


class SearchReceiptItemSchema(ReceiptListItemSchema):
    """Receipt list item augmented with optional search match context."""

    captured_at: datetime | None = None
    match_context: MatchContext | None = None


class SearchReceiptsResponse(BaseModel):
    """Response for POST /api/v1/receipts/search."""

    receipts: list[SearchReceiptItemSchema]
    total_count: int = Field(ge=0)
    next_cursor: str | None = None
