"""Financial OS FastAPI application entry point.

Initialises all adapters and dependencies at startup via the lifespan context.
All secrets come from environment variables (Secret Manager in production).
No long-lived service-account keys; no credential values are logged.
"""

from __future__ import annotations

import logging
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from financial_os.adapters.extraction.base import ExtractionAdapter
from financial_os.adapters.queue.base import QueueAdapter
from financial_os.adapters.storage.base import StorageAdapter
from financial_os.config import Settings, get_settings
from financial_os.database import build_engine, build_session_factory
from financial_os.domain.errors import (
    AssetNotFoundError,
    ConflictError,
    EvidenceIncompleteError,
    FinancialOsError,
    ForbiddenError,
    NotFoundError,
    RetryNotPermittedError,
    UnauthorizedError,
    ValidationError,
)
from financial_os.routers import health, receipts, worker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Initialise and tear down all stateful adapters."""
    settings: Settings = app.state.settings

    # Database
    database = build_engine(settings)
    session_factory = build_session_factory(database.engine)
    app.state.session_factory = session_factory

    # Firebase Admin SDK (skip in test mode when firebase_project_id is blank)
    if settings.firebase_project_id:
        try:
            from financial_os.auth.firebase import _init_firebase

            _init_firebase(settings.firebase_project_id)
        except Exception:
            logger.warning("Firebase Admin SDK init failed — auth will not work in production")

    # Storage adapter
    if settings.gcs_evidence_bucket and settings.environment != "test":
        from financial_os.adapters.storage.gcs import GCSStorageAdapter

        storage: StorageAdapter = GCSStorageAdapter(bucket_name=settings.gcs_evidence_bucket)
    else:
        from financial_os.adapters.storage.fake import FakeStorageAdapter

        storage = FakeStorageAdapter()

    app.state.storage = storage

    # Queue adapter
    if settings.cloud_tasks_queue_path and settings.environment != "test":
        from financial_os.adapters.queue.cloud_tasks import CloudTasksQueueAdapter

        queue: QueueAdapter = CloudTasksQueueAdapter(
            queue_path=settings.cloud_tasks_queue_path,
            worker_url_template=settings.cloud_tasks_worker_url,
            service_account_email=settings.cloud_tasks_service_account_email,
            project_id=settings.gcp_project_id,
        )
    else:
        from financial_os.adapters.queue.fake import FakeQueueAdapter

        queue = FakeQueueAdapter()

    app.state.queue = queue

    # Extraction adapter
    if settings.gcp_project_id and settings.environment not in ("test", "development"):
        from financial_os.adapters.extraction.vertex import VertexExtractionAdapter

        extractor: ExtractionAdapter = VertexExtractionAdapter(
            project_id=settings.gcp_project_id,
            location=settings.vertex_location,
            model_id=settings.vertex_model_id,
            prompt_version=settings.extraction_prompt_version,
            schema_version=settings.extraction_schema_version,
        )
    else:
        from financial_os.adapters.extraction.fake import FakeExtractionAdapter

        extractor = FakeExtractionAdapter()

    app.state.extractor = extractor

    logger.info(
        "Financial OS API started",
        extra={
            "environment": settings.environment,
            "pipeline_version": settings.pipeline_version,
        },
    )

    yield

    # Cleanup
    await database.close()
    logger.info("Financial OS API shutdown complete")


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""
    s = settings or get_settings()

    app = FastAPI(
        title="Financial OS API",
        version="1.0.0",
        docs_url=None,  # Disable Swagger UI in production
        redoc_url=None,
        openapi_url=None if s.is_production else "/openapi.json",
        lifespan=lifespan,
    )

    app.state.settings = s

    # CORS (NET-02): restrict to deployed application origin only.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[s.cors_allowed_origin],
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    )

    # Exception handlers — privacy-safe error responses.
    @app.exception_handler(NotFoundError)
    @app.exception_handler(AssetNotFoundError)
    async def not_found_handler(request: Request, exc: FinancialOsError) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={"error_code": exc.safe_error_code, "message": exc.message},
        )

    @app.exception_handler(UnauthorizedError)
    async def unauthorized_handler(request: Request, exc: FinancialOsError) -> JSONResponse:
        return JSONResponse(
            status_code=401,
            content={"error_code": exc.safe_error_code, "message": exc.message},
        )

    @app.exception_handler(ForbiddenError)
    async def forbidden_handler(request: Request, exc: FinancialOsError) -> JSONResponse:
        return JSONResponse(
            status_code=403,
            content={"error_code": exc.safe_error_code, "message": exc.message},
        )

    @app.exception_handler(EvidenceIncompleteError)
    @app.exception_handler(ValidationError)
    async def unprocessable_handler(request: Request, exc: FinancialOsError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={"error_code": exc.safe_error_code, "message": exc.message},
        )

    @app.exception_handler(ConflictError)
    @app.exception_handler(RetryNotPermittedError)
    async def conflict_handler(request: Request, exc: FinancialOsError) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={"error_code": exc.safe_error_code, "message": exc.message},
        )

    @app.exception_handler(FinancialOsError)
    async def generic_domain_handler(request: Request, exc: FinancialOsError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.http_status,
            content={"error_code": exc.safe_error_code, "message": exc.message},
        )

    # Include routers.
    app.include_router(health.router)
    app.include_router(receipts.router)
    app.include_router(worker.router)

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", "8080"))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",  # noqa: S104 — required for container deployment
        port=port,
        log_level="info",
    )
