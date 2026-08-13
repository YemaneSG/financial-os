"""Internal worker routes — /internal/v1/.

Authenticated by Cloud Tasks OIDC tokens (QUE-01).
Not reachable from the public internet (NET-01).
Always return 200; non-200 causes Cloud Tasks to retry.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Request

from financial_os import services
from financial_os.auth.deps import require_internal_oidc
from financial_os.schemas.worker import (
    ProcessReceiptRequest,
    ProcessReceiptResponse,
    ReconcileProcessingResponse,
)

router = APIRouter(
    prefix="/internal/v1",
    tags=["worker"],
    dependencies=[Depends(require_internal_oidc)],
)


def _correlation_id(request: Request) -> str:
    return request.headers.get("X-CloudTasks-TaskName", str(uuid.uuid4()))


@router.post(
    "/receipts/{receipt_id}/process",
    response_model=ProcessReceiptResponse,
)
async def process_receipt(
    receipt_id: uuid.UUID,
    body: ProcessReceiptRequest,
    request: Request,
) -> ProcessReceiptResponse:
    """Execute extraction and validation for one receipt (Cloud Tasks delivery only)."""
    correlation_id = _correlation_id(request)
    async with request.app.state.session_factory() as session:
        result = await services.worker.process_receipt(
            session=session,
            receipt_id=receipt_id,
            pipeline_version=body.pipeline_version,
            attempt_number=body.attempt_number,
            task_name=body.task_name,
            extractor=request.app.state.extractor,
            storage=request.app.state.storage,
            settings=request.app.state.settings,
            correlation_id=correlation_id,
        )
        await session.commit()
    return result


@router.post("/reconcile-processing", response_model=ReconcileProcessingResponse)
async def reconcile_processing(
    request: Request,
) -> ReconcileProcessingResponse:
    """Stale-work reconciliation sweep (Cloud Scheduler delivery only)."""
    correlation_id = _correlation_id(request)
    async with request.app.state.session_factory() as session:
        result = await services.worker.reconcile_processing(
            session=session,
            queue=request.app.state.queue,
            settings=request.app.state.settings,
            correlation_id=correlation_id,
        )
        await session.commit()
    return result
