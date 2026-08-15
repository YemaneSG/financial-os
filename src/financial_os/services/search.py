"""Receipt search service — owner-scoped server-side search with keyset pagination.

Design rules:
- Every query begins with Receipt.owner_id == owner_id (IAM-01).
- Search terms are parameterized ILIKE values; they are never concatenated into
  SQL and never appear in log output (LOG-01, SQL-01).
- No N+1: revision data is fetched with a single LEFT JOIN on the main query.
- Line-item match context uses one bulk query per page, not per-receipt calls.
- Fingerprints, hashes, and private identifiers are never returned.
- deduplication_status filter is applied only when the column exists on Receipt
  (Workstream A integration guard).
"""

from __future__ import annotations

import base64
import hashlib
import json
import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING, cast

from sqlalchemy import ColumnElement, and_, exists, func, nullslast, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from financial_os.auth.firebase import VerifiedOwner
from financial_os.domain.errors import ForbiddenError, ValidationError
from financial_os.domain.states import DeduplicationStatus
from financial_os.models.receipt import Receipt
from financial_os.schemas.receipt import RevisionSummarySchema
from financial_os.schemas.search import (
    MatchContext,
    SearchReceiptItemSchema,
    SearchReceiptsRequest,
    SearchReceiptsResponse,
)

if TYPE_CHECKING:
    from financial_os.config import Settings
    from financial_os.models.extraction import ReceiptRevision

# ── Cursor encoding ────────────────────────────────────────────────────────────


def _encode_date_cursor(
    effective_date: datetime,
    receipt_id: uuid.UUID,
    sort: str,
    filter_digest: str,
) -> str:
    payload = json.dumps(
        {
            "v": 1,
            "t": "d",
            "s": sort,
            "f": filter_digest,
            "d": effective_date.isoformat(),
            "id": str(receipt_id),
        },
        separators=(",", ":"),
    )
    return base64.urlsafe_b64encode(payload.encode()).decode()


def _encode_amount_cursor(
    amount: int | None,
    receipt_id: uuid.UUID,
    sort: str,
    filter_digest: str,
) -> str:
    payload = json.dumps(
        {
            "v": 1,
            "t": "a",
            "s": sort,
            "f": filter_digest,
            "a": amount,
            "id": str(receipt_id),
        },
        separators=(",", ":"),
    )
    return base64.urlsafe_b64encode(payload.encode()).decode()


def _request_filter_digest(request: SearchReceiptsRequest) -> str:
    payload = request.model_dump(mode="json", exclude={"cursor", "limit"})
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode()).hexdigest()[:24]


def _decode_cursor(cursor: str, expected_sort: str, filter_digest: str) -> dict[str, object]:
    try:
        payload = json.loads(base64.urlsafe_b64decode(cursor.encode()).decode())
        if not isinstance(payload, dict):
            raise ValueError
        if payload.get("v") != 1:
            raise ValueError
        if payload.get("s") != expected_sort or payload.get("f") != filter_digest:
            raise ValueError
        expected_type = "a" if expected_sort.startswith("amount_") else "d"
        if payload.get("t") != expected_type:
            raise ValueError
        uuid.UUID(str(payload["id"]))
        if expected_type == "a":
            amount = payload.get("a")
            if amount is not None and (not isinstance(amount, int) or isinstance(amount, bool)):
                raise ValueError
        else:
            datetime.fromisoformat(str(payload["d"]))
        return payload
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ValidationError("Search cursor is invalid for this request.") from exc


def _escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


# ── Effective-date expression ──────────────────────────────────────────────────


def _effective_date_expr(revision_cls: type[ReceiptRevision]) -> ColumnElement[datetime]:
    """COALESCE(revision.purchase_datetime, receipt.captured_at, receipt.created_at)."""
    return func.coalesce(
        revision_cls.purchase_datetime,
        Receipt.captured_at,
        Receipt.created_at,
    )


# ── Owner resolver ─────────────────────────────────────────────────────────────


async def _resolve_owner_id(
    session: AsyncSession,
    owner: VerifiedOwner,
    settings: Settings,
) -> uuid.UUID:
    from financial_os.models.auth import AuthSubject

    result = await session.execute(
        select(AuthSubject).where(AuthSubject.provider_subject == owner.subject_id)
    )
    subject = result.scalar_one_or_none()
    if subject is None or not subject.allowlisted:
        raise ForbiddenError("Access denied.")

    if subject.valid_after is not None:
        auth_dt = datetime.fromtimestamp(owner.auth_time, tz=UTC)
        if auth_dt < subject.valid_after:
            raise ForbiddenError("Session invalidated.")

    return subject.id


# ── Main search function ───────────────────────────────────────────────────────


async def search_receipts(
    session: AsyncSession,
    owner: VerifiedOwner,
    request: SearchReceiptsRequest,
    settings: Settings,
) -> SearchReceiptsResponse:
    """Owner-scoped receipt search with keyset pagination and no N+1.

    Security invariant: every query branch begins with the owner_id WHERE clause.
    Search terms are parameterized; they never appear in log lines.
    """
    from financial_os.models.extraction import LineItemRevision, ReceiptRevision

    owner_id = await _resolve_owner_id(session, owner, settings)
    norm_query = request.normalized_query
    like_pattern = f"%{_escape_like(norm_query)}%" if norm_query else None
    filter_digest = _request_filter_digest(request)

    eff = _effective_date_expr(ReceiptRevision)

    # ── Base query: Receipt LEFT JOIN ReceiptRevision ──────────────────────────
    base_stmt = (
        select(Receipt, ReceiptRevision)
        .outerjoin(ReceiptRevision, Receipt.current_revision_id == ReceiptRevision.id)
        .where(Receipt.owner_id == owner_id)
    )

    # ── Text search filter ─────────────────────────────────────────────────────
    if like_pattern:
        # Case-insensitive via func.lower + LIKE. Raw OCR never searched (LOG-01).
        merchant_match = func.lower(ReceiptRevision.merchant_normalized).like(
            like_pattern, escape="\\"
        )
        item_match = exists(
            select(LineItemRevision.id)
            .where(
                LineItemRevision.receipt_revision_id == ReceiptRevision.id,
                func.lower(LineItemRevision.normalized_description).like(like_pattern, escape="\\"),
            )
            .correlate(ReceiptRevision)
        )
        base_stmt = base_stmt.where(or_(merchant_match, item_match))

    # ── Status filters ─────────────────────────────────────────────────────────
    if request.processing_status:
        base_stmt = base_stmt.where(Receipt.processing_status.in_(request.processing_status))

    if request.verification_status:
        base_stmt = base_stmt.where(Receipt.verification_status.in_(request.verification_status))

    if request.deduplication_status and hasattr(Receipt, "deduplication_status"):
        dedup_col = Receipt.deduplication_status
        base_stmt = base_stmt.where(dedup_col.in_(request.deduplication_status))

    # ── Date range filter (on effective date) ─────────────────────────────────
    if request.date_from is not None:
        base_stmt = base_stmt.where(eff >= request.date_from)
    if request.date_to is not None:
        base_stmt = base_stmt.where(eff <= request.date_to)

    # ── Amount range filter ────────────────────────────────────────────────────
    if request.amount_min_minor is not None:
        base_stmt = base_stmt.where(ReceiptRevision.total_minor >= request.amount_min_minor)
    if request.amount_max_minor is not None:
        base_stmt = base_stmt.where(ReceiptRevision.total_minor <= request.amount_max_minor)

    # ── Total count (same filters, no pagination) ─────────────────────────────
    count_stmt = select(func.count()).select_from(base_stmt.subquery())
    total_count_result = await session.execute(count_stmt)
    total_count = total_count_result.scalar_one()

    # ── Sort and cursor ────────────────────────────────────────────────────────
    is_amount_sort = request.sort in ("amount_desc", "amount_asc")

    if request.sort == "effective_date_desc":
        page_stmt = base_stmt.order_by(eff.desc(), Receipt.id.desc())
    elif request.sort == "effective_date_asc":
        page_stmt = base_stmt.order_by(eff.asc(), Receipt.id.asc())
    elif request.sort == "amount_desc":
        page_stmt = base_stmt.order_by(
            nullslast(ReceiptRevision.total_minor.desc()), Receipt.id.desc()
        )
    elif request.sort == "amount_asc":
        page_stmt = base_stmt.order_by(
            nullslast(ReceiptRevision.total_minor.asc()), Receipt.id.asc()
        )
    else:
        page_stmt = base_stmt.order_by(eff.desc(), Receipt.id.desc())

    page_stmt = page_stmt.limit(request.limit + 1)

    # Apply keyset cursor
    if request.cursor:
        cur = _decode_cursor(request.cursor, request.sort, filter_digest)
        cur_id = uuid.UUID(str(cur["id"]))
        if cur.get("t") == "a":
            # Amount-based cursor. Null values sort last in both directions.
            raw_amount = cur.get("a")
            id_operator = (
                Receipt.id < cur_id if request.sort == "amount_desc" else Receipt.id > cur_id
            )
            if raw_amount is None:
                page_stmt = page_stmt.where(ReceiptRevision.total_minor.is_(None), id_operator)
            else:
                cur_amount = cast(int, raw_amount)
                if request.sort == "amount_desc":
                    page_stmt = page_stmt.where(
                        or_(
                            ReceiptRevision.total_minor < cur_amount,
                            ReceiptRevision.total_minor.is_(None),
                            and_(
                                ReceiptRevision.total_minor == cur_amount,
                                Receipt.id < cur_id,
                            ),
                        )
                    )
                else:
                    page_stmt = page_stmt.where(
                        or_(
                            ReceiptRevision.total_minor > cur_amount,
                            ReceiptRevision.total_minor.is_(None),
                            and_(
                                ReceiptRevision.total_minor == cur_amount,
                                Receipt.id > cur_id,
                            ),
                        )
                    )
        else:
            # Date-based cursor
            cur_date = datetime.fromisoformat(str(cur["d"]))
            if request.sort == "effective_date_desc":
                page_stmt = page_stmt.where(
                    or_(
                        eff < cur_date,
                        and_(eff == cur_date, Receipt.id < cur_id),
                    )
                )
            else:
                page_stmt = page_stmt.where(
                    or_(
                        eff > cur_date,
                        and_(eff == cur_date, Receipt.id > cur_id),
                    )
                )

    result = await session.execute(page_stmt)
    rows = result.all()

    next_cursor: str | None = None
    if len(rows) > request.limit:
        rows = rows[: request.limit]
        last_receipt, last_revision = rows[-1]
        if is_amount_sort:
            next_cursor = _encode_amount_cursor(
                last_revision.total_minor if last_revision else None,
                last_receipt.id,
                request.sort,
                filter_digest,
            )
        else:
            last_eff: datetime = (
                last_revision.purchase_datetime
                if last_revision and last_revision.purchase_datetime
                else (last_receipt.captured_at or last_receipt.created_at)
            )
            next_cursor = _encode_date_cursor(
                last_eff, last_receipt.id, request.sort, filter_digest
            )

    # ── Build match context (one bulk query for line-item matches) ─────────────
    matched_items: dict[uuid.UUID, str] = {}
    if norm_query and like_pattern and rows:
        non_merchant_revision_ids = [
            rv.id
            for _, rv in rows
            if rv is not None and norm_query not in (rv.merchant_normalized or "").lower()
        ]
        if non_merchant_revision_ids:
            item_result = await session.execute(
                select(
                    LineItemRevision.receipt_revision_id,
                    LineItemRevision.normalized_description,
                )
                .where(
                    LineItemRevision.receipt_revision_id.in_(non_merchant_revision_ids),
                    func.lower(LineItemRevision.normalized_description).like(
                        like_pattern, escape="\\"
                    ),
                )
                .order_by(
                    LineItemRevision.receipt_revision_id.asc(),
                    LineItemRevision.ordinal.asc(),
                )
            )
            for rev_id, desc in item_result:
                if desc:
                    matched_items.setdefault(rev_id, desc)

    # ── Assemble response items ────────────────────────────────────────────────
    items: list[SearchReceiptItemSchema] = []
    for receipt, revision in rows:
        revision_summary = _build_revision_summary(revision)

        match_context: MatchContext | None = None
        if norm_query and revision is not None:
            merchant = (revision.merchant_normalized or "").lower()
            if norm_query in merchant:
                match_context = MatchContext(source="merchant")
            elif revision.id in matched_items:
                match_context = MatchContext(
                    source="line_item",
                    matched_description=matched_items[revision.id],
                )

        items.append(
            SearchReceiptItemSchema(
                receipt_id=receipt.id,
                processing_status=receipt.processing_status,
                verification_status=receipt.verification_status,
                financial_context=receipt.financial_context,
                expected_asset_count=receipt.expected_asset_count,
                acknowledged_at=receipt.acknowledged_at,
                created_at=receipt.created_at,
                captured_at=receipt.captured_at,
                deduplication_status=DeduplicationStatus(receipt.deduplication_status),
                canonical_receipt_id=receipt.canonical_receipt_id,
                current_revision=revision_summary,
                match_context=match_context,
            )
        )

    return SearchReceiptsResponse(
        receipts=items,
        total_count=total_count,
        next_cursor=next_cursor,
    )


def _build_revision_summary(
    revision: ReceiptRevision | None,
) -> RevisionSummarySchema | None:
    if revision is None:
        return None
    return RevisionSummarySchema(
        revision_id=revision.id,
        source_type=revision.source_type,
        merchant_normalized=revision.merchant_normalized,
        purchase_datetime=revision.purchase_datetime,
        purchase_timezone=revision.purchase_timezone,
        currency=revision.currency,
        subtotal_minor=revision.subtotal_minor,
        tax_minor=revision.tax_minor,
        tip_minor=revision.tip_minor,
        discount_minor=revision.discount_minor,
        total_minor=revision.total_minor,
        overall_confidence=(
            float(revision.overall_confidence) if revision.overall_confidence is not None else None
        ),
    )
