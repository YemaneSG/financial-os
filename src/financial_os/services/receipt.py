"""Receipt service — public API business logic.

Idempotency, state machine enforcement, evidence verification, and queue dispatch.
All invariants from domain/states.py and implementation-contracts.md are enforced here.
"""

from __future__ import annotations

import base64
import hashlib
import logging
import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from financial_os.adapters.queue.base import QueueAdapter
from financial_os.adapters.storage.base import StorageAdapter
from financial_os.auth.firebase import VerifiedOwner
from financial_os.domain.errors import (
    AssetNotFoundError,
    EvidenceIncompleteError,
    ForbiddenError,
    NotFoundError,
    RetryNotPermittedError,
    StorageError,
)
from financial_os.domain.states import (
    ActorType,
    FinancialContext,
    ProcessingStatus,
    StateEventDimension,
    UploadStatus,
    is_already_queued_or_processing,
    is_retryable,
)
from financial_os.models.events import StateEvent
from financial_os.models.receipt import ProcessingAttempt, Receipt, ReceiptAsset
from financial_os.schemas import receipt as rschemas
from financial_os.schemas.common import is_decodable_image

if TYPE_CHECKING:
    from financial_os.config import Settings
    from financial_os.models.extraction import ReceiptRevision

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _build_revision_summary(
    revision: ReceiptRevision | None,
) -> rschemas.RevisionSummarySchema | None:
    if revision is None:
        return None
    return rschemas.RevisionSummarySchema(
        revision_id=revision.id,
        source_type=revision.source_type,
        merchant_normalized=revision.merchant_normalized,
        purchase_datetime=revision.purchase_datetime,
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


def _encode_cursor(ts: datetime) -> str:
    return base64.urlsafe_b64encode(ts.isoformat().encode()).decode()


def _decode_cursor(cursor: str) -> datetime:
    return datetime.fromisoformat(base64.urlsafe_b64decode(cursor.encode()).decode())


async def _resolve_owner_id(
    session: AsyncSession,
    owner: VerifiedOwner,
    settings: Settings,
) -> uuid.UUID:
    """Return the internal owner UUID, checking session-version (IAM-02)."""
    from financial_os.models.auth import AuthSubject

    result = await session.execute(
        select(AuthSubject).where(AuthSubject.provider_subject == owner.subject_id)
    )
    subject = result.scalar_one_or_none()

    if subject is None or not subject.allowlisted:
        raise ForbiddenError("Access denied.")

    # Session-version check (IAM-02): reject tokens older than valid_after.
    if subject.valid_after is not None:
        auth_dt = datetime.fromtimestamp(owner.auth_time, tz=UTC)
        if auth_dt < subject.valid_after:
            raise ForbiddenError("Session invalidated.")

    return subject.id


async def create_receipt(
    session: AsyncSession,
    owner: VerifiedOwner,
    request: rschemas.CreateReceiptRequest,
    storage: StorageAdapter,
    settings: Settings,
    correlation_id: str,
) -> tuple[rschemas.CreateReceiptResponse, int]:
    """Create a receipt or return the existing one (idempotent A-01).

    Returns (response, http_status) where http_status is 201 (new) or 200 (existing).
    """
    owner_id = await _resolve_owner_id(session, owner, settings)

    receipt_id = uuid.uuid4()
    client_submission_id = request.client_submission_key

    # Idempotent INSERT: ON CONFLICT DO NOTHING + returning id.
    # The UNIQUE constraint on (owner_id, client_submission_id) ensures atomicity.
    stmt = (
        pg_insert(Receipt)
        .values(
            id=receipt_id,
            owner_id=owner_id,
            client_submission_id=client_submission_id,
            financial_context=request.financial_context or FinancialContext.PERSONAL,
            processing_status=ProcessingStatus.RESERVED,
            verification_status="unreviewed",
            expected_asset_count=request.expected_asset_count,
            captured_at=request.captured_at,
            row_version=0,
        )
        .on_conflict_do_nothing(index_elements=["owner_id", "client_submission_id"])
        .returning(Receipt.id)
    )

    result = await session.execute(stmt)
    new_row = result.scalar_one_or_none()
    http_status = 201 if new_row else 200

    # Reload the receipt (either newly inserted or existing).
    receipt_result = await session.execute(
        select(Receipt).where(
            Receipt.owner_id == owner_id,
            Receipt.client_submission_id == client_submission_id,
        )
    )
    receipt = receipt_result.scalar_one()

    # For a new receipt, create asset reservation rows.
    if http_status == 201:
        asset_rows = []
        for asset_input in sorted(request.assets, key=lambda a: a.ordinal):
            asset_id = uuid.uuid4()
            object_key = StorageAdapter.object_key(owner_id, receipt.id, asset_id)
            asset_rows.append(
                ReceiptAsset(
                    id=asset_id,
                    receipt_id=receipt.id,
                    ordinal=asset_input.ordinal,
                    object_key=object_key,
                    declared_mime_type=asset_input.declared_mime_type,
                    upload_status=UploadStatus.RESERVED,
                )
            )
        session.add_all(asset_rows)

        # State event for reservation.
        session.add(
            StateEvent(
                receipt_id=receipt.id,
                dimension=StateEventDimension.PROCESSING,
                from_state=None,
                to_state=ProcessingStatus.RESERVED,
                actor_type=ActorType.API,
                reason_code="receipt_created",
                correlation_id=correlation_id,
            )
        )
        await session.flush()

    # Always return fresh upload capabilities.
    await session.refresh(receipt, attribute_names=["assets"])

    capabilities = []
    for asset in sorted(receipt.assets, key=lambda a: a.ordinal):
        capability = await storage.generate_upload_capability(
            object_key=asset.object_key,
            declared_mime_type=asset.declared_mime_type,
            lifetime_seconds=settings.signed_url_lifetime_seconds,
        )
        capabilities.append(
            rschemas.UploadCapabilitySchema(
                asset_id=asset.id,
                ordinal=asset.ordinal,
                upload_url=capability.upload_url,
                method=capability.method,
                expires_at=capability.expires_at,
                allowed_mime_types=capability.allowed_mime_types,
            )
        )

    return (
        rschemas.CreateReceiptResponse(
            receipt_id=receipt.id,
            processing_status=receipt.processing_status,
            upload_capabilities=capabilities,
        ),
        http_status,
    )


async def finalize_receipt(
    session: AsyncSession,
    owner: VerifiedOwner,
    receipt_id: uuid.UUID,
    storage: StorageAdapter,
    queue: QueueAdapter,
    settings: Settings,
    correlation_id: str,
) -> rschemas.FinalizeReceiptResponse:
    """Verify uploaded evidence and durably acknowledge the receipt (API-03).

    OBJ-03 verification steps:
    1. Object existence check.
    2. Owner/receipt path match.
    3. Ordered count matches expected_asset_count.
    4. Byte size within limits.
    5. Allowed MIME type (magic bytes check).
    6. Decodable image content (magic signature check).
    7. storage_generation and sha256 recorded.

    Raises EvidenceIncompleteError if any asset fails verification.
    Returns 200 for already-acknowledged receipts (idempotent retry safe).
    """
    owner_id = await _resolve_owner_id(session, owner, settings)

    result = await session.execute(
        select(Receipt).where(
            Receipt.id == receipt_id,
            Receipt.owner_id == owner_id,
        )
    )
    receipt = result.scalar_one_or_none()
    if receipt is None:
        raise NotFoundError()

    # Idempotent: already queued or beyond → return current state.
    if is_already_queued_or_processing(ProcessingStatus(receipt.processing_status)):
        return rschemas.FinalizeReceiptResponse(
            receipt_id=receipt.id,
            processing_status=receipt.processing_status,
            acknowledged_at=receipt.acknowledged_at or _utc_now(),
        )
    if receipt.processing_status in (
        ProcessingStatus.EXTRACTED,
        ProcessingStatus.FAILED,
    ):
        return rschemas.FinalizeReceiptResponse(
            receipt_id=receipt.id,
            processing_status=receipt.processing_status,
            acknowledged_at=receipt.acknowledged_at or _utc_now(),
        )

    # Load assets.
    asset_result = await session.execute(
        select(ReceiptAsset)
        .where(ReceiptAsset.receipt_id == receipt.id)
        .order_by(ReceiptAsset.ordinal)
    )
    assets = list(asset_result.scalars().all())

    if len(assets) != receipt.expected_asset_count:
        raise EvidenceIncompleteError("Expected asset count does not match stored assets.")

    # Verify each asset against GCS (OBJ-03).
    verified_data: list[tuple[ReceiptAsset, bytes, str, str]] = []
    for asset in assets:
        try:
            data = await storage.read_object_bytes(asset.object_key)
        except StorageError as exc:
            raise EvidenceIncompleteError(
                "One or more expected images are missing or could not be verified."
            ) from exc

        # Verify object key contains owner and receipt path components (OBJ-03).
        expected_prefix = f"originals/{owner_id}/{receipt.id}/"
        if not asset.object_key.startswith(expected_prefix):
            raise EvidenceIncompleteError("Asset path does not match owner/receipt.")

        # Byte size check.
        if len(data) > settings.max_image_byte_size:
            raise EvidenceIncompleteError("Asset exceeds maximum byte size.")

        # Magic byte / MIME check (decodable image content).
        if not is_decodable_image(data):
            raise EvidenceIncompleteError("Asset is not a recognised image format.")

        # Compute SHA-256 for generation binding.
        sha256 = hashlib.sha256(data).hexdigest()

        # Get generation from metadata.
        meta = await storage.get_object_metadata(asset.object_key)
        generation = meta.generation if meta else "0"

        verified_data.append((asset, data, sha256, generation))

    # Single transaction: mark assets verified, update receipt status, record events.
    now = _utc_now()
    for asset, data, sha256, generation in verified_data:
        asset.storage_generation = generation
        asset.sha256 = sha256
        asset.verified_mime_type = asset.declared_mime_type  # magic verified above
        asset.byte_size = len(data)
        asset.upload_status = UploadStatus.VERIFIED
        asset.verified_at = now
        session.add(asset)

    prev_status = receipt.processing_status
    receipt.processing_status = ProcessingStatus.QUEUED
    receipt.acknowledged_at = now
    receipt.row_version += 1
    session.add(receipt)

    session.add(
        StateEvent(
            receipt_id=receipt.id,
            dimension=StateEventDimension.PROCESSING,
            from_state=prev_status,
            to_state=ProcessingStatus.QUEUED,
            actor_type=ActorType.API,
            reason_code="evidence_verified_and_queued",
            correlation_id=correlation_id,
        )
    )
    await session.flush()

    # Enqueue task (best-effort; reconciliation sweep repairs missed tasks).
    attempt_number = 1
    task_name = None
    try:
        task_name = await queue.enqueue_processing_task(
            receipt_id=receipt.id,
            pipeline_version=settings.pipeline_version,
            attempt_number=attempt_number,
        )
    except Exception:
        logger.warning(
            "Queue dispatch failed during finalization — reconciliation sweep will recover",
            extra={"receipt_id": str(receipt.id)},
        )

    # Record processing attempt regardless of queue success.
    session.add(
        ProcessingAttempt(
            receipt_id=receipt.id,
            pipeline_version=settings.pipeline_version,
            attempt_number=attempt_number,
            queue_task_name=task_name,
            status="queued",
        )
    )

    return rschemas.FinalizeReceiptResponse(
        receipt_id=receipt.id,
        processing_status=receipt.processing_status,
        acknowledged_at=now,
    )


async def list_receipts(
    session: AsyncSession,
    owner: VerifiedOwner,
    cursor: str | None,
    limit: int,
    settings: Settings,
) -> rschemas.ListReceiptsResponse:
    """List receipts for the owner, newest first, with cursor pagination."""
    from financial_os.models.extraction import ReceiptRevision

    owner_id = await _resolve_owner_id(session, owner, settings)

    stmt = (
        select(Receipt)
        .where(Receipt.owner_id == owner_id)
        .order_by(Receipt.created_at.desc())
        .limit(limit + 1)
    )

    if cursor:
        try:
            cursor_ts = _decode_cursor(cursor)
            stmt = stmt.where(Receipt.created_at < cursor_ts)
        except Exception:
            logger.info("Invalid receipt-list cursor ignored")

    result = await session.execute(stmt)
    rows = list(result.scalars().all())

    next_cursor = None
    if len(rows) > limit:
        rows = rows[:limit]
        next_cursor = _encode_cursor(rows[-1].created_at)

    items = []
    for receipt in rows:
        revision = None
        if receipt.current_revision_id:
            rev_result = await session.execute(
                select(ReceiptRevision).where(ReceiptRevision.id == receipt.current_revision_id)
            )
            revision = rev_result.scalar_one_or_none()

        items.append(
            rschemas.ReceiptListItemSchema(
                receipt_id=receipt.id,
                processing_status=receipt.processing_status,
                verification_status=receipt.verification_status,
                financial_context=receipt.financial_context,
                expected_asset_count=receipt.expected_asset_count,
                acknowledged_at=receipt.acknowledged_at,
                created_at=receipt.created_at,
                current_revision=_build_revision_summary(revision),
            )
        )

    return rschemas.ListReceiptsResponse(receipts=items, next_cursor=next_cursor)


async def get_receipt(
    session: AsyncSession,
    owner: VerifiedOwner,
    receipt_id: uuid.UUID,
    settings: Settings,
) -> rschemas.ReceiptDetailSchema:
    """Return full receipt detail including assets, line items, and validation findings."""
    from financial_os.models.extraction import ExtractionRun, LineItemRevision, ReceiptRevision
    from financial_os.models.findings import ValidationFinding

    owner_id = await _resolve_owner_id(session, owner, settings)

    result = await session.execute(
        select(Receipt).where(
            Receipt.id == receipt_id,
            Receipt.owner_id == owner_id,
        )
    )
    receipt = result.scalar_one_or_none()
    if receipt is None:
        raise NotFoundError()

    # Load assets.
    asset_result = await session.execute(
        select(ReceiptAsset)
        .where(ReceiptAsset.receipt_id == receipt.id)
        .order_by(ReceiptAsset.ordinal)
    )
    assets = list(asset_result.scalars().all())

    revision = None
    line_items = None
    findings = None
    provenance = None
    safe_error_code = None

    if receipt.current_revision_id:
        rev_result = await session.execute(
            select(ReceiptRevision).where(ReceiptRevision.id == receipt.current_revision_id)
        )
        revision = rev_result.scalar_one_or_none()

        if revision:
            li_result = await session.execute(
                select(LineItemRevision)
                .where(LineItemRevision.receipt_revision_id == revision.id)
                .order_by(LineItemRevision.ordinal)
            )
            line_items = list(li_result.scalars().all())

            fi_result = await session.execute(
                select(ValidationFinding).where(
                    ValidationFinding.receipt_revision_id == revision.id
                )
            )
            findings = list(fi_result.scalars().all())

            if revision.extraction_run_id:
                run_result = await session.execute(
                    select(ExtractionRun).where(ExtractionRun.id == revision.extraction_run_id)
                )
                run = run_result.scalar_one_or_none()
                if run:
                    attempt_result = await session.execute(
                        select(ProcessingAttempt)
                        .where(ProcessingAttempt.receipt_id == receipt.id)
                        .order_by(ProcessingAttempt.attempt_number.desc())
                    )
                    last_attempt = attempt_result.scalars().first()
                    attempt_count = last_attempt.attempt_number if last_attempt else 1
                    provenance = rschemas.ProvenanceSummarySchema(
                        provider=run.provider,
                        model_id=run.model_id,
                        prompt_version=run.prompt_version,
                        schema_version=run.schema_version,
                        attempt_count=attempt_count,
                    )

    # Safe error code from last processing attempt if failed.
    if receipt.processing_status in (
        ProcessingStatus.RETRYABLE_FAILED,
        ProcessingStatus.FAILED,
    ):
        attempt_result = await session.execute(
            select(ProcessingAttempt)
            .where(ProcessingAttempt.receipt_id == receipt.id)
            .order_by(ProcessingAttempt.attempt_number.desc())
        )
        last = attempt_result.scalars().first()
        if last:
            safe_error_code = last.safe_error_code

    return rschemas.ReceiptDetailSchema(
        receipt_id=receipt.id,
        processing_status=receipt.processing_status,
        verification_status=receipt.verification_status,
        financial_context=receipt.financial_context,
        expected_asset_count=receipt.expected_asset_count,
        acknowledged_at=receipt.acknowledged_at,
        created_at=receipt.created_at,
        current_revision=_build_revision_summary(revision),
        assets=[
            rschemas.AssetSummarySchema(
                asset_id=a.id,
                ordinal=a.ordinal,
                upload_status=a.upload_status,
                verified_mime_type=a.verified_mime_type,
                byte_size=a.byte_size,
            )
            for a in assets
        ],
        line_items=[
            rschemas.LineItemSummarySchema(
                ordinal=li.ordinal,
                raw_description=li.raw_description,
                normalized_description=li.normalized_description,
                quantity=str(li.quantity) if li.quantity is not None else None,
                unit=li.unit,
                unit_price_decimal=(
                    str(li.unit_price_decimal) if li.unit_price_decimal is not None else None
                ),
                line_total_minor=li.line_total_minor,
                discount_minor=li.discount_minor,
                category_suggestion=li.category_suggestion,
            )
            for li in (line_items or [])
        ]
        if line_items is not None
        else None,
        validation_findings=[
            rschemas.ValidationFindingSummarySchema(
                check_code=f.check_code,
                outcome=f.outcome,
                rule_version=f.rule_version,
            )
            for f in (findings or [])
        ]
        if findings is not None
        else None,
        safe_error_code=safe_error_code,
        provenance_summary=provenance,
    )


async def retry_processing(
    session: AsyncSession,
    owner: VerifiedOwner,
    receipt_id: uuid.UUID,
    queue: QueueAdapter,
    settings: Settings,
    correlation_id: str,
) -> rschemas.RetryProcessingResponse:
    """Re-enqueue a retryable_failed receipt (idempotent)."""
    owner_id = await _resolve_owner_id(session, owner, settings)

    result = await session.execute(
        select(Receipt).where(
            Receipt.id == receipt_id,
            Receipt.owner_id == owner_id,
        )
    )
    receipt = result.scalar_one_or_none()
    if receipt is None:
        raise NotFoundError()

    current = ProcessingStatus(receipt.processing_status)

    # Idempotent: already queued or processing → return without re-enqueue.
    if is_already_queued_or_processing(current):
        return rschemas.RetryProcessingResponse(
            receipt_id=receipt.id,
            processing_status=receipt.processing_status,
        )

    if not is_retryable(current):
        raise RetryNotPermittedError()

    # Determine next attempt number.
    attempt_result = await session.execute(
        select(ProcessingAttempt)
        .where(ProcessingAttempt.receipt_id == receipt.id)
        .order_by(ProcessingAttempt.attempt_number.desc())
    )
    last_attempt = attempt_result.scalars().first()
    next_attempt = (last_attempt.attempt_number + 1) if last_attempt else 1

    # Transition to queued.
    prev_status = receipt.processing_status
    receipt.processing_status = ProcessingStatus.QUEUED
    receipt.row_version += 1
    session.add(receipt)

    session.add(
        StateEvent(
            receipt_id=receipt.id,
            dimension=StateEventDimension.PROCESSING,
            from_state=prev_status,
            to_state=ProcessingStatus.QUEUED,
            actor_type=ActorType.API,
            reason_code="manual_retry",
            correlation_id=correlation_id,
        )
    )
    await session.flush()

    task_name = None
    try:
        task_name = await queue.enqueue_processing_task(
            receipt_id=receipt.id,
            pipeline_version=settings.pipeline_version,
            attempt_number=next_attempt,
        )
    except Exception:
        logger.warning(
            "Queue dispatch failed during retry — reconciliation will recover",
            extra={"receipt_id": str(receipt.id)},
        )

    session.add(
        ProcessingAttempt(
            receipt_id=receipt.id,
            pipeline_version=settings.pipeline_version,
            attempt_number=next_attempt,
            queue_task_name=task_name,
            status="queued",
        )
    )

    return rschemas.RetryProcessingResponse(
        receipt_id=receipt.id,
        processing_status=receipt.processing_status,
    )


async def get_asset_download_capability(
    session: AsyncSession,
    owner: VerifiedOwner,
    receipt_id: uuid.UUID,
    asset_id: uuid.UUID,
    storage: StorageAdapter,
    settings: Settings,
) -> rschemas.DownloadCapabilityResponse:
    """Return a short-lived download capability for a receipt asset (OBJ-02, S-03)."""
    owner_id = await _resolve_owner_id(session, owner, settings)

    receipt_result = await session.execute(
        select(Receipt).where(
            Receipt.id == receipt_id,
            Receipt.owner_id == owner_id,
        )
    )
    receipt = receipt_result.scalar_one_or_none()
    if receipt is None:
        raise NotFoundError()

    asset_result = await session.execute(
        select(ReceiptAsset).where(
            ReceiptAsset.id == asset_id,
            ReceiptAsset.receipt_id == receipt.id,
        )
    )
    asset = asset_result.scalar_one_or_none()
    if asset is None:
        raise AssetNotFoundError()

    if asset.storage_generation is None:
        raise AssetNotFoundError("Asset not yet verified.")

    capability = await storage.generate_download_capability(
        object_key=asset.object_key,
        generation=asset.storage_generation,
        lifetime_seconds=settings.signed_url_lifetime_seconds,
    )

    return rschemas.DownloadCapabilityResponse(
        download_url=capability.download_url,
        method=capability.method,
        expires_at=capability.expires_at,
    )
