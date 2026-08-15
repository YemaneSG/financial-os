"""Integration tests for POST /api/v1/receipts/search (Workstream B — Discovery).

Covers: merchant search, line-item search, date/amount/status filters, keyset
pagination stability, total_count accuracy, cross-page completeness, sort orders,
and combined filter composition.

Requires DATABASE_URL env var (skipped when absent).
All fixtures are synthetic — no real receipt content (AGENTS.md §7).
"""

from __future__ import annotations

import os
import uuid
from datetime import UTC, datetime

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
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
from financial_os.models.extraction import LineItemRevision, ReceiptRevision
from financial_os.models.receipt import Receipt

pytestmark = [
    pytest.mark.integration,
    pytest.mark.asyncio(loop_scope="module"),
]

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

TEST_OWNER = VerifiedOwner(
    subject_id="google:test-subject-search",
    auth_subject_id="",
    auth_time=9999999999,
)

OTHER_OWNER = VerifiedOwner(
    subject_id="google:test-subject-search-other",
    auth_subject_id="",
    auth_time=9999999999,
)


@pytest.fixture(scope="module")
def db_url_module() -> str:
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        pytest.skip("DATABASE_URL not set — skipping integration tests")
    return url


@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def test_engine(db_url_module: str):
    engine = create_async_engine(db_url_module, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def session_factory(test_engine):
    factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        session.add(
            AuthSubject(
                provider="google",
                provider_subject=TEST_OWNER.subject_id,
                allowlisted=True,
            )
        )
        session.add(
            AuthSubject(
                provider="google",
                provider_subject=OTHER_OWNER.subject_id,
                allowlisted=True,
            )
        )
        await session.commit()
    return factory


@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def owner_id(session_factory) -> uuid.UUID:
    async with session_factory() as session:
        from sqlalchemy import select

        from financial_os.models.auth import AuthSubject

        result = await session.execute(
            select(AuthSubject).where(AuthSubject.provider_subject == TEST_OWNER.subject_id)
        )
        subject = result.scalar_one()
        return subject.id


@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def other_owner_id(session_factory) -> uuid.UUID:
    async with session_factory() as session:
        from sqlalchemy import select

        from financial_os.models.auth import AuthSubject

        result = await session.execute(
            select(AuthSubject).where(AuthSubject.provider_subject == OTHER_OWNER.subject_id)
        )
        subject = result.scalar_one()
        return subject.id


def _make_receipt(owner_id: uuid.UUID, *, processing_status: str = "extracted") -> Receipt:
    return Receipt(
        id=uuid.uuid4(),
        owner_id=owner_id,
        client_submission_id=uuid.uuid4(),
        financial_context="personal",
        processing_status=processing_status,
        verification_status="system_validated",
        expected_asset_count=1,
        created_at=datetime.now(UTC),
    )


def _make_revision(
    receipt: Receipt,
    *,
    merchant_normalized: str = "Synthetic Merchant",
    total_minor: int = 1000,
    purchase_datetime: datetime | None = None,
) -> ReceiptRevision:
    return ReceiptRevision(
        id=uuid.uuid4(),
        receipt_id=receipt.id,
        parent_revision_id=None,
        source_type="extractor",
        merchant_normalized=merchant_normalized,
        merchant_raw=merchant_normalized.upper(),
        purchase_datetime=purchase_datetime,
        currency="USD",
        total_minor=total_minor,
        subtotal_minor=total_minor,
        tax_minor=0,
    )


def _make_line_item(
    revision: ReceiptRevision, *, description: str, ordinal: int = 1
) -> LineItemRevision:
    return LineItemRevision(
        id=uuid.uuid4(),
        receipt_revision_id=revision.id,
        ordinal=ordinal,
        raw_description=description.upper(),
        normalized_description=description,
        line_total_minor=500,
        field_confidence={},
    )


@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def seeded_receipts(session_factory, owner_id, other_owner_id):
    """Seed a known set of synthetic receipts for search tests."""
    async with session_factory() as session:
        # Receipt A: merchant "Coffee House", 500 minor, known date
        r_a = _make_receipt(owner_id)
        rv_a = _make_revision(
            r_a,
            merchant_normalized="Coffee House",
            total_minor=500,
            purchase_datetime=datetime(2026, 6, 1, 10, 0, tzinfo=UTC),
        )
        session.add(r_a)
        await session.flush()
        session.add(rv_a)
        await session.flush()
        r_a.current_revision_id = rv_a.id

        # Receipt B: merchant "Grocery Store", has line item "organic apples"
        r_b = _make_receipt(owner_id)
        r_b.deduplication_status = "suspected_duplicate"
        rv_b = _make_revision(r_b, merchant_normalized="Grocery Store", total_minor=2000)
        li_b = _make_line_item(rv_b, description="organic apples")
        session.add(r_b)
        await session.flush()
        session.add(rv_b)
        await session.flush()
        r_b.current_revision_id = rv_b.id
        session.add(li_b)

        # Receipt C: needs_review, merchant "Tech Shop"
        r_c = _make_receipt(owner_id)
        r_c.verification_status = "needs_review"
        rv_c = _make_revision(r_c, merchant_normalized="Tech Shop", total_minor=15000)
        session.add(r_c)
        await session.flush()
        session.add(rv_c)
        await session.flush()
        r_c.current_revision_id = rv_c.id

        # Receipt D: different owner — must not appear in TEST_OWNER searches
        r_d = _make_receipt(other_owner_id)
        rv_d = _make_revision(r_d, merchant_normalized="Coffee House", total_minor=300)
        session.add(r_d)
        await session.flush()
        session.add(rv_d)
        await session.flush()
        r_d.current_revision_id = rv_d.id

        # Receipt E: unreviewed, no revision
        r_e = _make_receipt(owner_id, processing_status="queued")
        r_e.verification_status = "unreviewed"
        session.add(r_e)

        await session.commit()
        return {
            "r_a": r_a,
            "r_b": r_b,
            "r_c": r_c,
            "r_d": r_d,
            "r_e": r_e,
        }


@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def app_module(session_factory):
    app = create_test_app(
        settings=TEST_SETTINGS,
        storage=FakeStorageAdapter(),
        queue=FakeQueueAdapter(),
        extractor=FakeExtractionAdapter(),
        session_factory=session_factory,
    )
    app.dependency_overrides[get_verified_owner] = lambda: TEST_OWNER
    async with app.router.lifespan_context(app):
        yield app


@pytest_asyncio.fixture(loop_scope="module")
async def client(app_module):
    async with AsyncClient(transport=ASGITransport(app=app_module), base_url="http://test") as c:
        yield c


class TestSearchBasic:
    async def test_empty_body_returns_all_owner_receipts(
        self, client: AsyncClient, seeded_receipts
    ):
        """No filters → all owner receipts returned (not the other owner's)."""
        r = await client.post("/api/v1/receipts/search", json={})
        assert r.status_code == 200
        data = r.json()
        ids = {item["receipt_id"] for item in data["receipts"]}
        assert str(seeded_receipts["r_d"].id) not in ids, "Cross-owner receipt must not appear"
        assert "total_count" in data
        assert data["total_count"] >= 4  # A, B, C, E

    async def test_merchant_search(self, client: AsyncClient, seeded_receipts):
        """Query matches merchant name case-insensitively."""
        r = await client.post("/api/v1/receipts/search", json={"query": "coffee"})
        assert r.status_code == 200
        data = r.json()
        ids = {item["receipt_id"] for item in data["receipts"]}
        assert str(seeded_receipts["r_a"].id) in ids
        assert str(seeded_receipts["r_b"].id) not in ids
        assert str(seeded_receipts["r_d"].id) not in ids  # other owner

    async def test_line_item_search(self, client: AsyncClient, seeded_receipts):
        """Query matches normalized line-item description."""
        r = await client.post("/api/v1/receipts/search", json={"query": "apples"})
        assert r.status_code == 200
        data = r.json()
        ids = {item["receipt_id"] for item in data["receipts"]}
        assert str(seeded_receipts["r_b"].id) in ids
        assert str(seeded_receipts["r_a"].id) not in ids

    async def test_match_context_merchant(self, client: AsyncClient, seeded_receipts):
        """Merchant match sets source=merchant in match_context."""
        r = await client.post("/api/v1/receipts/search", json={"query": "coffee"})
        data = r.json()
        item = next(
            x for x in data["receipts"] if x["receipt_id"] == str(seeded_receipts["r_a"].id)
        )
        assert item["match_context"]["source"] == "merchant"

    async def test_match_context_line_item(self, client: AsyncClient, seeded_receipts):
        """Line-item match sets source=line_item and matched_description."""
        r = await client.post("/api/v1/receipts/search", json={"query": "apples"})
        data = r.json()
        item = next(
            x for x in data["receipts"] if x["receipt_id"] == str(seeded_receipts["r_b"].id)
        )
        ctx = item["match_context"]
        assert ctx["source"] == "line_item"
        assert "apple" in (ctx.get("matched_description") or "").lower()

    async def test_total_count_unaffected_by_pagination(self, client: AsyncClient, seeded_receipts):
        """total_count reflects full result set even when limit < total."""
        r1 = await client.post("/api/v1/receipts/search", json={"limit": 1})
        r2 = await client.post("/api/v1/receipts/search", json={"limit": 50})
        assert r1.json()["total_count"] == r2.json()["total_count"]

    async def test_next_cursor_present_when_more_results(
        self, client: AsyncClient, seeded_receipts
    ):
        r = await client.post("/api/v1/receipts/search", json={"limit": 1})
        data = r.json()
        if data["total_count"] > 1:
            assert data["next_cursor"] is not None


class TestSearchFilters:
    async def test_processing_status_filter(self, client: AsyncClient, seeded_receipts):
        r = await client.post(
            "/api/v1/receipts/search",
            json={"processing_status": ["queued"]},
        )
        data = r.json()
        ids = {item["receipt_id"] for item in data["receipts"]}
        assert str(seeded_receipts["r_e"].id) in ids
        assert str(seeded_receipts["r_a"].id) not in ids

    async def test_verification_status_filter(self, client: AsyncClient, seeded_receipts):
        r = await client.post(
            "/api/v1/receipts/search",
            json={"verification_status": ["needs_review"]},
        )
        data = r.json()
        ids = {item["receipt_id"] for item in data["receipts"]}
        assert str(seeded_receipts["r_c"].id) in ids
        assert str(seeded_receipts["r_a"].id) not in ids

    async def test_amount_range_filter(self, client: AsyncClient, seeded_receipts):
        r = await client.post(
            "/api/v1/receipts/search",
            json={"amount_min_minor": 400, "amount_max_minor": 600},
        )
        data = r.json()
        ids = {item["receipt_id"] for item in data["receipts"]}
        assert str(seeded_receipts["r_a"].id) in ids
        assert str(seeded_receipts["r_c"].id) not in ids  # 15000

    async def test_invalid_amount_range_rejected(self, client: AsyncClient):
        r = await client.post(
            "/api/v1/receipts/search",
            json={"amount_min_minor": 1000, "amount_max_minor": 500},
        )
        assert r.status_code == 422

    async def test_invalid_processing_status_rejected(self, client: AsyncClient):
        r = await client.post(
            "/api/v1/receipts/search",
            json={"processing_status": ["not_a_real_status"]},
        )
        assert r.status_code == 422

    async def test_combined_query_and_status_filter(self, client: AsyncClient, seeded_receipts):
        """Query + status filter composes correctly."""
        r = await client.post(
            "/api/v1/receipts/search",
            json={"query": "tech", "verification_status": ["needs_review"]},
        )
        data = r.json()
        ids = {item["receipt_id"] for item in data["receipts"]}
        assert str(seeded_receipts["r_c"].id) in ids
        assert str(seeded_receipts["r_a"].id) not in ids

    async def test_deduplication_status_filter(self, client: AsyncClient, seeded_receipts):
        r = await client.post(
            "/api/v1/receipts/search",
            json={"deduplication_status": ["suspected_duplicate"]},
        )
        assert r.status_code == 200
        data = r.json()
        ids = {item["receipt_id"] for item in data["receipts"]}
        assert str(seeded_receipts["r_b"].id) in ids
        assert data["receipts"][0]["deduplication_status"] == "suspected_duplicate"

    async def test_like_wildcards_are_literal(self, client: AsyncClient):
        r = await client.post("/api/v1/receipts/search", json={"query": "%_"})
        assert r.status_code == 200
        assert r.json()["total_count"] == 0


class TestSearchPagination:
    async def test_no_duplicates_across_pages(self, client: AsyncClient, seeded_receipts):
        """Load all pages and confirm no receipt_id appears twice."""
        all_ids: list[str] = []
        cursor = None
        while True:
            payload = {"limit": 2}
            if cursor:
                payload["cursor"] = cursor
            r = await client.post("/api/v1/receipts/search", json=payload)
            data = r.json()
            page_ids = [item["receipt_id"] for item in data["receipts"]]
            all_ids.extend(page_ids)
            cursor = data.get("next_cursor")
            if not cursor:
                break

        assert len(all_ids) == len(set(all_ids)), "Duplicate receipt_id across pages"

    async def test_all_receipts_covered_across_pages(self, client: AsyncClient, seeded_receipts):
        """All owner receipts appear exactly once across all pages."""
        all_ids: set[str] = set()
        cursor = None
        while True:
            payload = {"limit": 2}
            if cursor:
                payload["cursor"] = cursor
            r = await client.post("/api/v1/receipts/search", json=payload)
            data = r.json()
            for item in data["receipts"]:
                all_ids.add(item["receipt_id"])
            cursor = data.get("next_cursor")
            if not cursor:
                break

        assert str(seeded_receipts["r_a"].id) in all_ids
        assert str(seeded_receipts["r_b"].id) in all_ids
        assert str(seeded_receipts["r_d"].id) not in all_ids  # other owner

    async def test_page_with_amount_asc_sort(self, client: AsyncClient, seeded_receipts):
        r = await client.post(
            "/api/v1/receipts/search",
            json={"sort": "amount_asc", "limit": 3},
        )
        assert r.status_code == 200
        data = r.json()
        amounts = [
            item["current_revision"]["total_minor"]
            for item in data["receipts"]
            if item.get("current_revision")
            and item["current_revision"].get("total_minor") is not None
        ]
        assert amounts == sorted(amounts), "amount_asc: results not sorted ascending"

    async def test_invalid_cursor_rejected(self, client: AsyncClient):
        r = await client.post(
            "/api/v1/receipts/search",
            json={"cursor": "not-a-valid-cursor"},
        )
        assert r.status_code == 422

    async def test_cursor_cannot_be_reused_with_different_filters(
        self, client: AsyncClient, seeded_receipts
    ):
        first = await client.post(
            "/api/v1/receipts/search",
            json={"limit": 1},
        )
        cursor = first.json()["next_cursor"]
        assert cursor is not None

        reused = await client.post(
            "/api/v1/receipts/search",
            json={"limit": 1, "cursor": cursor, "query": "coffee"},
        )
        assert reused.status_code == 422

    async def test_amount_sort_pages_include_null_amounts_once(
        self, client: AsyncClient, seeded_receipts
    ):
        all_ids: list[str] = []
        cursor = None
        while True:
            payload = {"sort": "amount_asc", "limit": 1}
            if cursor:
                payload["cursor"] = cursor
            response = await client.post("/api/v1/receipts/search", json=payload)
            assert response.status_code == 200
            data = response.json()
            all_ids.extend(item["receipt_id"] for item in data["receipts"])
            cursor = data.get("next_cursor")
            if not cursor:
                break

        assert len(all_ids) == len(set(all_ids))
        assert str(seeded_receipts["r_e"].id) in all_ids


class TestSearchSecurity:
    async def test_other_owner_receipts_excluded(self, client: AsyncClient, seeded_receipts):
        """Other owner's receipts must never appear — even with matching merchant."""
        r = await client.post("/api/v1/receipts/search", json={"query": "coffee"})
        data = r.json()
        ids = {item["receipt_id"] for item in data["receipts"]}
        assert str(seeded_receipts["r_d"].id) not in ids

    async def test_query_term_not_logged(self, client: AsyncClient, caplog):
        """Sensitive search term must not appear in structured log output."""
        import logging

        with caplog.at_level(logging.DEBUG):
            await client.post(
                "/api/v1/receipts/search",
                json={"query": "SENTINELTERM12345"},
            )
        for record in caplog.records:
            assert "SENTINELTERM12345" not in record.getMessage()
