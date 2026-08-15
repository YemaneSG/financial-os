"""Receipt deduplication service — deterministic classification engine.

Classification rules (priority order):
  1. Idempotency: same owner/client-submission → same receipt (DB constraint, not here).
  2. Exact evidence fingerprint match within owner → confirmed_duplicate.
  3. Complete semantic fingerprint match within owner → confirmed_duplicate.
  4. Partial structured agreement (merchant+date+currency+total) → suspected_duplicate.
  5. No match → unique.

All queries begin with the authenticated owner boundary (AGENTS.md §8).
No merchant names, amounts, fingerprint values, or owner PII appear in logs.
Fingerprints are never returned by public APIs.
This function does NOT commit — the caller commits.
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy import cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.types import Date

from financial_os.domain.dedup import (
    compute_evidence_fingerprint,
    compute_semantic_fingerprint,
)
from financial_os.domain.states import (
    ActorType,
    DeduplicationStatus,
    StateEventDimension,
)
from financial_os.models.events import StateEvent
from financial_os.models.extraction import LineItemRevision, ReceiptRevision
from financial_os.models.receipt import Receipt, ReceiptAsset

logger = logging.getLogger(__name__)

_DEDUP_RULE_VERSION = "v1"


def _utc_now() -> datetime:
    return datetime.now(UTC)


async def classify_receipt(
    session: AsyncSession,
    receipt: Receipt,
    correlation_id: str,
    actor_type: ActorType = ActorType.WORKER,
) -> DeduplicationStatus:
    """Classify receipt against the owner's existing receipts and update its fields.

    Idempotent: calling multiple times converges to the same result.
    Owner-scoped: every query is bounded by receipt.owner_id.
    Does NOT commit — router or caller commits.
    """
    owner_id: uuid.UUID = receipt.owner_id
    prev_status = receipt.deduplication_status

    # ── Step 1: Compute evidence fingerprint from verified assets ──────────────
    asset_result = await session.execute(
        select(ReceiptAsset)
        .where(
            ReceiptAsset.receipt_id == receipt.id,
            ReceiptAsset.upload_status == "verified",
        )
        .order_by(ReceiptAsset.ordinal)
    )
    assets = list(asset_result.scalars().all())

    evidence_fp: str | None = None
    if assets and all(a.sha256 for a in assets):
        evidence_fp = compute_evidence_fingerprint(
            [{"ordinal": a.ordinal, "sha256": a.sha256} for a in assets]
        )

    # ── Step 2: Compute semantic fingerprint from current revision ─────────────
    semantic_fp: str | None = None
    revision: ReceiptRevision | None = None
    if receipt.current_revision_id:
        rev_result = await session.execute(
            select(ReceiptRevision).where(ReceiptRevision.id == receipt.current_revision_id)
        )
        revision = rev_result.scalar_one_or_none()
        if revision is not None:
            li_result = await session.execute(
                select(LineItemRevision)
                .where(LineItemRevision.receipt_revision_id == revision.id)
                .order_by(LineItemRevision.ordinal)
            )
            line_items = list(li_result.scalars().all())
            semantic_fp = compute_semantic_fingerprint(
                merchant_normalized=revision.merchant_normalized,
                purchase_datetime=revision.purchase_datetime,
                currency=revision.currency,
                total_minor=revision.total_minor,
                line_items=[
                    {
                        "normalized_description": li.normalized_description,
                        "line_total_minor": li.line_total_minor,
                    }
                    for li in line_items
                ],
            )

    # Persist fingerprints early so subsequent queries can find them.
    receipt.evidence_fingerprint = evidence_fp
    receipt.semantic_fingerprint = semantic_fp
    session.add(receipt)
    await session.flush()

    # ── Step 3: Rule 2 — exact evidence fingerprint match ─────────────────────
    matched: Receipt | None = None
    method: str | None = None

    if evidence_fp is not None:
        ev_result = await session.execute(
            select(Receipt).where(
                Receipt.owner_id == owner_id,
                Receipt.evidence_fingerprint == evidence_fp,
                Receipt.id != receipt.id,
                Receipt.acknowledged_at.is_not(None),
            )
        )
        candidates = list(ev_result.scalars().all())
        if candidates:
            matched = _earliest(candidates)
            method = "exact_evidence"

    # ── Step 4: Rule 3 — exact semantic fingerprint match ─────────────────────
    if matched is None and semantic_fp is not None:
        sem_result = await session.execute(
            select(Receipt).where(
                Receipt.owner_id == owner_id,
                Receipt.semantic_fingerprint == semantic_fp,
                Receipt.id != receipt.id,
                Receipt.processing_status == "extracted",
            )
        )
        candidates = list(sem_result.scalars().all())
        if candidates:
            matched = _earliest(candidates)
            method = "exact_semantic"

    # ── Step 5: Confirmed duplicate path (Rules 2 + 3) ────────────────────────
    if matched is not None:
        candidates = candidates if candidates else [matched]
        cluster = _deduplicate_receipts([receipt, *candidates])
        canonical = _earliest(cluster)

        # Converge the whole visible cluster onto a direct canonical pointer.
        # Backfill processes oldest-first, while this also repairs an out-of-order
        # classification without deleting or merging any source evidence.
        for member in cluster:
            member_previous_status = member.deduplication_status
            if member.id == canonical.id:
                member.canonical_receipt_id = None
                member_status = DeduplicationStatus.UNIQUE
            else:
                member.canonical_receipt_id = canonical.id
                member_status = DeduplicationStatus.CONFIRMED_DUPLICATE
            _write_dedup_fields(member, member_status, method)
            _emit_event_if_changed(
                session,
                member,
                member_previous_status,
                member_status,
                method or "unknown",
                correlation_id,
                actor_type,
            )
            session.add(member)

        await session.flush()
        return DeduplicationStatus(receipt.deduplication_status)

    # ── Step 6: Rule 4 — partial structured match → suspected ─────────────────
    if revision is not None:
        suspected = await _find_partial_match(session, receipt, owner_id, revision)
        if suspected is not None:
            receipt.canonical_receipt_id = None
            new_status = DeduplicationStatus.SUSPECTED_DUPLICATE
            _write_dedup_fields(receipt, new_status, "partial_semantic")
            _emit_event_if_changed(
                session,
                receipt,
                prev_status,
                new_status,
                "partial_semantic",
                correlation_id,
                actor_type,
            )
            await session.flush()
            return new_status

    # ── Step 7: Rule 5 — unique ───────────────────────────────────────────────
    receipt.canonical_receipt_id = None
    new_status = DeduplicationStatus.UNIQUE
    _write_dedup_fields(receipt, new_status, None)
    _emit_event_if_changed(
        session,
        receipt,
        prev_status,
        new_status,
        "no_match",
        correlation_id,
        actor_type,
    )
    await session.flush()
    return new_status


def _earliest(candidates: list[Receipt]) -> Receipt:
    """Return the receipt with the earliest acknowledged_at; UUID tie-break."""
    _max_dt = datetime.max.replace(tzinfo=UTC)
    return min(
        candidates,
        key=lambda r: (
            r.acknowledged_at if r.acknowledged_at is not None else _max_dt,
            str(r.id),
        ),
    )


def _deduplicate_receipts(receipts: list[Receipt]) -> list[Receipt]:
    """Return one ORM object per receipt ID while preserving query order."""
    return list({receipt.id: receipt for receipt in receipts}.values())


async def _find_partial_match(
    session: AsyncSession,
    receipt: Receipt,
    owner_id: uuid.UUID,
    revision: ReceiptRevision,
) -> Receipt | None:
    """Rule 4: find a receipt sharing merchant, purchase date, currency, and total."""
    if (
        revision.merchant_normalized is None
        or revision.purchase_datetime is None
        or revision.currency is None
        or revision.total_minor is None
    ):
        return None

    stmt = (
        select(Receipt)
        .join(ReceiptRevision, ReceiptRevision.id == Receipt.current_revision_id)
        .where(
            Receipt.owner_id == owner_id,
            Receipt.id != receipt.id,
            Receipt.processing_status == "extracted",
            func.lower(ReceiptRevision.merchant_normalized)
            == func.lower(revision.merchant_normalized),
            cast(ReceiptRevision.purchase_datetime, Date) == cast(revision.purchase_datetime, Date),
            ReceiptRevision.currency == revision.currency,
            ReceiptRevision.total_minor == revision.total_minor,
        )
        .order_by(Receipt.acknowledged_at.asc().nulls_last(), Receipt.id.asc())
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


def _write_dedup_fields(
    receipt: Receipt,
    status: DeduplicationStatus,
    method: str | None,
) -> None:
    receipt.deduplication_status = status
    receipt.deduplication_method = method
    receipt.deduplication_rule_version = _DEDUP_RULE_VERSION
    receipt.deduplication_checked_at = _utc_now()


def _emit_event_if_changed(
    session: AsyncSession,
    receipt: Receipt,
    prev_status: str,
    new_status: DeduplicationStatus,
    reason_code: str,
    correlation_id: str,
    actor_type: ActorType,
) -> None:
    if str(prev_status) == str(new_status):
        return
    session.add(
        StateEvent(
            receipt_id=receipt.id,
            dimension=StateEventDimension.DEDUPLICATION,
            from_state=prev_status,
            to_state=new_status,
            actor_type=actor_type,
            reason_code=reason_code,
            correlation_id=correlation_id,
        )
    )
