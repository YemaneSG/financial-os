from uuid import uuid4

import pytest

from financial_os.adapters.queue.cloud_tasks import CloudTasksQueueAdapter
from financial_os.domain.errors import QueueError


def test_oidc_audience_uses_worker_service_origin() -> None:
    receipt_id = uuid4()
    worker_url = (
        "https://private-worker.example.run.app/"
        f"internal/v1/receipts/{receipt_id}/process"
    )

    assert (
        CloudTasksQueueAdapter._oidc_audience(worker_url)
        == "https://private-worker.example.run.app"
    )


@pytest.mark.parametrize(
    "worker_url",
    ["", "private-worker.example.run.app/process", "/internal/v1/process"],
)
def test_oidc_audience_rejects_invalid_worker_url(worker_url: str) -> None:
    with pytest.raises(QueueError, match="Invalid worker URL"):
        CloudTasksQueueAdapter._oidc_audience(worker_url)
