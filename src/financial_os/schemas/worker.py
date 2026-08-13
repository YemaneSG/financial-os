"""Pydantic schemas for /internal/v1/ worker routes."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class ProcessReceiptRequest(BaseModel):
    pipeline_version: str
    attempt_number: int = Field(ge=1)
    task_name: str | None = None


class ProcessReceiptResponse(BaseModel):
    receipt_id: UUID
    outcome: str  # succeeded | retryable_failed | terminal_failed | no_op
    safe_error_code: str | None = None


class ReconcileProcessingResponse(BaseModel):
    evaluated_count: int
    re_enqueued_count: int
    flagged_count: int
