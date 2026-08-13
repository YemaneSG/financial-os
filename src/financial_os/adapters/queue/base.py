"""Abstract queue adapter interface (Cloud Tasks).

Tasks are delivered with OIDC authentication to the worker endpoint (QUE-01).
The queue enforces bounded exponential retry (QUE-02).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID


class QueueAdapter(ABC):
    """Port for the durable processing task queue."""

    @abstractmethod
    async def enqueue_processing_task(
        self,
        receipt_id: UUID,
        pipeline_version: str,
        attempt_number: int,
        task_name_hint: str | None = None,
    ) -> str:
        """Enqueue an extraction task for a receipt.

        Returns the queue task name (safe operational reference, not a secret).
        """

    @abstractmethod
    async def is_healthy(self) -> bool:
        """Return True when the queue backend is reachable (readiness probe)."""
