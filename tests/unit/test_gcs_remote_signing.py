from typing import Any

import pytest

from financial_os.adapters.storage.gcs import GCSStorageAdapter


class RecordingBlob:
    def __init__(self) -> None:
        self.kwargs: dict[str, Any] = {}

    def generate_signed_url(self, **kwargs: object) -> str:
        self.kwargs = kwargs
        return "https://storage.invalid/signed"


class RecordingBucket:
    def __init__(self, blob: RecordingBlob) -> None:
        self._blob = blob

    def blob(self, object_key: str, generation: int | None = None) -> RecordingBlob:
        return self._blob


class RecordingClient:
    def __init__(self, blob: RecordingBlob) -> None:
        self._bucket = RecordingBucket(blob)

    def bucket(self, bucket_name: str) -> RecordingBucket:
        return self._bucket


@pytest.mark.asyncio
async def test_upload_capability_uses_keyless_iam_signing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    blob = RecordingBlob()
    adapter = GCSStorageAdapter("synthetic-bucket")
    monkeypatch.setattr(adapter, "_get_client", lambda: RecordingClient(blob))
    monkeypatch.setattr(
        adapter,
        "_get_remote_signing_identity",
        lambda: ("runtime@example.invalid", "ephemeral-token"),
    )

    capability = await adapter.generate_upload_capability(
        object_key="originals/opaque/image.jpg",
        declared_mime_type="image/jpeg",
        lifetime_seconds=900,
    )

    assert capability.method == "PUT"
    assert blob.kwargs["service_account_email"] == "runtime@example.invalid"
    assert blob.kwargs["access_token"] == "ephemeral-token"  # noqa: S105 - synthetic
    assert blob.kwargs["method"] == "PUT"
