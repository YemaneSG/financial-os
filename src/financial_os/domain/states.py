"""Processing and verification state enumerations with legal transition guards.

State machine (processing):
  reserved → uploading → uploaded → queued → processing → extracted
                                                         ↘ retryable_failed → queued
                                                         ↘ failed
  reserved | uploading → abandoned (reconciliation sweep only)
"""

from __future__ import annotations

from enum import StrEnum


class ProcessingStatus(StrEnum):
    RESERVED = "reserved"
    UPLOADING = "uploading"
    UPLOADED = "uploaded"
    QUEUED = "queued"
    PROCESSING = "processing"
    EXTRACTED = "extracted"
    RETRYABLE_FAILED = "retryable_failed"
    FAILED = "failed"
    ABANDONED = "abandoned"


class VerificationStatus(StrEnum):
    UNREVIEWED = "unreviewed"
    SYSTEM_VALIDATED = "system_validated"
    NEEDS_REVIEW = "needs_review"
    HUMAN_VERIFIED = "human_verified"


class FinancialContext(StrEnum):
    PERSONAL = "personal"
    RENTAL_PROPERTY = "rental_property"


class UploadStatus(StrEnum):
    RESERVED = "reserved"
    UPLOADED = "uploaded"
    VERIFIED = "verified"
    REJECTED = "rejected"


class AttemptStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    RETRYABLE_FAILED = "retryable_failed"
    TERMINAL_FAILED = "terminal_failed"
    SUCCEEDED = "succeeded"


class ExtractionRunStatus(StrEnum):
    STARTED = "started"
    SUCCEEDED = "succeeded"
    INVALID = "invalid"
    FAILED = "failed"


class RevisionSourceType(StrEnum):
    EXTRACTOR = "extractor"
    HUMAN = "human"
    IMPORT = "import"


class ValidationOutcome(StrEnum):
    PASS = "pass"  # noqa: S105 -- validation outcome, not a password
    WARN = "warn"
    FAIL = "fail"
    NOT_APPLICABLE = "not_applicable"


class DeduplicationStatus(StrEnum):
    UNCHECKED = "unchecked"
    UNIQUE = "unique"
    SUSPECTED_DUPLICATE = "suspected_duplicate"
    CONFIRMED_DUPLICATE = "confirmed_duplicate"


class StateEventDimension(StrEnum):
    PROCESSING = "processing"
    VERIFICATION = "verification"
    FINANCIAL_CONTEXT = "financial_context"
    DEDUPLICATION = "deduplication"


class ActorType(StrEnum):
    USER = "user"
    API = "api"
    WORKER = "worker"
    SCHEDULER = "scheduler"
    IMPORT = "import"


# ── Processing state machine ──────────────────────────────────────────────────

_PROCESSING_TRANSITIONS: dict[ProcessingStatus, frozenset[ProcessingStatus]] = {
    ProcessingStatus.RESERVED: frozenset(
        {
            ProcessingStatus.UPLOADING,
            ProcessingStatus.ABANDONED,
        }
    ),
    ProcessingStatus.UPLOADING: frozenset(
        {
            ProcessingStatus.UPLOADED,
            ProcessingStatus.ABANDONED,
        }
    ),
    ProcessingStatus.UPLOADED: frozenset(
        {
            ProcessingStatus.QUEUED,
        }
    ),
    ProcessingStatus.QUEUED: frozenset(
        {
            ProcessingStatus.PROCESSING,
        }
    ),
    ProcessingStatus.PROCESSING: frozenset(
        {
            ProcessingStatus.EXTRACTED,
            ProcessingStatus.RETRYABLE_FAILED,
            ProcessingStatus.FAILED,
        }
    ),
    ProcessingStatus.RETRYABLE_FAILED: frozenset(
        {
            ProcessingStatus.QUEUED,
        }
    ),
    ProcessingStatus.EXTRACTED: frozenset(),  # terminal
    ProcessingStatus.FAILED: frozenset(),  # terminal
    ProcessingStatus.ABANDONED: frozenset(),  # terminal
}

_VERIFICATION_TRANSITIONS: dict[VerificationStatus, frozenset[VerificationStatus]] = {
    VerificationStatus.UNREVIEWED: frozenset(
        {
            VerificationStatus.SYSTEM_VALIDATED,
            VerificationStatus.NEEDS_REVIEW,
        }
    ),
    VerificationStatus.SYSTEM_VALIDATED: frozenset(
        {
            VerificationStatus.HUMAN_VERIFIED,
            VerificationStatus.NEEDS_REVIEW,
        }
    ),
    VerificationStatus.NEEDS_REVIEW: frozenset(
        {
            VerificationStatus.HUMAN_VERIFIED,
        }
    ),
    VerificationStatus.HUMAN_VERIFIED: frozenset(),  # terminal; no automated process sets this
}

_TERMINAL_PROCESSING: frozenset[ProcessingStatus] = frozenset(
    {
        ProcessingStatus.EXTRACTED,
        ProcessingStatus.FAILED,
        ProcessingStatus.ABANDONED,
    }
)

_RETRYABLE_PROCESSING: frozenset[ProcessingStatus] = frozenset(
    {
        ProcessingStatus.RETRYABLE_FAILED,
    }
)


def can_transition_processing(from_status: ProcessingStatus, to_status: ProcessingStatus) -> bool:
    return to_status in _PROCESSING_TRANSITIONS.get(from_status, frozenset())


def can_transition_verification(
    from_status: VerificationStatus, to_status: VerificationStatus
) -> bool:
    return to_status in _VERIFICATION_TRANSITIONS.get(from_status, frozenset())


def is_terminal_processing(status: ProcessingStatus) -> bool:
    return status in _TERMINAL_PROCESSING


def is_retryable(status: ProcessingStatus) -> bool:
    return status in _RETRYABLE_PROCESSING


# Processing statuses that indicate the receipt is still in-flight (not yet acknowledged).
_PRE_ACKNOWLEDGED: frozenset[ProcessingStatus] = frozenset(
    {
        ProcessingStatus.RESERVED,
        ProcessingStatus.UPLOADING,
    }
)

# Statuses where re-enqueueing is idempotent (already in queue or processing).
_ALREADY_QUEUED_OR_PROCESSING: frozenset[ProcessingStatus] = frozenset(
    {
        ProcessingStatus.QUEUED,
        ProcessingStatus.PROCESSING,
    }
)


def is_pre_acknowledged(status: ProcessingStatus) -> bool:
    return status in _PRE_ACKNOWLEDGED


def is_already_queued_or_processing(status: ProcessingStatus) -> bool:
    return status in _ALREADY_QUEUED_OR_PROCESSING
