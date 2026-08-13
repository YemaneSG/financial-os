"""In-memory storage adapter for deterministic tests.

No real GCP credentials, bucket names, or signed URLs are used.
Signed URL values are opaque test strings — never real bearer secrets.
"""

from __future__ import annotations

import datetime as dt
import hashlib

from financial_os.adapters.storage.base import (
    DownloadCapability,
    ObjectMetadata,
    StorageAdapter,
    UploadCapability,
)
from financial_os.domain.errors import StorageError


class FakeStorageAdapter(StorageAdapter):
    """In-memory object store for unit and integration tests."""

    def __init__(self) -> None:
        self._objects: dict[str, bytes] = {}
        self._generations: dict[str, int] = {}

    def put_object(self, object_key: str, data: bytes) -> str:
        """Directly write bytes and return the new generation string (test helper)."""
        gen = self._generations.get(object_key, 0) + 1
        self._generations[object_key] = gen
        self._objects[f"{object_key}#{gen}"] = data
        self._objects[object_key] = data  # latest
        return str(gen)

    def sha256_of(self, object_key: str) -> str:
        data = self._objects.get(object_key, b"")
        return hashlib.sha256(data).hexdigest()

    async def generate_upload_capability(
        self,
        object_key: str,
        declared_mime_type: str,
        lifetime_seconds: int,
    ) -> UploadCapability:
        expires_at = dt.datetime.now(dt.UTC) + dt.timedelta(seconds=lifetime_seconds)
        return UploadCapability(
            upload_url=f"https://fake-storage.invalid/upload/{object_key}",
            method="PUT",
            expires_at=expires_at,
            allowed_mime_types=[declared_mime_type],
        )

    async def generate_download_capability(
        self,
        object_key: str,
        generation: str,
        lifetime_seconds: int,
    ) -> DownloadCapability:
        expires_at = dt.datetime.now(dt.UTC) + dt.timedelta(seconds=lifetime_seconds)
        return DownloadCapability(
            download_url=f"https://fake-storage.invalid/download/{object_key}?gen={generation}",
            method="GET",
            expires_at=expires_at,
        )

    async def get_object_metadata(self, object_key: str) -> ObjectMetadata | None:
        data = self._objects.get(object_key)
        if data is None:
            return None
        gen = self._generations.get(object_key, 1)
        md5 = hashlib.md5(data).hexdigest()  # noqa: S324 — not used for security
        return ObjectMetadata(
            generation=str(gen),
            byte_size=len(data),
            content_type="image/jpeg",
            md5_hash=md5,
        )

    async def read_object_bytes(self, object_key: str, generation: str | None = None) -> bytes:
        if generation is not None:
            key = f"{object_key}#{generation}"
            data = self._objects.get(key)
        else:
            data = self._objects.get(object_key)
        if data is None:
            raise StorageError(f"Object not found: {object_key}")
        return data

    async def is_healthy(self) -> bool:
        return True
