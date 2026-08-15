"""Idempotent duplicate-detection backfill for existing extracted receipts.

Run as a one-shot pre-deploy step after migration 002 is applied.
Default mode is dry-run: prints privacy-safe aggregate counts without writing.

Usage:
    python -m financial_os.operations.backfill_dedup [--apply] [--batch-size N] [--limit N]

Outputs only privacy-safe aggregate counts. No merchant names, amounts, fingerprints,
owner identifiers, or receipt text appear in any output (AGENTS.md §7).
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from financial_os.domain.states import ActorType, DeduplicationStatus
from financial_os.models.receipt import Receipt
from financial_os.services.dedup import classify_receipt

logger = logging.getLogger(__name__)

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
    stream=sys.stderr,
)


async def _run_backfill(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    dry_run: bool,
    batch_size: int,
    limit: int | None,
) -> dict[str, int]:
    """Evaluate unchecked extracted receipts and (if not dry-run) write results.

    Returns privacy-safe aggregate counts only.
    Processes oldest-first so canonical selection is stable across runs.
    """
    if batch_size <= 0:
        raise ValueError("batch_size must be greater than zero")
    if limit is not None and limit <= 0:
        raise ValueError("limit must be greater than zero")

    counts: dict[str, int] = {
        "evaluated": 0,
        "unique": 0,
        "suspected_duplicate": 0,
        "confirmed_duplicate": 0,
    }

    # Collect IDs first to avoid holding a long-lived query cursor.
    async with session_factory() as session:
        stmt = (
            select(Receipt.id)
            .where(
                Receipt.processing_status == "extracted",
                Receipt.deduplication_status == DeduplicationStatus.UNCHECKED,
            )
            .order_by(Receipt.acknowledged_at.asc(), Receipt.id.asc())
        )
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await session.execute(stmt)
        receipt_ids: list[uuid.UUID] = [row[0] for row in result.all()]

    logger.info(
        "Backfill candidates found",
        extra={"count": len(receipt_ids), "dry_run": dry_run},
    )

    if dry_run:
        # One rollback-only transaction preserves prior preview fingerprints so
        # later candidates can be classified accurately, then discards every
        # projection and audit row atomically.
        async with session_factory() as session:
            try:
                for receipt_id in receipt_ids:
                    await _classify_one(session, receipt_id, counts)
            finally:
                await session.rollback()
        return counts

    for batch_start in range(0, len(receipt_ids), batch_size):
        batch = receipt_ids[batch_start : batch_start + batch_size]
        async with session_factory() as session, session.begin():
            for receipt_id in batch:
                await _classify_one(session, receipt_id, counts)

        logger.info(
            "Batch complete",
            extra={"batch_end": batch_start + len(batch), "total": len(receipt_ids)},
        )

    return counts


async def _classify_one(
    session: AsyncSession,
    receipt_id: uuid.UUID,
    counts: dict[str, int],
) -> None:
    receipt_result = await session.execute(select(Receipt).where(Receipt.id == receipt_id))
    receipt = receipt_result.scalar_one_or_none()
    if receipt is None:
        return

    counts["evaluated"] += 1
    status = await classify_receipt(
        session=session,
        receipt=receipt,
        correlation_id=f"backfill-{uuid.uuid4()}",
        actor_type=ActorType.SCHEDULER,
    )
    counts[status] = counts.get(status, 0) + 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Idempotent deduplication backfill for extracted receipts."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        default=False,
        help="Write results. Default is dry-run (no writes).",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        metavar="N",
        help="Receipts per transaction batch (default: 50).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        metavar="N",
        help="Maximum receipts to evaluate (for bounded runs).",
    )
    return parser


async def main() -> int:
    args = _build_parser().parse_args()
    dry_run = not args.apply

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL environment variable is required")
        return 1

    engine = create_async_engine(database_url, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    logger.info(
        "Starting deduplication backfill",
        extra={
            "dry_run": dry_run,
            "batch_size": args.batch_size,
            "limit": args.limit,
        },
    )

    counts = await _run_backfill(
        session_factory,
        dry_run=dry_run,
        batch_size=args.batch_size,
        limit=args.limit,
    )

    mode = "DRY RUN" if dry_run else "APPLIED"
    logger.info(
        "Backfill complete (%s)",
        mode,
        extra=counts,
    )
    print(
        f"\nDeduplication backfill — {mode}\n"
        f"  Evaluated:           {counts['evaluated']}\n"
        f"  Unique:              {counts.get('unique', 0)}\n"
        f"  Suspected duplicate: {counts.get('suspected_duplicate', 0)}\n"
        f"  Confirmed duplicate: {counts.get('confirmed_duplicate', 0)}\n"
    )
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
