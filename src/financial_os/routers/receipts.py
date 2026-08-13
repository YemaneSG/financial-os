"""Public receipt routes — /api/v1/receipts.

All routes require Firebase Bearer token for the allowlisted owner (IAM-01).
Upload capabilities in responses are bearer secrets — never logged (OBJ-02, LOG-01).
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Query, Request, Response

from financial_os import services
from financial_os.auth.deps import OwnerDep
from financial_os.domain.errors import (
    ForbiddenError,
    ValidationError,
)
from financial_os.schemas.receipt import (
    CreateReceiptRequest,
    CreateReceiptResponse,
    DownloadCapabilityResponse,
    FinalizeReceiptResponse,
    ListReceiptsResponse,
    ReceiptDetailSchema,
    RetryProcessingResponse,
)

router = APIRouter(prefix="/api/v1", tags=["receipts"])


def _correlation_id(request: Request) -> str:
    return request.headers.get("X-Request-ID", str(uuid.uuid4()))


@router.post("/receipts", response_model=CreateReceiptResponse)
async def create_receipt(
    body: CreateReceiptRequest,
    request: Request,
    owner: OwnerDep,
    response: Response,
) -> CreateReceiptResponse:
    """Create a receipt and obtain upload capabilities (idempotent A-01)."""
    correlation_id = _correlation_id(request)
    async with request.app.state.session_factory() as session:
        try:
            result, http_status = await services.receipt.create_receipt(
                session=session,
                owner=owner,
                request=body,
                storage=request.app.state.storage,
                settings=request.app.state.settings,
                correlation_id=correlation_id,
            )
            await session.commit()
        except (ForbiddenError, ValidationError):
            await session.rollback()
            raise

    response.status_code = http_status
    return result


@router.get("/receipts", response_model=ListReceiptsResponse)
async def list_receipts(
    request: Request,
    owner: OwnerDep,
    cursor: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=50),
) -> ListReceiptsResponse:
    """List receipts for the authenticated owner, newest first."""
    async with request.app.state.session_factory() as session:
        return await services.receipt.list_receipts(
            session=session,
            owner=owner,
            cursor=cursor,
            limit=limit,
            settings=request.app.state.settings,
        )


@router.get("/receipts/{receipt_id}", response_model=ReceiptDetailSchema)
async def get_receipt(
    receipt_id: uuid.UUID,
    request: Request,
    owner: OwnerDep,
) -> ReceiptDetailSchema:
    """Get full receipt detail including assets, line items, and validation findings."""
    async with request.app.state.session_factory() as session:
        return await services.receipt.get_receipt(
            session=session,
            owner=owner,
            receipt_id=receipt_id,
            settings=request.app.state.settings,
        )


@router.post("/receipts/{receipt_id}/finalize", response_model=FinalizeReceiptResponse)
async def finalize_receipt(
    receipt_id: uuid.UUID,
    request: Request,
    owner: OwnerDep,
) -> FinalizeReceiptResponse:
    """Verify evidence and durably acknowledge the receipt (API-03, OBJ-03)."""
    correlation_id = _correlation_id(request)
    async with request.app.state.session_factory() as session:
        result = await services.receipt.finalize_receipt(
            session=session,
            owner=owner,
            receipt_id=receipt_id,
            storage=request.app.state.storage,
            queue=request.app.state.queue,
            settings=request.app.state.settings,
            correlation_id=correlation_id,
        )
        await session.commit()
    return result


@router.post(
    "/receipts/{receipt_id}/retry-processing",
    response_model=RetryProcessingResponse,
)
async def retry_processing(
    receipt_id: uuid.UUID,
    request: Request,
    owner: OwnerDep,
) -> RetryProcessingResponse:
    """Re-enqueue a retryable_failed receipt for extraction."""
    correlation_id = _correlation_id(request)
    async with request.app.state.session_factory() as session:
        result = await services.receipt.retry_processing(
            session=session,
            owner=owner,
            receipt_id=receipt_id,
            queue=request.app.state.queue,
            settings=request.app.state.settings,
            correlation_id=correlation_id,
        )
        await session.commit()
    return result


@router.post(
    "/receipts/{receipt_id}/assets/{asset_id}/download",
    response_model=DownloadCapabilityResponse,
)
async def get_asset_download_capability(
    receipt_id: uuid.UUID,
    asset_id: uuid.UUID,
    request: Request,
    owner: OwnerDep,
) -> DownloadCapabilityResponse:
    """Obtain a short-lived download capability for a receipt asset (OBJ-02, S-03)."""
    async with request.app.state.session_factory() as session:
        return await services.receipt.get_asset_download_capability(
            session=session,
            owner=owner,
            receipt_id=receipt_id,
            asset_id=asset_id,
            storage=request.app.state.storage,
            settings=request.app.state.settings,
        )
