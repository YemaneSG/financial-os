from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

from financial_os.adapters.queue.fake import FakeQueueAdapter
from financial_os.config import Settings
from financial_os.domain.states import ProcessingStatus
from financial_os.models.events import StateEvent
from financial_os.models.receipt import ProcessingAttempt, Receipt
from financial_os.services.worker import reconcile_processing


class _ScalarResult:
    def __init__(self, rows: list[Any]) -> None:
        self._rows = rows

    def scalars(self) -> list[Any]:
        return self._rows

    def scalar_one_or_none(self) -> Any | None:
        return self._rows[0] if self._rows else None


class _Session:
    def __init__(self, result_rows: list[list[Any]]) -> None:
        self._result_rows = iter(result_rows)
        self.added: list[Any] = []

    async def execute(self, _statement: Any) -> _ScalarResult:
        return _ScalarResult(next(self._result_rows))

    def add(self, value: Any) -> None:
        self.added.append(value)

    async def flush(self) -> None:
        return None


class _FailingQueue(FakeQueueAdapter):
    async def enqueue_processing_task(self, *args: Any, **kwargs: Any) -> str:
        raise RuntimeError("synthetic queue outage")


def _receipt(status: ProcessingStatus) -> Receipt:
    old = datetime.now(UTC) - timedelta(hours=1)
    return Receipt(
        id=uuid4(),
        owner_id=uuid4(),
        client_submission_id=uuid4(),
        financial_context="personal",
        processing_status=status,
        verification_status="unreviewed",
        expected_asset_count=1,
        row_version=1,
        created_at=old,
        updated_at=old,
    )


async def test_reconcile_redispatches_stale_queued_receipt() -> None:
    queued = _receipt(ProcessingStatus.QUEUED)
    session = _Session([[], [], [queued], [3], []])
    queue = FakeQueueAdapter()

    result = await reconcile_processing(
        session=session,  # type: ignore[arg-type]
        queue=queue,
        settings=Settings(pipeline_version="test-v1"),
        correlation_id="synthetic-correlation",
    )

    assert result.re_enqueued_count == 1
    assert result.flagged_count == 0
    assert queue.enqueued[0]["receipt_id"] == queued.id
    assert queue.enqueued[0]["attempt_number"] == 4
    attempt = next(value for value in session.added if isinstance(value, ProcessingAttempt))
    assert attempt.attempt_number == 4
    assert any(
        isinstance(event, StateEvent) and event.reason_code == "reconcile_queued_re_enqueue"
        for event in session.added
    )


async def test_reconcile_flags_stale_queued_receipt_when_redispatch_fails() -> None:
    queued = _receipt(ProcessingStatus.QUEUED)
    session = _Session([[], [], [queued], [3], []])

    result = await reconcile_processing(
        session=session,  # type: ignore[arg-type]
        queue=_FailingQueue(),
        settings=Settings(pipeline_version="test-v1"),
        correlation_id="synthetic-correlation",
    )

    assert result.re_enqueued_count == 0
    assert result.flagged_count == 1
    assert any(
        isinstance(event, StateEvent) and event.reason_code == "reconcile_queued_dispatch_failed"
        for event in session.added
    )


async def test_abandoned_event_preserves_actual_previous_state() -> None:
    reserved = _receipt(ProcessingStatus.RESERVED)
    session = _Session([[reserved], [], [], []])

    await reconcile_processing(
        session=session,  # type: ignore[arg-type]
        queue=FakeQueueAdapter(),
        settings=Settings(),
        correlation_id="synthetic-correlation",
    )

    event = next(value for value in session.added if isinstance(value, StateEvent))
    assert event.from_state == ProcessingStatus.RESERVED
    assert event.to_state == ProcessingStatus.ABANDONED
