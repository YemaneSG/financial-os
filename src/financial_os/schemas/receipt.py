"""Pydantic schemas for the /api/v1/receipts routes.

All schemas match the OpenAPI contract in contracts/openapi.yaml exactly.
Never include signed URLs, auth tokens, or receipt content in error fields.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

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

    check_code: str
    outcome: str
    rule_version: str | None = None


class RevisionSummarySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    revision_id: UUID | None = None
    source_type: str | None = None
    merchant_normalized: str | None = None
    purchase_datetime: datetime | None = None
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
    current_revision: RevisionSummarySchema | None = None


class ListReceiptsResponse(BaseModel):
    receipts: list[ReceiptListItemSchema]
    next_cursor: str | None = None


# ── Receipt detail ────────────────────────────────────────────────────────────


class ReceiptDetailSchema(ReceiptListItemSchema):
    assets: list[AssetSummarySchema] = Field(default_factory=list)
    line_items: list[LineItemSummarySchema] | None = None
    validation_findings: list[ValidationFindingSummarySchema] | None = None
    safe_error_code: str | None = None
    provenance_summary: ProvenanceSummarySchema | None = None


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
