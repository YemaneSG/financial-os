"""Health probe routes — /health/live and /health/ready.

No authentication required; these are used by Cloud Run liveness/readiness checks.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from financial_os.schemas.health import LivenessResponse

router = APIRouter(tags=["health"])
logger = logging.getLogger(__name__)


@router.get("/health/live", response_model=LivenessResponse)
async def health_live() -> LivenessResponse:
    """Liveness probe — process is running."""
    return LivenessResponse(status="ok")


@router.get("/health/ready")
async def health_ready(request: Request) -> JSONResponse:
    """Readiness probe — database, storage, and queue are reachable."""
    storage = request.app.state.storage
    queue = request.app.state.queue

    db_ok = False
    storage_ok = False
    queue_ok = False

    try:
        from sqlalchemy import text

        async with request.app.state.session_factory() as session:
            await session.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        logger.warning("Readiness database check failed")

    try:
        storage_ok = await storage.is_healthy()
    except Exception:
        logger.warning("Readiness storage check failed")

    try:
        queue_ok = await queue.is_healthy()
    except Exception:
        logger.warning("Readiness queue check failed")

    all_ok = db_ok and storage_ok and queue_ok
    status_code = 200 if all_ok else 503
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ok" if all_ok else "degraded",
            "checks": {
                "database": db_ok,
                "storage": storage_ok,
                "queue": queue_ok,
            },
        },
    )
