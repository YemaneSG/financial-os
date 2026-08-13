"""Cloud Tasks queue adapter.

Creates OIDC-authenticated tasks delivered to the worker endpoint.
The service account email and worker URL come from settings — never hard-coded.
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING
from urllib.parse import urlsplit
from uuid import UUID

from financial_os.adapters.queue.base import QueueAdapter
from financial_os.domain.errors import QueueError

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from google.cloud.tasks_v2 import CloudTasksClient


class CloudTasksQueueAdapter(QueueAdapter):
    """Queue adapter backed by Google Cloud Tasks."""

    def __init__(
        self,
        queue_path: str,
        worker_url_template: str,
        service_account_email: str,
        project_id: str,
    ) -> None:
        self._queue_path = queue_path
        self._worker_url_template = worker_url_template
        self._service_account_email = service_account_email
        self._project_id = project_id
        self._client: CloudTasksClient | None = None

    @staticmethod
    def _oidc_audience(worker_url: str) -> str:
        """Return the stable Cloud Run service origin used by worker auth.

        Receipt-specific paths must not enter the OIDC audience: the worker
        validates tokens against its configured base URL, and Cloud Run uses
        that same stable service audience for every internal route.
        """
        parsed = urlsplit(worker_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise QueueError("Invalid worker URL")
        return f"{parsed.scheme}://{parsed.netloc}"

    def _get_client(self) -> CloudTasksClient:
        if self._client is None:
            from google.cloud.tasks_v2 import CloudTasksClient

            self._client = CloudTasksClient()
        return self._client

    async def enqueue_processing_task(
        self,
        receipt_id: UUID,
        pipeline_version: str,
        attempt_number: int,
        task_name_hint: str | None = None,
    ) -> str:
        import asyncio

        from google.cloud import tasks_v2

        worker_url = self._worker_url_template.format(receipt_id=receipt_id)
        payload = json.dumps(
            {
                "pipeline_version": pipeline_version,
                "attempt_number": attempt_number,
            }
        ).encode()

        task = tasks_v2.Task(
            http_request=tasks_v2.HttpRequest(
                http_method=tasks_v2.HttpMethod.POST,
                url=worker_url,
                headers={"Content-Type": "application/json"},
                body=payload,
                oidc_token=tasks_v2.OidcToken(
                    service_account_email=self._service_account_email,
                    audience=self._oidc_audience(worker_url),
                ),
            )
        )

        loop = asyncio.get_running_loop()

        def _create() -> str:
            client = self._get_client()
            response = client.create_task(parent=self._queue_path, task=task)
            return response.name

        try:
            return await loop.run_in_executor(None, _create)
        except Exception as exc:
            logger.error(
                "Cloud Tasks enqueue failed",
                extra={"receipt_id": str(receipt_id), "attempt": attempt_number},
            )
            raise QueueError("Failed to enqueue processing task") from exc

    async def is_healthy(self) -> bool:
        try:
            import asyncio

            loop = asyncio.get_running_loop()

            def _check() -> bool:
                client = self._get_client()
                client.get_queue(name=self._queue_path)
                return True

            return await loop.run_in_executor(None, _check)
        except Exception:
            return False
