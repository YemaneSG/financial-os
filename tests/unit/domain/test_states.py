"""Unit tests for the processing state machine."""

import pytest

from financial_os.domain.states import (
    ProcessingStatus,
    VerificationStatus,
    can_transition_processing,
    can_transition_verification,
    is_already_queued_or_processing,
    is_retryable,
    is_terminal_processing,
)


@pytest.mark.unit
class TestProcessingStateMachine:
    def test_reserved_to_uploading_allowed(self):
        assert can_transition_processing(ProcessingStatus.RESERVED, ProcessingStatus.UPLOADING)

    def test_reserved_to_abandoned_allowed(self):
        assert can_transition_processing(ProcessingStatus.RESERVED, ProcessingStatus.ABANDONED)

    def test_uploading_to_uploaded_allowed(self):
        assert can_transition_processing(ProcessingStatus.UPLOADING, ProcessingStatus.UPLOADED)

    def test_uploaded_to_queued_allowed(self):
        assert can_transition_processing(ProcessingStatus.UPLOADED, ProcessingStatus.QUEUED)

    def test_queued_to_processing_allowed(self):
        assert can_transition_processing(ProcessingStatus.QUEUED, ProcessingStatus.PROCESSING)

    def test_processing_to_extracted_allowed(self):
        assert can_transition_processing(ProcessingStatus.PROCESSING, ProcessingStatus.EXTRACTED)

    def test_processing_to_retryable_failed_allowed(self):
        assert can_transition_processing(
            ProcessingStatus.PROCESSING, ProcessingStatus.RETRYABLE_FAILED
        )

    def test_processing_to_failed_allowed(self):
        assert can_transition_processing(ProcessingStatus.PROCESSING, ProcessingStatus.FAILED)

    def test_retryable_failed_to_queued_allowed(self):
        assert can_transition_processing(ProcessingStatus.RETRYABLE_FAILED, ProcessingStatus.QUEUED)

    def test_extracted_is_terminal(self):
        assert not can_transition_processing(ProcessingStatus.EXTRACTED, ProcessingStatus.QUEUED)
        assert is_terminal_processing(ProcessingStatus.EXTRACTED)

    def test_failed_is_terminal(self):
        assert not can_transition_processing(ProcessingStatus.FAILED, ProcessingStatus.QUEUED)
        assert is_terminal_processing(ProcessingStatus.FAILED)

    def test_abandoned_is_terminal(self):
        assert is_terminal_processing(ProcessingStatus.ABANDONED)

    def test_reserved_to_extracted_not_allowed(self):
        assert not can_transition_processing(ProcessingStatus.RESERVED, ProcessingStatus.EXTRACTED)

    def test_queued_to_retryable_not_allowed(self):
        assert not can_transition_processing(
            ProcessingStatus.QUEUED, ProcessingStatus.RETRYABLE_FAILED
        )

    def test_retryable_failed_is_retryable(self):
        assert is_retryable(ProcessingStatus.RETRYABLE_FAILED)

    def test_failed_is_terminal_and_not_retryable(self):
        assert is_terminal_processing(ProcessingStatus.FAILED)
        assert not is_retryable(ProcessingStatus.FAILED)

    def test_extracted_is_not_retryable(self):
        assert not is_retryable(ProcessingStatus.EXTRACTED)

    def test_queued_is_already_queued_or_processing(self):
        assert is_already_queued_or_processing(ProcessingStatus.QUEUED)

    def test_processing_is_already_queued_or_processing(self):
        assert is_already_queued_or_processing(ProcessingStatus.PROCESSING)

    def test_reserved_is_not_already_queued_or_processing(self):
        assert not is_already_queued_or_processing(ProcessingStatus.RESERVED)


@pytest.mark.unit
class TestVerificationStateMachine:
    def test_unreviewed_to_system_validated(self):
        assert can_transition_verification(
            VerificationStatus.UNREVIEWED, VerificationStatus.SYSTEM_VALIDATED
        )

    def test_unreviewed_to_needs_review(self):
        assert can_transition_verification(
            VerificationStatus.UNREVIEWED, VerificationStatus.NEEDS_REVIEW
        )

    def test_human_verified_is_terminal(self):
        assert not can_transition_verification(
            VerificationStatus.HUMAN_VERIFIED, VerificationStatus.NEEDS_REVIEW
        )

    def test_unreviewed_to_human_verified_not_directly_allowed(self):
        assert not can_transition_verification(
            VerificationStatus.UNREVIEWED, VerificationStatus.HUMAN_VERIFIED
        )
