"""In-memory queue adapter for deterministic tests."""

from __future__ import annotations

from uuid import UUID

from financial_os.adapters.queue.base import QueueAdapter


class FakeQueueAdapter(QueueAdapter):
    """In-memory queue that records enqueued tasks for test assertions."""

    def __init__(self) -> None:
        self.enqueued: list[dict[str, object]] = []

    async def enqueue_processing_task(
        self,
        receipt_id: UUID,
        pipeline_version: str,
        attempt_number: int,
        task_name_hint: str | None = None,
    ) -> str:
        task_name = f"fake-task/{receipt_id}/{attempt_number}"
        self.enqueued.append(
            {
                "receipt_id": receipt_id,
                "pipeline_version": pipeline_version,
                "attempt_number": attempt_number,
                "task_name": task_name,
            }
        )
        return task_name

    async def is_healthy(self) -> bool:
        return True

    def reset(self) -> None:
        self.enqueued.clear()
