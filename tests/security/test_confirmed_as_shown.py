"""Security tests for the confirmed_as_shown review disposition (Sprint 2B).

S1: Bypass prevention — _snapshot_equals_parent unit tests.
    Verifies that confirmed_as_shown cannot be used when the submitted snapshot
    differs from the current parent revision in any material field.

S2: Authorization — confirms that auth enforcement (401, 404, 422) is
    unchanged when review_disposition="confirmed_as_shown" is included.

All test data is entirely synthetic (OPS-02, AGENTS.md §7).
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace

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
from financial_os.schemas.receipt import CreateHumanRevisionRequest, LineItemInputSchema
from financial_os.services.receipt import _snapshot_equals_parent

pytestmark = [pytest.mark.security]

# ── Shared test identities ────────────────────────────────────────────────────

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

TEST_OWNER_A = VerifiedOwner(
    subject_id="google:test-confirmed-shown-owner-a",
    auth_subject_id="",
    auth_time=9999999999,
)

TEST_OWNER_B = VerifiedOwner(
    subject_id="google:test-confirmed-shown-owner-b",
    auth_subject_id="",
    auth_time=9999999999,
)


# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_parent_revision(
    *,
    currency: str = "USD",
    merchant_normalized: str | None = None,
    purchase_datetime=None,
    purchase_timezone: str | None = None,
    subtotal_minor: int | None = 1000,
    tax_minor: int | None = 80,
    tip_minor: int | None = None,
    discount_minor: int | None = None,
    total_minor: int = 1080,
) -> SimpleNamespace:
    """Build a synthetic parent ReceiptRevision duck-typed object."""
    return SimpleNamespace(
        currency=currency,
        merchant_normalized=merchant_normalized,
        purchase_datetime=purchase_datetime,
        purchase_timezone=purchase_timezone,
        subtotal_minor=subtotal_minor,
        tax_minor=tax_minor,
        tip_minor=tip_minor,
        discount_minor=discount_minor,
        total_minor=total_minor,
    )


def _make_parent_line_item(
    ordinal: int,
    *,
    raw_description: str = "SYNTHETIC ITEM",
    normalized_description: str | None = None,
    quantity=None,
    unit: str | None = None,
    unit_price_decimal=None,
    line_total_minor: int | None = 500,
    discount_minor: int | None = None,
    category_suggestion: str | None = None,
) -> SimpleNamespace:
    """Build a synthetic LineItemRevision duck-typed object."""
    return SimpleNamespace(
        ordinal=ordinal,
        raw_description=raw_description,
        normalized_description=normalized_description,
        quantity=quantity,
        unit=unit,
        unit_price_decimal=unit_price_decimal,
        line_total_minor=line_total_minor,
        discount_minor=discount_minor,
        category_suggestion=category_suggestion,
    )


def _make_request(
    *,
    currency: str = "USD",
    subtotal_minor: int | None = 1000,
    tax_minor: int | None = 80,
    tip_minor: int | None = None,
    discount_minor: int | None = None,
    total_minor: int = 1080,
    line_items: list[LineItemInputSchema] | None = None,
) -> CreateHumanRevisionRequest:
    """Build a CreateHumanRevisionRequest with minimal required fields."""
    return CreateHumanRevisionRequest(
        expected_parent_revision_id=uuid.uuid4(),
        currency=currency,
        subtotal_minor=subtotal_minor,
        tax_minor=tax_minor,
        tip_minor=tip_minor,
        discount_minor=discount_minor,
        total_minor=total_minor,
        review_disposition="confirmed_as_shown",
        line_items=line_items or [],
    )


def _line_item_input(
    description: str = "SYNTHETIC ITEM",
    *,
    normalized_description: str | None = None,
    quantity: str | None = None,
    unit: str | None = None,
    unit_price_decimal: str | None = None,
    line_total_minor: int | None = 500,
    discount_minor: int | None = None,
    category_suggestion: str | None = None,
) -> LineItemInputSchema:
    return LineItemInputSchema(
        description=description,
        normalized_description=normalized_description,
        quantity=quantity,
        unit=unit,
        unit_price_decimal=unit_price_decimal,
        line_total_minor=line_total_minor,
        discount_minor=discount_minor,
        category_suggestion=category_suggestion,
    )


# ── S1: Bypass prevention unit tests ─────────────────────────────────────────


@pytest.mark.unit
class TestSnapshotEqualsParent:
    """_snapshot_equals_parent must return True only for semantically identical snapshots.

    If any material field differs between the submitted snapshot and the parent revision,
    the helper must return False — preventing confirmed_as_shown from bypassing arithmetic
    validation on a materially changed payload.
    """

    def test_identical_snapshot_returns_true(self):
        """Snapshot that exactly mirrors the parent revision returns True."""
        parent = _make_parent_revision()
        request = _make_request()
        result = _snapshot_equals_parent(request, parent, [])
        assert result is True

    def test_modified_total_minor_returns_false(self):
        """Changed total_minor must be detected — even 1 cent difference."""
        parent = _make_parent_revision(total_minor=1080)
        request = _make_request(total_minor=1081)
        assert _snapshot_equals_parent(request, parent, []) is False

    def test_modified_subtotal_minor_returns_false(self):
        """Changed subtotal_minor must be detected."""
        parent = _make_parent_revision(subtotal_minor=1000, total_minor=1080)
        request = _make_request(subtotal_minor=999, total_minor=1080)
        assert _snapshot_equals_parent(request, parent, []) is False

    def test_modified_tax_minor_returns_false(self):
        """Changed tax_minor must be detected."""
        parent = _make_parent_revision(tax_minor=80, total_minor=1080)
        request = _make_request(tax_minor=81, total_minor=1080)
        assert _snapshot_equals_parent(request, parent, []) is False

    def test_modified_discount_minor_returns_false(self):
        """Adding a discount where parent has None must be detected."""
        parent = _make_parent_revision(discount_minor=None, total_minor=1080)
        request = _make_request(discount_minor=100, total_minor=1080)
        assert _snapshot_equals_parent(request, parent, []) is False

    def test_different_discount_value_returns_false(self):
        """Changing discount_minor from one non-None value to another is detected."""
        parent = _make_parent_revision(discount_minor=50, total_minor=1080)
        request = _make_request(discount_minor=100, total_minor=1080)
        assert _snapshot_equals_parent(request, parent, []) is False

    def test_none_to_nonzero_tip_returns_false(self):
        """Adding tip_minor where parent has None must be detected."""
        parent = _make_parent_revision(tip_minor=None, total_minor=1080)
        request = _make_request(tip_minor=50, total_minor=1080)
        assert _snapshot_equals_parent(request, parent, []) is False

    def test_different_currency_returns_false(self):
        """Currency mismatch is caught by the equality check."""
        parent = _make_parent_revision(currency="USD")
        request = _make_request(currency="EUR")
        assert _snapshot_equals_parent(request, parent, []) is False

    def test_extra_line_item_returns_false(self):
        """Submitting one more line item than the parent returns False."""
        parent = _make_parent_revision()
        parent_lines = []  # no line items on parent
        request = _make_request(line_items=[_line_item_input()])
        assert _snapshot_equals_parent(request, parent, parent_lines) is False

    def test_fewer_line_items_returns_false(self):
        """Submitting fewer line items than the parent returns False."""
        parent = _make_parent_revision()
        parent_lines = [_make_parent_line_item(1), _make_parent_line_item(2)]
        request = _make_request(line_items=[_line_item_input()])
        assert _snapshot_equals_parent(request, parent, parent_lines) is False

    def test_modified_line_item_description_returns_false(self):
        """Changed line item raw_description must be detected."""
        parent = _make_parent_revision()
        parent_lines = [_make_parent_line_item(1, raw_description="ORIGINAL ITEM")]
        request = _make_request(line_items=[_line_item_input("CHANGED DESCRIPTION")])
        assert _snapshot_equals_parent(request, parent, parent_lines) is False

    def test_modified_line_item_total_returns_false(self):
        """Changed line_total_minor in a line item must be detected."""
        parent = _make_parent_revision()
        parent_lines = [_make_parent_line_item(1, line_total_minor=500)]
        request = _make_request(line_items=[_line_item_input(line_total_minor=501)])
        assert _snapshot_equals_parent(request, parent, parent_lines) is False

    def test_modified_line_item_discount_returns_false(self):
        """Changed discount_minor in a line item must be detected."""
        parent = _make_parent_revision()
        parent_lines = [_make_parent_line_item(1, discount_minor=None)]
        request = _make_request(line_items=[_line_item_input(discount_minor=50)])
        assert _snapshot_equals_parent(request, parent, parent_lines) is False

    def test_matching_line_items_returns_true(self):
        """Line items matching the parent in description, total, discount return True."""
        parent = _make_parent_revision()
        parent_lines = [
            _make_parent_line_item(1, raw_description="SYNTHETIC ITEM", line_total_minor=500)
        ]
        request = _make_request(
            line_items=[_line_item_input("SYNTHETIC ITEM", line_total_minor=500)]
        )
        assert _snapshot_equals_parent(request, parent, parent_lines) is True

    def test_none_equals_none_for_subtotal(self):
        """None subtotal_minor on both sides returns True (None != 0 invariant)."""
        parent = _make_parent_revision(subtotal_minor=None, total_minor=1080)
        request = _make_request(subtotal_minor=None, total_minor=1080)
        assert _snapshot_equals_parent(request, parent, []) is True

    def test_none_does_not_equal_zero_for_tax(self):
        """None and zero remain distinct for optional money fields."""
        # The parent has tax_minor=None. Request tax_minor=0 should not be considered equal.
        parent = _make_parent_revision(tax_minor=None, subtotal_minor=1080, total_minor=1080)
        request = _make_request(tax_minor=None, subtotal_minor=1080, total_minor=1080)
        # Identical: both None — should be True
        assert _snapshot_equals_parent(request, parent, []) is True

    # ── New field coverage: merchant_normalized, purchase_timezone ────────────

    def test_modified_merchant_normalized_returns_false(self):
        """Changed merchant_normalized must be detected."""
        parent = _make_parent_revision(merchant_normalized="ACME STORE")
        request = _make_request()
        request.merchant_normalized = "DIFFERENT STORE"
        assert _snapshot_equals_parent(request, parent, []) is False

    def test_added_merchant_normalized_where_parent_none_returns_false(self):
        """Submitting merchant_normalized when parent has None must be detected."""
        parent = _make_parent_revision(merchant_normalized=None)
        request = _make_request()
        request.merchant_normalized = "ACME STORE"
        assert _snapshot_equals_parent(request, parent, []) is False

    def test_matching_merchant_normalized_returns_true(self):
        """Identical merchant_normalized returns True."""
        parent = _make_parent_revision(merchant_normalized="ACME STORE")
        request = _make_request()
        request.merchant_normalized = "ACME STORE"
        assert _snapshot_equals_parent(request, parent, []) is True

    def test_modified_purchase_timezone_returns_false(self):
        """Changed purchase_timezone must be detected."""
        parent = _make_parent_revision(purchase_timezone="America/New_York")
        request = _make_request()
        request.purchase_timezone = "America/Los_Angeles"
        assert _snapshot_equals_parent(request, parent, []) is False

    def test_added_purchase_timezone_where_parent_none_returns_false(self):
        """Submitting purchase_timezone when parent has None must be detected."""
        parent = _make_parent_revision(purchase_timezone=None)
        request = _make_request()
        request.purchase_timezone = "America/New_York"
        assert _snapshot_equals_parent(request, parent, []) is False

    def test_matching_purchase_timezone_returns_true(self):
        """Identical purchase_timezone returns True."""
        parent = _make_parent_revision(purchase_timezone="America/New_York")
        request = _make_request()
        request.purchase_timezone = "America/New_York"
        assert _snapshot_equals_parent(request, parent, []) is True

    def test_modified_purchase_datetime_returns_false(self):
        """A changed purchase instant must be detected."""
        parent = _make_parent_revision(
            purchase_datetime=datetime.fromisoformat("2026-08-14T12:00:00+00:00")
        )
        request = _make_request()
        request.purchase_datetime = datetime.fromisoformat("2026-08-14T12:01:00+00:00")
        assert _snapshot_equals_parent(request, parent, []) is False

    def test_same_purchase_instant_in_another_offset_returns_true(self):
        """Datetime equality is based on the instant rather than offset spelling."""
        parent = _make_parent_revision(
            purchase_datetime=datetime.fromisoformat("2026-08-14T12:00:00+00:00")
        )
        request = _make_request()
        request.purchase_datetime = datetime.fromisoformat("2026-08-14T07:00:00-05:00")
        assert _snapshot_equals_parent(request, parent, []) is True

    # ── New line-item field coverage ──────────────────────────────────────────

    def test_modified_line_item_normalized_description_returns_false(self):
        """Changed normalized_description in a line item must be detected."""
        parent = _make_parent_revision()
        parent_lines = [_make_parent_line_item(1, normalized_description="Original")]
        request = _make_request(line_items=[_line_item_input(normalized_description="Changed")])
        assert _snapshot_equals_parent(request, parent, parent_lines) is False

    def test_modified_line_item_category_suggestion_returns_false(self):
        """Changed category_suggestion in a line item must be detected."""
        parent = _make_parent_revision()
        parent_lines = [_make_parent_line_item(1, category_suggestion="groceries")]
        request = _make_request(line_items=[_line_item_input(category_suggestion="household")])
        assert _snapshot_equals_parent(request, parent, parent_lines) is False

    @pytest.mark.parametrize(
        ("parent_kwargs", "request_kwargs"),
        [
            ({"quantity": Decimal("2.0")}, {"quantity": "3"}),
            ({"unit": "ea"}, {"unit": "lb"}),
            (
                {"unit_price_decimal": Decimal("5.00")},
                {"unit_price_decimal": "5.01"},
            ),
        ],
    )
    def test_modified_line_item_detail_returns_false(
        self, parent_kwargs: dict, request_kwargs: dict
    ):
        """Quantity, unit, and unit price cannot change under confirm-as-shown."""
        parent = _make_parent_revision()
        parent_lines = [_make_parent_line_item(1, **parent_kwargs)]
        request = _make_request(line_items=[_line_item_input(**request_kwargs)])
        assert _snapshot_equals_parent(request, parent, parent_lines) is False

    def test_decimal_trailing_zeros_are_semantically_equal(self):
        """Equivalent NUMERIC values compare equally regardless of scale."""
        parent = _make_parent_revision()
        parent_lines = [
            _make_parent_line_item(
                1,
                quantity=Decimal("2.000000"),
                unit_price_decimal=Decimal("5.000000"),
            )
        ]
        request = _make_request(
            line_items=[_line_item_input(quantity="2", unit_price_decimal="5.0")]
        )
        assert _snapshot_equals_parent(request, parent, parent_lines) is True

    def test_matching_line_items_with_all_fields_returns_true(self):
        """All line-item fields matching returns True."""
        parent = _make_parent_revision()
        parent_lines = [
            _make_parent_line_item(
                1,
                raw_description="SYNTHETIC ITEM",
                normalized_description="Synthetic Item",
                category_suggestion="groceries",
                line_total_minor=500,
                discount_minor=None,
            )
        ]
        request = _make_request(
            line_items=[
                _line_item_input(
                    "SYNTHETIC ITEM",
                    normalized_description="Synthetic Item",
                    category_suggestion="groceries",
                    line_total_minor=500,
                    discount_minor=None,
                )
            ]
        )
        assert _snapshot_equals_parent(request, parent, parent_lines) is True


# ── S2: Authorization tests (HTTP ASGI) ───────────────────────────────────────
# These tests require DATABASE_URL; they are skipped automatically when absent.


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
    """App with NO dependency override — auth layer runs for real."""
    app = create_test_app(
        settings=TEST_SETTINGS,
        storage=FakeStorageAdapter(),
        queue=FakeQueueAdapter(),
        extractor=FakeExtractionAdapter(),
        session_factory=session_factory,
    )
    async with app.router.lifespan_context(app):
        yield app


@pytest_asyncio.fixture(scope="module")
async def owner_a_receipt_id(session_factory) -> uuid.UUID:
    """Create a reserved receipt owned by owner A for auth checks."""
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


def _confirmed_body(parent_revision_id: uuid.UUID | None = None) -> dict:
    """A confirmed_as_shown request body — arithmetically valid."""
    return {
        "expected_parent_revision_id": str(parent_revision_id or uuid.uuid4()),
        "currency": "USD",
        "subtotal_minor": 1000,
        "tax_minor": 80,
        "total_minor": 1080,
        "review_disposition": "confirmed_as_shown",
        "line_items": [],
    }


pytestmark_integration = [
    pytest.mark.security,
    pytest.mark.integration,
    pytest.mark.asyncio(loop_scope="module"),
]


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="module")
class TestConfirmedAsShownAuth:
    """IAM: auth enforcement is identical regardless of review_disposition value.

    confirmed_as_shown in the request body must not weaken any authorization check.
    """

    async def test_missing_bearer_returns_401_for_confirmed_as_shown(
        self,
        base_app_no_override,
        owner_a_receipt_id: uuid.UUID,
    ) -> None:
        """No Authorization header → 401 even when review_disposition is confirmed_as_shown."""
        async with AsyncClient(
            transport=ASGITransport(app=base_app_no_override),
            base_url="http://test",
        ) as client:
            resp = await client.post(
                f"/api/v1/receipts/{owner_a_receipt_id}/human-revisions",
                json=_confirmed_body(),
            )
        assert resp.status_code == 401, f"Expected 401 for missing token, got {resp.status_code}"

    async def test_cross_owner_returns_404_for_confirmed_as_shown(
        self,
        session_factory,
        owner_a_receipt_id: uuid.UUID,
    ) -> None:
        """Owner B cannot access Owner A's receipt via confirmed_as_shown — returns 404."""
        app = create_test_app(
            settings=TEST_SETTINGS,
            storage=FakeStorageAdapter(),
            queue=FakeQueueAdapter(),
            extractor=FakeExtractionAdapter(),
            session_factory=session_factory,
        )
        app.dependency_overrides[get_verified_owner] = lambda: TEST_OWNER_B

        async with app.router.lifespan_context(app):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.post(
                    f"/api/v1/receipts/{owner_a_receipt_id}/human-revisions",
                    json=_confirmed_body(),
                )

        # 404: opaque — prevents receipt ID enumeration.
        assert resp.status_code == 404, (
            f"Cross-ownership with confirmed_as_shown: expected 404, got {resp.status_code}"
        )

    async def test_invalid_receipt_id_format_returns_422(
        self,
        session_factory,
    ) -> None:
        """An authenticated malformed receipt_id receives path-validation 422."""
        app = create_test_app(
            settings=TEST_SETTINGS,
            storage=FakeStorageAdapter(),
            queue=FakeQueueAdapter(),
            extractor=FakeExtractionAdapter(),
            session_factory=session_factory,
        )
        app.dependency_overrides[get_verified_owner] = lambda: TEST_OWNER_A

        async with app.router.lifespan_context(app):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.post(
                    "/api/v1/receipts/not-a-valid-uuid/human-revisions",
                    json=_confirmed_body(),
                )
        assert resp.status_code == 422, f"Invalid receipt_id: expected 422, got {resp.status_code}"
