"""Worker service — receipt extraction pipeline and reconciliation sweep.

Implements the extraction pipeline described in processReceipt (openapi.yaml):
1. Acquire idempotent processing lease (optimistic lock on row_version).
2. Read assets by storage_generation (S-01).
3. Verify SHA-256 matches recorded value.
4. Enforce input ceilings (implementation-contracts.md §8).
5. Strip EXIF metadata from images before sending to extractor.
6. Invoke ReceiptExtractor.extract().
7. Validate extraction output against versioned JSON Schema.
8. Run deterministic arithmetic checks.
9. Commit extraction run, revision, line items, findings, and state transitions atomically.

Returns 200 for both success and expected terminal failures (Cloud Tasks semantics).
Non-200 causes Cloud Tasks to retry — only returned for transient infrastructure failures.
"""

from __future__ import annotations

import hashlib
import io
import logging
import struct
import uuid
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

import jsonschema
from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from financial_os.adapters.extraction.base import AssetForExtraction, ExtractionAdapter
from financial_os.adapters.queue.base import QueueAdapter
from financial_os.adapters.storage.base import StorageAdapter
from financial_os.domain.errors import (
    CEILING_ASSET_BYTES,
    CEILING_ASSET_COUNT,
    CEILING_TOTAL_BYTES,
    COST_CIRCUIT_BREAKER,
    GENERATION_MISMATCH,
)
from financial_os.domain.money import compute_asset_manifest_hash
from financial_os.domain.states import (
    ActorType,
    AttemptStatus,
    ExtractionRunStatus,
    ProcessingStatus,
    RevisionSourceType,
    StateEventDimension,
)
from financial_os.models.events import StateEvent
from financial_os.models.extraction import ExtractionRun, LineItemRevision, ReceiptRevision
from financial_os.models.findings import ValidationFinding
from financial_os.models.receipt import ProcessingAttempt, Receipt, ReceiptAsset
from financial_os.schemas.worker import ProcessReceiptResponse, ReconcileProcessingResponse
from financial_os.services.validation import (
    determine_verification_status,
    run_deterministic_checks,
    validate_extraction_schema,
)

if TYPE_CHECKING:
    from financial_os.config import Settings

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(UTC)


# ── EXIF stripping ────────────────────────────────────────────────────────────


def _strip_jpeg_exif(data: bytes) -> bytes:
    """Remove Exif APP1 markers from JPEG without external dependencies.

    Known gap: HEIC/HEIF files are passed through without EXIF stripping.
    A full implementation requires Pillow + pillow-heif (see known-gaps).
    """
    if not data.startswith(b"\xff\xd8\xff"):
        return data

    out = io.BytesIO()
    out.write(b"\xff\xd8")
    i = 2
    while i < len(data) - 1:
        if data[i] != 0xFF:
            out.write(data[i:])
            break
        marker = data[i : i + 2]
        i += 2
        if marker in (b"\xff\xd9", b"\xff\xda"):
            # EOI or SOS: write remainder
            out.write(marker)
            out.write(data[i:])
            break
        if i + 2 > len(data):
            break
        length = struct.unpack(">H", data[i : i + 2])[0]
        segment_data = data[i : i + length]
        # Skip APP1 (Exif) and APP13 (IPTC) — may contain location/camera data.
        if marker in (b"\xff\xe1", b"\xff\xed"):
            i += length
            continue
        out.write(marker)
        out.write(segment_data)
        i += length

    return out.getvalue()


def _strip_png_exif(data: bytes) -> bytes:
    """Remove eXIf chunk from PNG. Passes non-PNG data through unchanged."""
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        return data

    out = io.BytesIO()
    out.write(data[:8])
    i = 8
    while i < len(data):
        if i + 8 > len(data):
            break
        length = struct.unpack(">I", data[i : i + 4])[0]
        chunk_type = data[i + 4 : i + 8]
        chunk_end = i + 12 + length
        if chunk_type in (b"eXIf", b"iTXt", b"tEXt"):
            i = chunk_end
            continue
        out.write(data[i:chunk_end])
        i = chunk_end

    return out.getvalue()


def strip_exif(data: bytes, mime_type: str) -> bytes:
    """Strip EXIF metadata from image bytes before sending to extractor.

    Privacy control: prevents leaking GPS location, device identifiers, or
    capture metadata from receipt images to the extraction provider (AI-01).
    """
    if mime_type in ("image/jpeg", "image/jpg"):
        return _strip_jpeg_exif(data)
    if mime_type == "image/png":
        return _strip_png_exif(data)
    # HEIC/WEBP: pass through — HEIC stripping requires pillow-heif (known gap).
    return data


# ── Worker pipeline ───────────────────────────────────────────────────────────


async def process_receipt(
    session: AsyncSession,
    receipt_id: uuid.UUID,
    pipeline_version: str,
    attempt_number: int,
    task_name: str | None,
    extractor: ExtractionAdapter,
    storage: StorageAdapter,
    settings: Settings,
    correlation_id: str,
) -> ProcessReceiptResponse:
    """Execute one extraction attempt for a receipt.

    Returns a 200-class response for both success and expected failures.
    Cloud Tasks retries on non-200 — only transient infrastructure failures
    should raise unhandled exceptions.
    """
    # Load receipt.
    result = await session.execute(select(Receipt).where(Receipt.id == receipt_id))
    receipt = result.scalar_one_or_none()
    if receipt is None:
        logger.error("Worker received unknown receipt_id", extra={"receipt_id": str(receipt_id)})
        return ProcessReceiptResponse(
            receipt_id=receipt_id,
            outcome="terminal_failed",
            safe_error_code="RECEIPT_NOT_FOUND",
        )

    current_status = ProcessingStatus(receipt.processing_status)

    # Idempotent: already succeeded or terminal → no-op.
    if current_status == ProcessingStatus.EXTRACTED:
        return ProcessReceiptResponse(receipt_id=receipt_id, outcome="no_op")
    if current_status == ProcessingStatus.FAILED:
        return ProcessReceiptResponse(
            receipt_id=receipt_id, outcome="no_op", safe_error_code="ALREADY_TERMINAL"
        )

    # Acquire processing lease via optimistic lock on row_version (A-01 §2.2).
    current_version = receipt.row_version
    update_stmt = (
        update(Receipt)
        .where(
            Receipt.id == receipt_id,
            Receipt.processing_status == ProcessingStatus.QUEUED,
            Receipt.row_version == current_version,
        )
        .values(
            processing_status=ProcessingStatus.PROCESSING,
            row_version=current_version + 1,
        )
        .returning(Receipt.id)
    )
    lock_result = await session.execute(update_stmt)
    if lock_result.scalar_one_or_none() is None:
        # Another worker holds the lease or status already advanced.
        logger.info(
            "Worker lease not acquired — no-op",
            extra={"receipt_id": str(receipt_id)},
        )
        return ProcessReceiptResponse(receipt_id=receipt_id, outcome="no_op")

    await session.flush()

    # Record state event for lease acquisition.
    session.add(
        StateEvent(
            receipt_id=receipt.id,
            dimension=StateEventDimension.PROCESSING,
            from_state=ProcessingStatus.QUEUED,
            to_state=ProcessingStatus.PROCESSING,
            actor_type=ActorType.WORKER,
            reason_code="worker_lease_acquired",
            correlation_id=correlation_id,
        )
    )

    # Insert or find processing attempt row (idempotent on unique constraint).
    attempt_id = uuid.uuid4()
    attempt_stmt = (
        pg_insert(ProcessingAttempt)
        .values(
            id=attempt_id,
            receipt_id=receipt_id,
            pipeline_version=pipeline_version,
            attempt_number=attempt_number,
            queue_task_name=task_name,
            status=AttemptStatus.RUNNING,
            started_at=_utc_now(),
        )
        .on_conflict_do_nothing(index_elements=["receipt_id", "pipeline_version", "attempt_number"])
        .returning(ProcessingAttempt.id)
    )

    attempt_result = await session.execute(attempt_stmt)
    resolved_attempt_id = attempt_result.scalar_one_or_none()
    if resolved_attempt_id is None:
        # Duplicate delivery — attempt row already exists.
        existing = await session.execute(
            select(ProcessingAttempt).where(
                ProcessingAttempt.receipt_id == receipt_id,
                ProcessingAttempt.pipeline_version == pipeline_version,
                ProcessingAttempt.attempt_number == attempt_number,
            )
        )
        attempt_row = existing.scalar_one()
        attempt_id = attempt_row.id
    else:
        attempt_id = resolved_attempt_id

    await session.flush()

    # Load verified assets ordered by ordinal.
    asset_result = await session.execute(
        select(ReceiptAsset)
        .where(
            ReceiptAsset.receipt_id == receipt_id,
            ReceiptAsset.upload_status == "verified",
        )
        .order_by(ReceiptAsset.ordinal)
    )
    assets = list(asset_result.scalars().all())

    try:
        outcome, safe_error_code = await _run_extraction_pipeline(
            session=session,
            receipt=receipt,
            assets=assets,
            attempt_id=attempt_id,
            pipeline_version=pipeline_version,
            extractor=extractor,
            storage=storage,
            settings=settings,
            correlation_id=correlation_id,
        )
    except Exception:
        # Unexpected infrastructure failure — return retryable status so Cloud Tasks retries.
        logger.exception(
            "Unexpected worker error",
            extra={"receipt_id": str(receipt_id)},
        )
        await _mark_attempt_failed(
            session,
            attempt_id,
            receipt,
            "WORKER_ERROR",
            correlation_id,
        )
        return ProcessReceiptResponse(
            receipt_id=receipt_id,
            outcome="retryable_failed",
            safe_error_code="WORKER_ERROR",
        )

    return ProcessReceiptResponse(
        receipt_id=receipt_id,
        outcome=outcome,
        safe_error_code=safe_error_code,
    )


async def _run_extraction_pipeline(
    session: AsyncSession,
    receipt: Receipt,
    assets: list[ReceiptAsset],
    attempt_id: uuid.UUID,
    pipeline_version: str,
    extractor: ExtractionAdapter,
    storage: StorageAdapter,
    settings: Settings,
    correlation_id: str,
) -> tuple[str, str | None]:
    """Run the full extraction pipeline; return (outcome, safe_error_code)."""

    # ── Ceiling checks (implementation-contracts.md §8) ───────────────────────
    if len(assets) > settings.worker_max_assets_per_extraction:
        await _mark_attempt_terminal(
            session, attempt_id, receipt, CEILING_ASSET_COUNT, correlation_id
        )
        return "terminal_failed", CEILING_ASSET_COUNT

    # ── Read assets from GCS with generation pinning (S-01) ──────────────────
    asset_blobs: list[tuple[ReceiptAsset, bytes]] = []
    total_bytes = 0
    for asset in assets:
        try:
            data = await storage.read_object_bytes(asset.object_key, asset.storage_generation)
        except Exception:
            await _mark_attempt_terminal(
                session, attempt_id, receipt, GENERATION_MISMATCH, correlation_id
            )
            return "terminal_failed", GENERATION_MISMATCH

        # Verify SHA-256 matches recorded value (S-01).
        observed_sha256 = hashlib.sha256(data).hexdigest()
        if observed_sha256 != asset.sha256:
            logger.error(
                "Generation mismatch detected",
                extra={"receipt_id": str(receipt.id), "asset_id": str(asset.id)},
            )
            await _mark_attempt_terminal(
                session, attempt_id, receipt, GENERATION_MISMATCH, correlation_id
            )
            return "terminal_failed", GENERATION_MISMATCH

        if len(data) > settings.worker_max_asset_bytes:
            await _mark_attempt_terminal(
                session, attempt_id, receipt, CEILING_ASSET_BYTES, correlation_id
            )
            return "terminal_failed", CEILING_ASSET_BYTES

        total_bytes += len(data)
        if total_bytes > settings.worker_max_total_extraction_bytes:
            await _mark_attempt_terminal(
                session, attempt_id, receipt, CEILING_TOTAL_BYTES, correlation_id
            )
            return "terminal_failed", CEILING_TOTAL_BYTES

        asset_blobs.append((asset, data))

    # ── Compute manifest hash (A-03) ──────────────────────────────────────────
    manifest_entries = [
        {"ordinal": a.ordinal, "object_key": a.object_key, "sha256": a.sha256}
        for a, _ in asset_blobs
    ]
    manifest_hash = compute_asset_manifest_hash(manifest_entries)

    # ── Strip EXIF before sending to provider (AI-01) ─────────────────────────
    extraction_assets = []
    for asset, data in asset_blobs:
        stripped = strip_exif(data, asset.verified_mime_type or asset.declared_mime_type)
        extraction_assets.append(
            AssetForExtraction(
                ordinal=asset.ordinal,
                data=stripped,
                mime_type=asset.verified_mime_type or asset.declared_mime_type,
                sha256=asset.sha256 or "",
            )
        )

    # ── Record extraction run start ───────────────────────────────────────────
    run_id = uuid.uuid4()
    run = ExtractionRun(
        id=run_id,
        receipt_id=receipt.id,
        processing_attempt_id=attempt_id,
        provider=extractor.provider_name,
        model_id=extractor.model_id,
        prompt_version=extractor.prompt_version,
        schema_version=extractor.schema_version,
        asset_manifest_hash=manifest_hash,
        status=ExtractionRunStatus.STARTED,
        input_metadata={
            "asset_count": len(assets),
            "total_bytes": total_bytes,
        },
    )
    session.add(run)
    await session.flush()

    # ── Call extractor (AI-01: no tools, credentials, or browsing) ────────────
    try:
        result = await extractor.extract(extraction_assets)
    except Exception:
        logger.warning(
            "Extraction provider call failed",
            extra={"receipt_id": str(receipt.id), "attempt_id": str(attempt_id)},
        )
        run.status = ExtractionRunStatus.FAILED
        run.completed_at = _utc_now()
        session.add(run)
        await _mark_attempt_terminal(
            session, attempt_id, receipt, "EXTRACTION_PROVIDER_ERROR", correlation_id
        )
        return "retryable_failed", "EXTRACTION_PROVIDER_ERROR"

    run.raw_response = result.raw
    run.latency_ms = result.latency_ms
    run.provider_request_id = result.provider_request_id

    # Cost circuit breaker (implementation-contracts.md §8.3).
    if (
        result.estimated_cost_cents is not None
        and result.estimated_cost_cents > settings.worker_max_extraction_cost_cents
    ):
        run.status = ExtractionRunStatus.FAILED
        run.completed_at = _utc_now()
        session.add(run)
        await _mark_attempt_terminal(
            session, attempt_id, receipt, COST_CIRCUIT_BREAKER, correlation_id
        )
        logger.error(
            "Extraction cost ceiling exceeded",
            extra={"receipt_id": str(receipt.id), "cost_cents": result.estimated_cost_cents},
        )
        return "terminal_failed", COST_CIRCUIT_BREAKER

    # ── Validate extraction output (AI-03, VAL-001) ───────────────────────────
    try:
        validate_extraction_schema(result.raw)
    except jsonschema.ValidationError:
        run.status = ExtractionRunStatus.INVALID
        run.completed_at = _utc_now()
        session.add(run)
        await _mark_attempt_failed(
            session, attempt_id, receipt, "SCHEMA_VALIDATION_FAILED", correlation_id
        )
        return "retryable_failed", "SCHEMA_VALIDATION_FAILED"

    # ── Run deterministic arithmetic checks ───────────────────────────────────
    finding_data = run_deterministic_checks(result.raw)
    verification_status = determine_verification_status(finding_data)

    # ── Promote to revision (atomic transaction) ──────────────────────────────
    raw = result.raw
    now = _utc_now()

    # Parse purchase_datetime from date + time + timezone fields.
    purchase_datetime = _parse_purchase_datetime(raw)

    # Check for duplicate manifest hash before inserting revision (A-01 §2.2).
    existing_rev = await session.execute(
        select(ReceiptRevision)
        .where(
            ReceiptRevision.receipt_id == receipt.id,
            ExtractionRun.asset_manifest_hash == manifest_hash,
        )
        .join(ExtractionRun, ExtractionRun.id == ReceiptRevision.extraction_run_id)
    )
    duplicate_revision = existing_rev.scalar_one_or_none()

    if duplicate_revision is not None:
        # Same evidence set already produced a revision — update pointer and skip re-insert.
        run.status = ExtractionRunStatus.SUCCEEDED
        run.completed_at = now
        session.add(run)
        receipt.current_revision_id = duplicate_revision.id
    else:
        # Insert immutable revision.
        revision_id = uuid.uuid4()
        revision = ReceiptRevision(
            id=revision_id,
            receipt_id=receipt.id,
            source_type=RevisionSourceType.EXTRACTOR,
            extraction_run_id=run_id,
            merchant_raw=raw.get("merchant_raw"),
            merchant_normalized=raw.get("merchant_normalized"),
            purchase_datetime=purchase_datetime,
            purchase_timezone=raw.get("purchase_timezone"),
            currency=raw.get("currency", "USD"),
            subtotal_minor=raw.get("subtotal_minor"),
            tax_minor=raw.get("tax_minor"),
            tip_minor=raw.get("tip_minor"),
            discount_minor=raw.get("discount_minor"),
            total_minor=raw.get("total_minor"),
            payment_method_hint=raw.get("payment_method_hint"),
            overall_confidence=raw.get("overall_confidence"),
        )
        session.add(revision)
        await session.flush()

        # Insert line items.
        for item in raw.get("line_items") or []:
            from decimal import Decimal

            qty = Decimal(item["quantity"]) if item.get("quantity") else None
            price = Decimal(item["unit_price_decimal"]) if item.get("unit_price_decimal") else None
            session.add(
                LineItemRevision(
                    receipt_revision_id=revision_id,
                    ordinal=item["ordinal"],
                    raw_description=item["raw_description"],
                    normalized_description=item.get("normalized_description"),
                    quantity=qty,
                    unit=item.get("unit"),
                    unit_price_decimal=price,
                    line_total_minor=item.get("line_total_minor"),
                    discount_minor=item.get("discount_minor"),
                    category_suggestion=item.get("category_suggestion"),
                    field_confidence=item.get("field_confidence") or {},
                )
            )

        # Insert validation findings.
        for fd in finding_data:
            session.add(
                ValidationFinding(
                    receipt_revision_id=revision_id,
                    check_code=fd.check_code,
                    outcome=fd.outcome,
                    observed=fd.observed,
                    expected=fd.expected,
                    rule_version=fd.rule_version,
                )
            )

        # Update receipt: current revision pointer + processing/verification status.
        receipt.current_revision_id = revision_id
        run.status = ExtractionRunStatus.SUCCEEDED
        run.completed_at = now

    receipt.processing_status = ProcessingStatus.EXTRACTED
    receipt.verification_status = verification_status
    receipt.row_version += 1
    session.add(receipt)
    session.add(run)

    # Complete processing attempt.
    attempt_result = await session.execute(
        select(ProcessingAttempt).where(ProcessingAttempt.id == attempt_id)
    )
    attempt = attempt_result.scalar_one_or_none()
    if attempt:
        attempt.status = AttemptStatus.SUCCEEDED
        attempt.completed_at = now
        session.add(attempt)

    # Append state events.
    session.add(
        StateEvent(
            receipt_id=receipt.id,
            dimension=StateEventDimension.PROCESSING,
            from_state=ProcessingStatus.PROCESSING,
            to_state=ProcessingStatus.EXTRACTED,
            actor_type=ActorType.WORKER,
            reason_code="extraction_succeeded",
            correlation_id=correlation_id,
        )
    )
    session.add(
        StateEvent(
            receipt_id=receipt.id,
            dimension=StateEventDimension.VERIFICATION,
            from_state="unreviewed",
            to_state=verification_status,
            actor_type=ActorType.WORKER,
            reason_code="validation_checks_complete",
            correlation_id=correlation_id,
        )
    )

    return "succeeded", None


async def _mark_attempt_terminal(
    session: AsyncSession,
    attempt_id: uuid.UUID,
    receipt: Receipt,
    safe_error_code: str,
    correlation_id: str,
) -> None:
    now = _utc_now()
    result = await session.execute(
        select(ProcessingAttempt).where(ProcessingAttempt.id == attempt_id)
    )
    attempt = result.scalar_one_or_none()
    if attempt:
        attempt.status = AttemptStatus.TERMINAL_FAILED
        attempt.safe_error_code = safe_error_code
        attempt.completed_at = now
        session.add(attempt)

    receipt.processing_status = ProcessingStatus.FAILED
    receipt.row_version += 1
    session.add(receipt)

    session.add(
        StateEvent(
            receipt_id=receipt.id,
            dimension=StateEventDimension.PROCESSING,
            from_state=ProcessingStatus.PROCESSING,
            to_state=ProcessingStatus.FAILED,
            actor_type=ActorType.WORKER,
            reason_code=safe_error_code,
            correlation_id=correlation_id,
        )
    )


async def _mark_attempt_failed(
    session: AsyncSession,
    attempt_id: uuid.UUID,
    receipt: Receipt,
    safe_error_code: str,
    correlation_id: str,
) -> None:
    now = _utc_now()
    result = await session.execute(
        select(ProcessingAttempt).where(ProcessingAttempt.id == attempt_id)
    )
    attempt = result.scalar_one_or_none()
    if attempt:
        attempt.status = AttemptStatus.RETRYABLE_FAILED
        attempt.safe_error_code = safe_error_code
        attempt.completed_at = now
        session.add(attempt)

    receipt.processing_status = ProcessingStatus.RETRYABLE_FAILED
    receipt.row_version += 1
    session.add(receipt)

    session.add(
        StateEvent(
            receipt_id=receipt.id,
            dimension=StateEventDimension.PROCESSING,
            from_state=ProcessingStatus.PROCESSING,
            to_state=ProcessingStatus.RETRYABLE_FAILED,
            actor_type=ActorType.WORKER,
            reason_code=safe_error_code,
            correlation_id=correlation_id,
        )
    )


def _parse_purchase_datetime(raw: dict[str, Any]) -> datetime | None:
    """Parse purchase_date + purchase_time into a UTC-aware datetime.

    Does not invent a timezone when not evidenced on the receipt (data-architecture §7).
    """
    date_str = raw.get("purchase_date")
    time_str = raw.get("purchase_time")
    tz_str = raw.get("purchase_timezone")

    if not date_str:
        return None

    try:
        from datetime import date, time

        d = date.fromisoformat(date_str)

        if time_str:
            parts = time_str.split(":")
            h, m, s = int(parts[0]), int(parts[1]), int(parts[2]) if len(parts) > 2 else 0
            t = time(h, m, s)
        else:
            t = time(0, 0, 0)

        if tz_str:
            import zoneinfo

            try:
                tz = zoneinfo.ZoneInfo(tz_str)
                return datetime(d.year, d.month, d.day, t.hour, t.minute, t.second, tzinfo=tz)
            except (ValueError, zoneinfo.ZoneInfoNotFoundError):
                logger.info("Invalid purchase timezone ignored")

        # No timezone known — store as naive (UTC-consistent with purchase_timezone=NULL).
        return datetime(d.year, d.month, d.day, t.hour, t.minute, t.second)
    except Exception:
        return None


# ── Reconciliation sweep ──────────────────────────────────────────────────────


async def reconcile_processing(
    session: AsyncSession,
    queue: QueueAdapter,
    settings: Settings,
    correlation_id: str,
) -> ReconcileProcessingResponse:
    """Idempotent stale-work sweep triggered by Cloud Scheduler.

    Detects and repairs:
    - Reserved/uploading receipts past stale threshold → abandoned.
    - Uploaded receipts not yet queued → re-enqueue.
    - Queued receipts past the stale threshold → dispatch a new attempt.
    - Processing receipts past the lease threshold → flag for manual review.

    Never deletes evidence (OBJ-04, REL-001).
    """
    now = _utc_now()
    evaluated = 0
    re_enqueued = 0
    flagged = 0

    # ── Abandon stale pre-acknowledged receipts ───────────────────────────────
    stale_uploading_cutoff = now - timedelta(seconds=settings.reconcile_uploading_stale_seconds)
    stale_reserved = await session.execute(
        select(Receipt).where(
            Receipt.processing_status.in_([ProcessingStatus.RESERVED, ProcessingStatus.UPLOADING]),
            Receipt.created_at < stale_uploading_cutoff,
        )
    )
    for receipt in stale_reserved.scalars():
        evaluated += 1
        prev = receipt.processing_status
        receipt.processing_status = ProcessingStatus.ABANDONED
        receipt.row_version += 1
        session.add(receipt)
        session.add(
            StateEvent(
                receipt_id=receipt.id,
                dimension=StateEventDimension.PROCESSING,
                from_state=prev,
                to_state=ProcessingStatus.ABANDONED,
                actor_type=ActorType.SCHEDULER,
                reason_code="stale_pre_acknowledged",
                correlation_id=correlation_id,
            )
        )

    # ── Re-enqueue uploaded receipts not yet queued ───────────────────────────
    stale_uploaded = await session.execute(
        select(Receipt).where(Receipt.processing_status == ProcessingStatus.UPLOADED)
    )
    for receipt in stale_uploaded.scalars():
        evaluated += 1
        prev = receipt.processing_status
        receipt.processing_status = ProcessingStatus.QUEUED
        receipt.row_version += 1
        session.add(receipt)
        session.add(
            StateEvent(
                receipt_id=receipt.id,
                dimension=StateEventDimension.PROCESSING,
                from_state=prev,
                to_state=ProcessingStatus.QUEUED,
                actor_type=ActorType.SCHEDULER,
                reason_code="reconcile_re_enqueue",
                correlation_id=correlation_id,
            )
        )
        try:
            await queue.enqueue_processing_task(
                receipt_id=receipt.id,
                pipeline_version=settings.pipeline_version,
                attempt_number=1,
            )
            re_enqueued += 1
        except Exception:
            logger.warning(
                "Reconcile queue dispatch failed",
                extra={"receipt_id": str(receipt.id)},
            )

    # ── Recover queued receipts whose task was never delivered ────────────────
    stale_queued_cutoff = now - timedelta(seconds=settings.reconcile_queued_stale_seconds)
    stale_queued = await session.execute(
        select(Receipt).where(
            Receipt.processing_status == ProcessingStatus.QUEUED,
            Receipt.updated_at < stale_queued_cutoff,
        )
    )
    for receipt in stale_queued.scalars():
        evaluated += 1
        latest_attempt = await session.execute(
            select(func.max(ProcessingAttempt.attempt_number)).where(
                ProcessingAttempt.receipt_id == receipt.id,
                ProcessingAttempt.pipeline_version == settings.pipeline_version,
            )
        )
        next_attempt = (latest_attempt.scalar_one_or_none() or 0) + 1
        try:
            task_name = await queue.enqueue_processing_task(
                receipt_id=receipt.id,
                pipeline_version=settings.pipeline_version,
                attempt_number=next_attempt,
            )
            session.add(
                ProcessingAttempt(
                    receipt_id=receipt.id,
                    pipeline_version=settings.pipeline_version,
                    attempt_number=next_attempt,
                    queue_task_name=task_name,
                    status=AttemptStatus.QUEUED,
                )
            )
            re_enqueued += 1
            reason_code = "reconcile_queued_re_enqueue"
        except Exception:
            flagged += 1
            reason_code = "reconcile_queued_dispatch_failed"
            logger.warning(
                "Reconcile queued dispatch failed",
                extra={"receipt_id": str(receipt.id)},
            )
        session.add(
            StateEvent(
                receipt_id=receipt.id,
                dimension=StateEventDimension.PROCESSING,
                from_state=ProcessingStatus.QUEUED,
                to_state=ProcessingStatus.QUEUED,
                actor_type=ActorType.SCHEDULER,
                reason_code=reason_code,
                correlation_id=correlation_id,
            )
        )

    # ── Flag stale processing leases for manual review ────────────────────────
    stale_processing_cutoff = now - timedelta(seconds=settings.reconcile_processing_stale_seconds)

    stale_processing = await session.execute(
        select(Receipt).where(
            Receipt.processing_status == ProcessingStatus.PROCESSING,
            Receipt.updated_at < stale_processing_cutoff,
        )
    )
    for receipt in stale_processing.scalars():
        evaluated += 1
        flagged += 1
        session.add(
            StateEvent(
                receipt_id=receipt.id,
                dimension=StateEventDimension.PROCESSING,
                from_state=receipt.processing_status,
                to_state=receipt.processing_status,
                actor_type=ActorType.SCHEDULER,
                reason_code="reconcile_stale_flag",
                correlation_id=correlation_id,
            )
        )
        logger.warning(
            "Stale in-flight receipt flagged for manual review",
            extra={"receipt_id": str(receipt.id), "status": receipt.processing_status},
        )

    await session.flush()

    return ReconcileProcessingResponse(
        evaluated_count=evaluated,
        re_enqueued_count=re_enqueued,
        flagged_count=flagged,
    )
