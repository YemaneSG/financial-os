"""Pydantic schemas for the /api/v1/receipts routes.

All schemas match the OpenAPI contract in contracts/openapi.yaml exactly.
Never include signed URLs, auth tokens, or receipt content in error fields.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from financial_os.domain.states import DeduplicationStatus

_SAFE_FINDING_FIELD_TYPES: dict[str, dict[str, dict[str, tuple[type[object], ...]]]] = {
    "TOTALS_ARITHMETIC_V1": {
        "observed": {
            "available_fields": (int,),
            "total_minor": (int,),
            "computed_minor": (int,),
            "delta_minor": (int,),
        },
        "expected": {"tolerance_minor": (int,)},
    },
    "TOTALS_ARITHMETIC_V2": {
        "observed": {
            "available_fields": (int,),
            "total_minor": (int,),
            "computed_minor": (int,),
            "delta_minor": (int,),
            "discount_included_in_subtotal": (bool,),
        },
        "expected": {"tolerance_minor": (int,)},
    },
    "LINE_ITEM_ARITHMETIC_V1": {
        "observed": {
            "ordinal": (int,),
            "line_total_minor": (int,),
            "computed_minor": (int,),
            "delta_minor": (int,),
        },
        "expected": {"tolerance_minor": (int,)},
    },
    "LINE_ITEMS_TO_SUBTOTAL_V1": {
        "observed": {
            "line_count": (int,),
            "lines_with_total": (int,),
            "subtotal_present": (bool,),
            "subtotal_minor": (int,),
            "gross_line_sum_minor": (int,),
            "net_line_sum_minor": (int,),
            "gross_delta_minor": (int,),
            "net_delta_minor": (int,),
        },
        "expected": {"tolerance_minor": (int,)},
    },
    "LINE_ITEMS_TO_SUBTOTAL_V2": {
        "observed": {
            "line_count": (int,),
            "lines_with_total": (int,),
            "subtotal_present": (bool,),
            "subtotal_minor": (int,),
            "gross_line_sum_minor": (int,),
            "net_line_sum_minor": (int,),
            "gross_delta_minor": (int,),
            "net_delta_minor": (int,),
            "receipt_adjusted_net_delta_minor": (int,),
        },
        "expected": {"tolerance_minor": (int,)},
    },
    "SCHEMA_VERSION_V1": {
        "observed": {"schema_version_present": (bool,)},
        "expected": {"required_value": (str,)},
    },
}


def sanitize_finding_values(
    check_code: str,
    section: Literal["observed", "expected"],
    values: object,
) -> dict[str, int | float | bool | str | None] | None:
    """Project stored finding JSON onto the privacy-safe public allowlist."""
    if not isinstance(values, dict):
        return None
    rules = _SAFE_FINDING_FIELD_TYPES.get(check_code, {}).get(section, {})
    sanitized: dict[str, int | float | bool | str | None] = {}
    for key, value in values.items():
        allowed_types = rules.get(key)
        if allowed_types is None:
            continue
        if value is None:
            sanitized[key] = None
        elif type(value) in allowed_types:
            if isinstance(value, str) and (len(value) > 50 or value != "v1"):
                continue
            sanitized[key] = value
    return sanitized or None


# ── Shared primitives ─────────────────────────────────────────────────────────


class AssetInputSchema(BaseModel):
    ordinal: int = Field(ge=1)
    declared_mime_type: str
    byte_size: int = Field(ge=1, le=10_485_760)


class UploadCapabilitySchema(BaseModel):
    asset_id: UUID
    ordinal: int = Field(ge=1)
    upload_url: str = Field(description="Short-lived signed PUT URL — bearer secret, never log")
    method: str = "PUT"
    expires_at: datetime
    allowed_mime_types: list[str]


class AssetSummarySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    asset_id: UUID
    ordinal: int = Field(ge=1)
    upload_status: str
    verified_mime_type: str | None = None
    byte_size: int | None = None


class LineItemSummarySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ordinal: int = Field(ge=1)
    raw_description: str
    normalized_description: str | None = None
    quantity: str | None = None
    unit: str | None = None
    unit_price_decimal: str | None = None
    line_total_minor: int | None = None
    discount_minor: int | None = None
    category_suggestion: str | None = None


class ValidationFindingSummarySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    check_code: str = Field(max_length=100)
    outcome: str = Field(max_length=50)
    rule_version: str | None = Field(default=None, max_length=20)
    observed: dict[str, int | float | bool | str | None] | None = None
    expected: dict[str, int | float | bool | str | None] | None = None

    @model_validator(mode="before")
    @classmethod
    def _sanitize_finding_fields(cls, data: object) -> object:
        """Drop unknown keys and non-scalar values before response validation."""
        if not isinstance(data, dict):
            return data
        sanitized = dict(data)
        check_code = sanitized.get("check_code")
        if not isinstance(check_code, str):
            sanitized["observed"] = None
            sanitized["expected"] = None
            return sanitized
        sanitized["observed"] = sanitize_finding_values(
            check_code, "observed", sanitized.get("observed")
        )
        sanitized["expected"] = sanitize_finding_values(
            check_code, "expected", sanitized.get("expected")
        )
        return sanitized


class RevisionSummarySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    revision_id: UUID | None = None
    source_type: str | None = None
    merchant_normalized: str | None = None
    purchase_datetime: datetime | None = None
    purchase_timezone: str | None = None
    currency: str | None = None
    subtotal_minor: int | None = None
    tax_minor: int | None = None
    tip_minor: int | None = None
    discount_minor: int | None = None
    total_minor: int | None = None
    overall_confidence: float | None = None


class ProvenanceSummarySchema(BaseModel):
    provider: str
    model_id: str
    prompt_version: str
    schema_version: str
    attempt_count: int


# ── Receipt create ─────────────────────────────────────────────────────────────


class CreateReceiptRequest(BaseModel):
    client_submission_key: UUID
    expected_asset_count: int = Field(ge=1, le=10)
    financial_context: str = "personal"
    captured_at: datetime | None = None
    assets: list[AssetInputSchema] = Field(min_length=1, max_length=10)

    @field_validator("financial_context")
    @classmethod
    def validate_financial_context(cls, v: str) -> str:
        allowed = {"personal", "rental_property"}
        if v not in allowed:
            raise ValueError(f"financial_context must be one of {allowed}")
        return v

    @model_validator(mode="after")
    def validate_assets_match_count(self) -> CreateReceiptRequest:
        if len(self.assets) != self.expected_asset_count:
            raise ValueError(
                f"assets length ({len(self.assets)}) must match "
                f"expected_asset_count ({self.expected_asset_count})"
            )
        ordinals = sorted(a.ordinal for a in self.assets)
        expected = list(range(1, len(self.assets) + 1))
        if ordinals != expected:
            raise ValueError("Asset ordinals must be contiguous starting from 1")
        return self


class CreateReceiptResponse(BaseModel):
    receipt_id: UUID
    processing_status: str
    upload_capabilities: list[UploadCapabilitySchema]


# ── Receipt list ──────────────────────────────────────────────────────────────


class ReceiptListItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    receipt_id: UUID
    processing_status: str
    verification_status: str
    financial_context: str
    expected_asset_count: int
    acknowledged_at: datetime | None = None
    created_at: datetime
    deduplication_status: DeduplicationStatus
    canonical_receipt_id: UUID | None = None
    current_revision: RevisionSummarySchema | None = None


class ListReceiptsResponse(BaseModel):
    receipts: list[ReceiptListItemSchema]
    next_cursor: str | None = None


# ── Sprint 2B: Review guidance schemas ────────────────────────────────────────

# PostgreSQL BIGINT upper bound (2^63 − 1). Must be defined before schemas that use it.
_BIGINT_MAX = 9_223_372_036_854_775_807

_DRAFT_PATCH_OPS = Literal[
    "clear_receipt_discount",
    "set_receipt_subtotal",
    "set_receipt_discount",
    "clear_receipt_subtotal",
    "clear_line_discount",
    "set_line_total",
    "remove_line_item",
]
_SAFE_CODE = Annotated[str, Field(max_length=100, pattern=r"^[a-z0-9_]+$")]
_SAFE_EQUATION = Annotated[str, Field(max_length=500)]


class DraftPatchSchema(BaseModel):
    """One allowlisted draft patch operation. Applied client-side only."""

    op: _DRAFT_PATCH_OPS
    ordinal: int | None = Field(default=None, ge=1, le=10_000)
    value: int | None = Field(default=None, ge=0, le=_BIGINT_MAX)


class ReviewCandidateSchema(BaseModel):
    """One deterministic correction proposal from the reconciliation engine."""

    kind: str = Field(max_length=100)
    evidence_band: Literal["strong", "possible", "ambiguous"]
    target_field: str | None = Field(default=None, max_length=100)
    target_item_ordinal: int | None = Field(default=None, ge=1, le=10_000)
    amount_minor: int | None = Field(default=None, ge=0, le=_BIGINT_MAX)
    reason_codes: list[_SAFE_CODE] = Field(max_length=10)
    equations_before: list[_SAFE_EQUATION] = Field(max_length=10)
    equations_after: list[_SAFE_EQUATION] = Field(max_length=10)
    draft_patch: list[DraftPatchSchema] = Field(max_length=5)


class ReviewGuidanceSchema(BaseModel):
    """Deterministic reconciliation guidance for receipts with arithmetic exceptions.

    Contains at most three ranked candidates. No probability percentages;
    evidence bands are strong, possible, or ambiguous only.
    No receipt text or private identifiers — amounts and ordinals only.
    """

    signed_delta_minor: int
    receipt_total_minor: int = Field(ge=0, le=_BIGINT_MAX)
    computed_total_minor: int
    component_equation: str = Field(max_length=500)
    gross_line_sum_minor: int | None = None
    net_line_sum_minor: int | None = None
    subtotal_vs_gross_delta_minor: int | None = None
    subtotal_vs_net_delta_minor: int | None = None
    review_candidates: list[ReviewCandidateSchema] = Field(max_length=3)


# ── Receipt detail ────────────────────────────────────────────────────────────


class ReceiptDetailSchema(ReceiptListItemSchema):
    assets: list[AssetSummarySchema] = Field(default_factory=list)
    line_items: list[LineItemSummarySchema] | None = None
    validation_findings: list[ValidationFindingSummarySchema] | None = None
    safe_error_code: str | None = None
    provenance_summary: ProvenanceSummarySchema | None = None
    review_guidance: ReviewGuidanceSchema | None = None


# ── Finalize ─────────────────────────────────────────────────────────────────


class FinalizeReceiptResponse(BaseModel):
    receipt_id: UUID
    processing_status: str
    acknowledged_at: datetime


# ── Retry processing ──────────────────────────────────────────────────────────


class RetryProcessingResponse(BaseModel):
    receipt_id: UUID
    processing_status: str


# ── Download capability ───────────────────────────────────────────────────────


class DownloadCapabilityResponse(BaseModel):
    download_url: str = Field(description="Short-lived signed GET URL — bearer secret, never log")
    method: str = "GET"
    expires_at: datetime


# ── Human revision ────────────────────────────────────────────────────────────

_CURRENCY_RE = re.compile(r"^[A-Z]{3}$")
_PLAIN_DECIMAL_RE = re.compile(r"^\d+(?:\.\d+)?$")

# NUMERIC(18, 6) column constraints used for quantity and unit_price_decimal.
_NUMERIC_MAX_PRECISION = 18
_NUMERIC_MAX_SCALE = 6


def _validate_nonneg_decimal_str(v: str, field_name: str) -> str:
    """Parse and validate a decimal string: finite, non-negative, within NUMERIC(18,6)."""
    from financial_os.domain.money import parse_decimal_string

    normalized = v.strip()
    if not _PLAIN_DECIMAL_RE.fullmatch(normalized):
        raise ValueError(f"{field_name} must be a plain non-negative decimal string")

    d = parse_decimal_string(normalized, field_name)
    if d is None:
        return normalized  # unreachable in non-None path, satisfies type checker
    if d < 0:
        raise ValueError(f"{field_name} must be non-negative")
    _sign, digits, exp = d.as_tuple()
    # exp is int for finite Decimal (guaranteed by parse_decimal_string is_finite check).
    # The isinstance guard satisfies mypy, which sees exponent as int | Literal['n','N','F'].
    if isinstance(exp, int) and exp < 0 and -exp > _NUMERIC_MAX_SCALE:
        raise ValueError(f"{field_name} has {-exp} decimal places, maximum is {_NUMERIC_MAX_SCALE}")
    integer_digits = max(d.adjusted() + 1, 0)
    if integer_digits > _NUMERIC_MAX_PRECISION - _NUMERIC_MAX_SCALE:
        raise ValueError(
            f"{field_name} exceeds NUMERIC({_NUMERIC_MAX_PRECISION},{_NUMERIC_MAX_SCALE}) range"
        )
    if len(digits) > _NUMERIC_MAX_PRECISION:
        raise ValueError(
            f"{field_name} exceeds NUMERIC({_NUMERIC_MAX_PRECISION},{_NUMERIC_MAX_SCALE}) precision"
        )
    return normalized


class LineItemInputSchema(BaseModel):
    """One line item in a human correction. Ordinals are assigned server-side."""

    description: str = Field(min_length=1, max_length=500)
    normalized_description: str | None = Field(default=None, max_length=500)
    quantity: str | None = Field(default=None, max_length=20)
    unit: str | None = Field(default=None, max_length=50)
    unit_price_decimal: str | None = Field(default=None, max_length=30)
    line_total_minor: int | None = Field(default=None, ge=0, le=_BIGINT_MAX)
    discount_minor: int | None = Field(default=None, ge=0, le=_BIGINT_MAX)
    category_suggestion: str | None = Field(default=None, max_length=100)

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str) -> str:
        normalized = v.strip()
        if not normalized:
            raise ValueError("description must contain non-whitespace text")
        return normalized

    @field_validator("quantity")
    @classmethod
    def validate_quantity_decimal(cls, v: str | None) -> str | None:
        if v is not None:
            return _validate_nonneg_decimal_str(v, "quantity")
        return v

    @field_validator("unit_price_decimal")
    @classmethod
    def validate_unit_price_decimal_str(cls, v: str | None) -> str | None:
        if v is not None:
            return _validate_nonneg_decimal_str(v, "unit_price_decimal")
        return v


class CreateHumanRevisionRequest(BaseModel):
    """Request body for POST /api/v1/receipts/{receipt_id}/human-revisions.

    The client provides a complete corrected snapshot; the server re-numbers
    line items contiguously and validates arithmetic before writing.
    """

    expected_parent_revision_id: UUID
    merchant_normalized: str | None = Field(default=None, max_length=500)
    purchase_datetime: datetime | None = None
    purchase_timezone: str | None = Field(default=None, max_length=100)
    currency: str = Field(min_length=3, max_length=3)
    subtotal_minor: int | None = Field(default=None, ge=0, le=_BIGINT_MAX)
    tax_minor: int | None = Field(default=None, ge=0, le=_BIGINT_MAX)
    tip_minor: int | None = Field(default=None, ge=0, le=_BIGINT_MAX)
    discount_minor: int | None = Field(default=None, ge=0, le=_BIGINT_MAX)
    total_minor: int = Field(ge=0, le=_BIGINT_MAX)
    line_items: list[LineItemInputSchema] = Field(default_factory=list, max_length=200)
    review_disposition: Literal["corrected", "confirmed_as_shown"] = "corrected"

    @field_validator("currency")
    @classmethod
    def validate_currency_code(cls, v: str) -> str:
        if not _CURRENCY_RE.match(v):
            raise ValueError("currency must be a three-letter uppercase ISO 4217 code")
        return v
