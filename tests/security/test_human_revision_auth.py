"""Authorization negative tests for POST /api/v1/receipts/{receipt_id}/human-revisions.

IAM-01 enforcement. Verifies:
- Missing Bearer token → 401 (no private detail in response)
- Malformed / invalid Bearer token → 401
- Authenticated identity NOT in DB allowlist → 403 (service-layer check)
- Owner B accessing owner A's receipt → 404 (opaque; prevents ID enumeration)
- 404 error response contains no receipt content, financial data, or internal IDs

Requires DATABASE_URL env var pointing to a PostgreSQL instance.
All tests are skipped automatically when DATABASE_URL is not set.

Tests in TestMissingTokenReturns401 and TestInvalidTokenReturns401 exercise
the FastAPI dependency layer and work independently of the create_human_revision
service function (which is resolved before the route body runs).

Tests in TestNonOwnerReturns403 and TestCrossReceiptOwnershipRejected exercise
the service-layer ownership check and require create_human_revision to be
implemented by Agent A. Until then, they will fail gracefully with assertion
errors (500 returned instead of the expected 403/404) and serve as
specification tests.
"""

from __future__ import annotations

import base64
import json
import os
import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from financial_os.adapters.extraction.fake import FakeExtractionAdapter
from financial_os.adapters.queue.fake import FakeQueueAdapter
from financial_os.adapters.storage.fake import FakeStorageAdapter
from financial_os.app_factory import create_test_app
from financial_os.auth.deps import get_verified_owner
from financial_os.auth.firebase import VerifiedOwner
from financial_os.config import Settings
from financial_os.models import Base
from financial_os.models.auth import AuthSubject
from financial_os.models.receipt import Receipt

pytestmark = [
    pytest.mark.integration,
    pytest.mark.asyncio(loop_scope="module"),
]

# ── Test identities ──────────────────────────────────────────────────────────

TEST_SETTINGS = Settings(
    environment="test",
    firebase_project_id="",
    gcp_project_id="",
    gcs_evidence_bucket="",
    cloud_tasks_queue_path="",
    worker_oidc_audience="",
    owner_allowlist="",
    pipeline_version="test-pipeline-v1",
)

# Owner A — allowlisted in DB; their receipts are the cross-ownership target
TEST_OWNER_A = VerifiedOwner(
    subject_id="google:test-humanrev-auth-owner-a",
    auth_subject_id="",
    auth_time=9999999999,
)

# Owner B — also allowlisted in DB, but does NOT own owner A's receipts
TEST_OWNER_B = VerifiedOwner(
    subject_id="google:test-humanrev-auth-owner-b",
    auth_subject_id="",
    auth_time=9999999999,
)

# Non-owner — a valid VerifiedOwner object but NOT present in auth_subjects
TEST_NON_OWNER = VerifiedOwner(
    subject_id="google:test-humanrev-auth-nonowner",
    auth_subject_id="",
    auth_time=9999999999,
)


def _hr_body(parent_revision_id: uuid.UUID | None = None) -> dict:
    """Minimal arithmetically valid CreateHumanRevisionRequest body."""
    return {
        "expected_parent_revision_id": str(parent_revision_id or uuid.uuid4()),
        "currency": "USD",
        "total_minor": 1099,
        "subtotal_minor": 999,
        "tax_minor": 100,
        "line_items": [],
    }


# ── Module-scoped DB and app fixtures ─────────────────────────────────────────


@pytest.fixture(scope="module")
def db_url_module() -> str:
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        pytest.skip("DATABASE_URL not set — skipping integration tests")
    return url


@pytest_asyncio.fixture(scope="module")
async def test_engine(db_url_module: str):
    engine = create_async_engine(db_url_module, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="module")
async def session_factory(test_engine):
    factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        session.add(
            AuthSubject(
                provider="google",
                provider_subject=TEST_OWNER_A.subject_id,
                allowlisted=True,
            )
        )
        session.add(
            AuthSubject(
                provider="google",
                provider_subject=TEST_OWNER_B.subject_id,
                allowlisted=True,
            )
        )
        await session.commit()
    return factory


@pytest_asyncio.fixture(scope="module")
async def base_app_no_override(session_factory):
    """App with NO dependency override — exercises the real FastAPI auth path.

    Used by auth dependency tests (missing token, invalid token) where the
    override must NOT be present so the actual HTTPBearer security scheme fires.
    """
    storage = FakeStorageAdapter()
    queue = FakeQueueAdapter()
    extractor = FakeExtractionAdapter()

    app = create_test_app(
        settings=TEST_SETTINGS,
        storage=storage,
        queue=queue,
        extractor=extractor,
        session_factory=session_factory,
    )
    async with app.router.lifespan_context(app):
        yield app


@pytest_asyncio.fixture(scope="module")
async def owner_a_receipt_id(session_factory) -> uuid.UUID:
    """Create a reserved receipt owned by owner A; return its ID.

    A reserved receipt is sufficient for auth tests because the ownership
    check (Receipt.owner_id == owner_id) is enforced before the state check.
    """
    async with session_factory() as session:
        result = await session.execute(
            select(AuthSubject).where(AuthSubject.provider_subject == TEST_OWNER_A.subject_id)
        )
        owner_a_subject = result.scalar_one()

        receipt = Receipt(
            id=uuid.uuid4(),
            owner_id=owner_a_subject.id,
            client_submission_id=uuid.uuid4(),
            processing_status="reserved",
            verification_status="unreviewed",
            expected_asset_count=1,
            current_revision_id=None,
            row_version=0,
        )
        session.add(receipt)
        await session.commit()
        return receipt.id


# ── Test classes ──────────────────────────────────────────────────────────────


class TestMissingTokenReturns401:
    """IAM-01: absent Authorization header must be rejected with 401.

    These tests exercise the FastAPI HTTPBearer dependency before any
    service code runs. They work independently of create_human_revision.
    """

    async def test_missing_token_returns_401(
        self,
        base_app_no_override,
        owner_a_receipt_id: uuid.UUID,
    ) -> None:
        async with AsyncClient(
            transport=ASGITransport(app=base_app_no_override),
            base_url="http://test",
        ) as client:
            resp = await client.post(
                f"/api/v1/receipts/{owner_a_receipt_id}/human-revisions",
                # Intentionally no Authorization header
            )
        assert resp.status_code == 401, f"Missing token: expected 401, got {resp.status_code}"

    async def test_missing_token_response_leaks_no_private_detail(
        self,
        base_app_no_override,
        owner_a_receipt_id: uuid.UUID,
    ) -> None:
        """401 response must contain no authentication internals (IAM-01, LOG-01)."""
        async with AsyncClient(
            transport=ASGITransport(app=base_app_no_override),
            base_url="http://test",
        ) as client:
            resp = await client.post(
                f"/api/v1/receipts/{owner_a_receipt_id}/human-revisions",
            )
        body = resp.text.lower()
        forbidden = [
            "password",
            "secret",
            "token",
            "allowlist",
            "subject",
            "stack",
            "traceback",
            "exception",
            "merchant",
        ]
        for word in forbidden:
            assert word not in body, f"401 response body contains sensitive word: {word!r}"


class TestInvalidTokenReturns401:
    """IAM-01: malformed or cryptographically invalid Bearer tokens → 401.

    These tests exercise the real verify_owner_token path. They work
    independently of create_human_revision.
    """

    async def test_malformed_bearer_returns_401(
        self,
        base_app_no_override,
        owner_a_receipt_id: uuid.UUID,
    ) -> None:
        async with AsyncClient(
            transport=ASGITransport(app=base_app_no_override),
            base_url="http://test",
        ) as client:
            resp = await client.post(
                f"/api/v1/receipts/{owner_a_receipt_id}/human-revisions",
                headers={"Authorization": "Bearer not-a-real-jwt"},
            )
        assert resp.status_code == 401, f"Malformed token: expected 401, got {resp.status_code}"

    async def test_structurally_plausible_but_invalid_jwt_returns_401(
        self,
        base_app_no_override,
        owner_a_receipt_id: uuid.UUID,
    ) -> None:
        """Structural JWT shape with bad signature → 401 (not 400 or 500)."""

        def encode_segment(value: dict[str, object]) -> str:
            return (
                base64.urlsafe_b64encode(json.dumps(value, separators=(",", ":")).encode())
                .rstrip(b"=")
                .decode()
            )

        fake_jwt = ".".join(
            (
                encode_segment({"alg": "RS256", "typ": "JWT"}),
                encode_segment({"sub": "synthetic-test-subject", "exp": 1}),
                "invalid-signature",
            )
        )
        async with AsyncClient(
            transport=ASGITransport(app=base_app_no_override),
            base_url="http://test",
        ) as client:
            resp = await client.post(
                f"/api/v1/receipts/{owner_a_receipt_id}/human-revisions",
                headers={"Authorization": f"Bearer {fake_jwt}"},
            )
        assert resp.status_code == 401, f"Invalid JWT: expected 401, got {resp.status_code}"

    async def test_empty_bearer_value_returns_401(
        self,
        base_app_no_override,
        owner_a_receipt_id: uuid.UUID,
    ) -> None:
        async with AsyncClient(
            transport=ASGITransport(app=base_app_no_override),
            base_url="http://test",
        ) as client:
            resp = await client.post(
                f"/api/v1/receipts/{owner_a_receipt_id}/human-revisions",
                headers={"Authorization": "Bearer "},
            )
        assert resp.status_code == 401, f"Empty bearer: expected 401, got {resp.status_code}"


class TestNonOwnerReturns403:
    """IAM-01: authenticated identity not in DB auth_subjects → 403.

    _resolve_owner_id raises ForbiddenError when the provider_subject is absent
    from auth_subjects (or not allowlisted). The response must be 403 and must
    not reveal any allowlist, DB structure, or receipt content.

    NOTE: Requires create_human_revision to be implemented by Agent A.
    Until then these tests will fail with 500 instead of 403.
    """

    async def test_non_owner_returns_403(
        self,
        session_factory,
        owner_a_receipt_id: uuid.UUID,
    ) -> None:
        """Subject absent from auth_subjects → ForbiddenError from _resolve_owner_id."""
        storage = FakeStorageAdapter()
        queue = FakeQueueAdapter()
        extractor = FakeExtractionAdapter()

        app = create_test_app(
            settings=TEST_SETTINGS,
            storage=storage,
            queue=queue,
            extractor=extractor,
            session_factory=session_factory,
        )
        # Inject subject that does NOT exist in auth_subjects
        app.dependency_overrides[get_verified_owner] = lambda: TEST_NON_OWNER

        async with app.router.lifespan_context(app):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.post(
                    f"/api/v1/receipts/{owner_a_receipt_id}/human-revisions",
                    json=_hr_body(),
                )

        assert resp.status_code == 403, (
            f"Non-DB subject: expected 403, got {resp.status_code}. "
            "Requires create_human_revision service function to be implemented."
        )

    async def test_non_owner_403_contains_no_private_detail(
        self,
        session_factory,
        owner_a_receipt_id: uuid.UUID,
    ) -> None:
        """403 response must not reveal allowlist membership or DB structure (LOG-01)."""
        storage = FakeStorageAdapter()
        queue = FakeQueueAdapter()
        extractor = FakeExtractionAdapter()

        app = create_test_app(
            settings=TEST_SETTINGS,
            storage=storage,
            queue=queue,
            extractor=extractor,
            session_factory=session_factory,
        )
        app.dependency_overrides[get_verified_owner] = lambda: TEST_NON_OWNER

        async with app.router.lifespan_context(app):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.post(
                    f"/api/v1/receipts/{owner_a_receipt_id}/human-revisions",
                    json=_hr_body(),
                )

        body = resp.text.lower()
        forbidden = [
            "allowlist",
            "subject",
            "email",
            "owner_id",
            "stack",
            "traceback",
            "exception",
            "merchant",
        ]
        for word in forbidden:
            assert word not in body, f"403 response leaks sensitive word: {word!r}"


class TestCrossReceiptOwnershipRejected:
    """IAM-01: owner B cannot access owner A's receipts; the error is an opaque 404.

    The receipt lookup uses WHERE receipt_id = X AND owner_id = owner_B_id. When
    the receipt exists but belongs to owner A, the query returns nothing. The
    service raises NotFoundError → 404. This prevents a valid authenticated caller
    from enumerating which receipt IDs exist for other owners.

    NOTE: Requires create_human_revision to be implemented by Agent A.
    Until then these tests will fail with 500 instead of 404.
    """

    async def test_cross_receipt_access_returns_404(
        self,
        session_factory,
        owner_a_receipt_id: uuid.UUID,
    ) -> None:
        """Owner B (allowlisted, not owner) accessing owner A's receipt → 404."""
        storage = FakeStorageAdapter()
        queue = FakeQueueAdapter()
        extractor = FakeExtractionAdapter()

        app = create_test_app(
            settings=TEST_SETTINGS,
            storage=storage,
            queue=queue,
            extractor=extractor,
            session_factory=session_factory,
        )
        # Inject owner B — allowlisted but does not own the receipt
        app.dependency_overrides[get_verified_owner] = lambda: TEST_OWNER_B

        async with app.router.lifespan_context(app):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.post(
                    f"/api/v1/receipts/{owner_a_receipt_id}/human-revisions",
                    json=_hr_body(),
                )

        # 404: indistinguishable from "does not exist" to prevent receipt enumeration
        assert resp.status_code == 404, (
            f"Cross-ownership: expected 404 (opaque), got {resp.status_code}. "
            "Requires create_human_revision service function to be implemented."
        )

    async def test_unauthorized_receipt_id_is_opaque(
        self,
        session_factory,
        owner_a_receipt_id: uuid.UUID,
    ) -> None:
        """The 404 response must contain no receipt content, financial data, or IDs."""
        storage = FakeStorageAdapter()
        queue = FakeQueueAdapter()
        extractor = FakeExtractionAdapter()

        app = create_test_app(
            settings=TEST_SETTINGS,
            storage=storage,
            queue=queue,
            extractor=extractor,
            session_factory=session_factory,
        )
        app.dependency_overrides[get_verified_owner] = lambda: TEST_OWNER_B

        async with app.router.lifespan_context(app):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.post(
                    f"/api/v1/receipts/{owner_a_receipt_id}/human-revisions",
                    json=_hr_body(),
                )

        assert resp.status_code == 404

        body = resp.text.lower()
        # Must not contain financial data from the request or any receipt internals
        forbidden_patterns = [
            "merchant",
            "owner_id",
            "allowlist",
            "traceback",
            "stack",
            "exception",
            str(owner_a_receipt_id).lower(),
        ]
        for pattern in forbidden_patterns:
            assert pattern not in body, f"404 response leaks sensitive content: {pattern!r}"

        # Must return the generic, stable "Receipt not found." message
        data = resp.json()
        assert data.get("message") == "Receipt not found.", (
            f"Expected generic not-found message, got: {data.get('message')!r}"
        )
        assert data.get("error_code") == "RECEIPT_NOT_FOUND", (
            f"Expected RECEIPT_NOT_FOUND, got: {data.get('error_code')!r}"
        )
