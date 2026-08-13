"""Google Cloud Storage adapter.

Signed URLs are generated using the service identity (Workload Identity or
application default credentials). No long-lived service account key is used
in production (CICD-01, DB-01).

Never log signed URLs — they are bearer secrets (OBJ-02, LOG-01).
"""

from __future__ import annotations

import datetime as dt
import logging
from typing import Protocol, cast

from financial_os.adapters.storage.base import (
    DownloadCapability,
    ObjectMetadata,
    StorageAdapter,
    UploadCapability,
)
from financial_os.domain.errors import StorageError

logger = logging.getLogger(__name__)


class _Blob(Protocol):
    generation: int | str | None
    size: int | None
    content_type: str | None
    md5_hash: str | None

    def generate_signed_url(self, **kwargs: object) -> str: ...

    def reload(self) -> None: ...

    def download_as_bytes(self) -> bytes: ...


class _Bucket(Protocol):
    def blob(self, object_key: str, generation: int | None = None) -> _Blob: ...

    def exists(self) -> bool: ...


class _StorageClient(Protocol):
    def bucket(self, bucket_name: str) -> _Bucket: ...


class GCSStorageAdapter(StorageAdapter):
    """Storage adapter backed by Google Cloud Storage."""

    def __init__(self, bucket_name: str) -> None:
        self._bucket_name = bucket_name
        self._client: _StorageClient | None = None

    def _get_client(self) -> _StorageClient:
        if self._client is None:
            from google.cloud.storage import Client  # type: ignore[import-untyped]

            self._client = cast(_StorageClient, Client())
        return self._client

    async def generate_upload_capability(
        self,
        object_key: str,
        declared_mime_type: str,
        lifetime_seconds: int,
    ) -> UploadCapability:
        import asyncio

        loop = asyncio.get_running_loop()

        def _sign() -> str:
            client = self._get_client()
            bucket = client.bucket(self._bucket_name)
            blob = bucket.blob(object_key)
            url = blob.generate_signed_url(
                version="v4",
                expiration=dt.timedelta(seconds=lifetime_seconds),
                method="PUT",
                content_type=declared_mime_type,
            )
            return url

        try:
            url = await loop.run_in_executor(None, _sign)
        except Exception as exc:
            logger.error("GCS sign upload failed", extra={"object_key": object_key})
            raise StorageError("Failed to generate upload capability") from exc

        expires_at = dt.datetime.now(dt.UTC) + dt.timedelta(seconds=lifetime_seconds)
        return UploadCapability(
            upload_url=url,
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
        import asyncio
        import datetime as dt

        loop = asyncio.get_running_loop()

        def _sign() -> str:
            client = self._get_client()
            bucket = client.bucket(self._bucket_name)
            blob = bucket.blob(object_key, generation=int(generation))
            url = blob.generate_signed_url(
                version="v4",
                expiration=dt.timedelta(seconds=lifetime_seconds),
                method="GET",
            )
            return url

        try:
            url = await loop.run_in_executor(None, _sign)
        except Exception as exc:
            logger.error("GCS sign download failed")
            raise StorageError("Failed to generate download capability") from exc

        expires_at = dt.datetime.now(dt.UTC) + dt.timedelta(seconds=lifetime_seconds)
        return DownloadCapability(download_url=url, method="GET", expires_at=expires_at)

    async def get_object_metadata(self, object_key: str) -> ObjectMetadata | None:
        import asyncio

        loop = asyncio.get_running_loop()

        def _fetch() -> ObjectMetadata | None:
            from google.api_core.exceptions import NotFound

            client = self._get_client()
            bucket = client.bucket(self._bucket_name)
            blob = bucket.blob(object_key)
            try:
                blob.reload()
            except NotFound:
                return None
            return ObjectMetadata(
                generation=str(blob.generation),
                byte_size=blob.size or 0,
                content_type=blob.content_type,
                md5_hash=blob.md5_hash,
            )

        try:
            return await loop.run_in_executor(None, _fetch)
        except Exception as exc:
            logger.error("GCS get_object_metadata failed")
            raise StorageError("Storage metadata lookup failed") from exc

    async def read_object_bytes(self, object_key: str, generation: str | None = None) -> bytes:
        import asyncio

        loop = asyncio.get_running_loop()

        def _download() -> bytes:
            client = self._get_client()
            bucket = client.bucket(self._bucket_name)
            gen = int(generation) if generation else None
            blob = bucket.blob(object_key, generation=gen)
            return blob.download_as_bytes()

        try:
            return await loop.run_in_executor(None, _download)
        except Exception as exc:
            logger.error("GCS read_object_bytes failed")
            raise StorageError("Storage download failed") from exc

    async def is_healthy(self) -> bool:
        try:
            import asyncio

            loop = asyncio.get_running_loop()

            def _check() -> bool:
                client = self._get_client()
                client.bucket(self._bucket_name).exists()
                return True

            return await loop.run_in_executor(None, _check)
        except Exception:
            return False
