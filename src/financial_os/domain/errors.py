"""Domain error classes.

All errors exposed to clients use privacy-safe codes and messages that contain
no receipt content, credentials, signed URLs, or internal identifiers.
"""

from __future__ import annotations


class FinancialOsError(Exception):
    """Base class for all application errors."""

    safe_error_code: str = "INTERNAL_ERROR"
    http_status: int = 500
    message: str = "An unexpected error occurred."

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.__class__.message
        super().__init__(self.message)


class NotFoundError(FinancialOsError):
    safe_error_code = "RECEIPT_NOT_FOUND"
    http_status = 404
    message = "Receipt not found."


class AssetNotFoundError(FinancialOsError):
    safe_error_code = "ASSET_NOT_FOUND"
    http_status = 404
    message = "Asset not found."


class ConflictError(FinancialOsError):
    safe_error_code = "CONFLICT"
    http_status = 409
    message = "State conflict."


class RetryNotPermittedError(ConflictError):
    safe_error_code = "RETRY_NOT_PERMITTED"
    message = "Receipt is not in a retryable state."


class StaleParentRevisionError(ConflictError):
    safe_error_code = "STALE_PARENT_REVISION"
    message = "The expected parent revision does not match the current revision."


class InvalidReceiptStateError(ConflictError):
    safe_error_code = "INVALID_RECEIPT_STATE"
    message = "Receipt is not in a state that allows human correction."


class EvidenceIncompleteError(FinancialOsError):
    safe_error_code = "EVIDENCE_INCOMPLETE"
    http_status = 422
    message = "One or more expected images are missing or could not be verified."


class ValidationError(FinancialOsError):
    safe_error_code = "VALIDATION_ERROR"
    http_status = 422
    message = "Request validation failed."


class InvalidStateTransitionError(FinancialOsError):
    safe_error_code = "INVALID_STATE_TRANSITION"
    http_status = 409
    message = "The requested state transition is not permitted."


class UnauthorizedError(FinancialOsError):
    safe_error_code = "UNAUTHORIZED"
    http_status = 401
    message = "Authentication required."


class ForbiddenError(FinancialOsError):
    safe_error_code = "FORBIDDEN"
    http_status = 403
    message = "Access denied."


class StorageError(FinancialOsError):
    safe_error_code = "STORAGE_ERROR"
    http_status = 500
    message = "Storage operation failed."


class QueueError(FinancialOsError):
    safe_error_code = "QUEUE_ERROR"
    http_status = 500
    message = "Queue operation failed."


# ── Worker-specific safe error codes ─────────────────────────────────────────

CEILING_ASSET_COUNT = "CEILING_ASSET_COUNT"
CEILING_ASSET_BYTES = "CEILING_ASSET_BYTES"
CEILING_TOTAL_BYTES = "CEILING_TOTAL_BYTES"
CEILING_COST = "CEILING_COST"
COST_CIRCUIT_BREAKER = "COST_CIRCUIT_BREAKER"
GENERATION_MISMATCH = "GENERATION_MISMATCH"
SCHEMA_VALIDATION_FAILED = "SCHEMA_VALIDATION_FAILED"
ARITHMETIC_VALIDATION_FAILED = "ARITHMETIC_VALIDATION_FAILED"
EXTRACTION_PROVIDER_ERROR = "EXTRACTION_PROVIDER_ERROR"
LEASE_LOST = "LEASE_LOST"


class WorkerCeilingError(FinancialOsError):
    """Terminal: extraction inputs exceed a configured ceiling."""

    http_status = 200  # Worker always returns 200; outcome recorded in DB.

    def __init__(self, safe_error_code: str, message: str) -> None:
        self.safe_error_code = safe_error_code
        super().__init__(message)


class GenerationMismatchError(FinancialOsError):
    """Terminal: fetched object generation does not match recorded generation."""

    safe_error_code = GENERATION_MISMATCH
    http_status = 200
    message = "Object generation mismatch; original evidence no longer accessible."


class ExtractionSchemaError(FinancialOsError):
    """Terminal: extraction output does not conform to the versioned schema."""

    safe_error_code = SCHEMA_VALIDATION_FAILED
    http_status = 200
    message = "Extraction output failed schema validation."


class LeaseConflictError(FinancialOsError):
    """Non-terminal: another worker instance holds the processing lease."""

    safe_error_code = LEASE_LOST
    http_status = 200
    message = "Processing lease already held by another worker."
