"""Test-mode app factory — creates a FastAPI app with injectable adapters.

This module is used by the test suite to inject fake adapters without
going through the lifespan context (which requires real GCP credentials).

Never used in production; production always uses apps/api/main.py.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from financial_os.adapters.extraction.base import ExtractionAdapter
from financial_os.adapters.queue.base import QueueAdapter
from financial_os.adapters.storage.base import StorageAdapter
from financial_os.config import Settings
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
from financial_os.routers import health, receipts, search, worker


def create_test_app(
    settings: Settings,
    storage: StorageAdapter,
    queue: QueueAdapter,
    extractor: ExtractionAdapter,
    session_factory: async_sessionmaker[AsyncSession] | None = None,
) -> FastAPI:
    """Create a FastAPI app with the given adapters for testing."""

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        app.state.settings = settings
        app.state.storage = storage
        app.state.queue = queue
        app.state.extractor = extractor

        if session_factory is None:
            raise ValueError(
                "session_factory is required for create_test_app. "
                "Pass a real async_sessionmaker or skip the test if DATABASE_URL is not set."
            )
        app.state.session_factory = session_factory

        yield

    app = FastAPI(title="Financial OS (Test)", lifespan=lifespan)
    app.state.settings = settings  # also set early for dependency overrides

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

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
    async def domain_handler(request: Request, exc: FinancialOsError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.http_status,
            content={"error_code": exc.safe_error_code, "message": exc.message},
        )

    app.include_router(health.router)
    app.include_router(receipts.router)
    app.include_router(search.router)
    app.include_router(worker.router)

    return app
