"""Abstract storage adapter interface.

All receipt evidence is stored in a private GCS bucket (OBJ-01).
Signed capabilities have narrow object scope and short expiry (OBJ-02).
Object keys contain no merchant, date, amount, or other financial data.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class ObjectMetadata:
    """Metadata returned for a verified GCS object (S-01)."""

    generation: str
    byte_size: int
    content_type: str | None
    md5_hash: str | None


@dataclass(frozen=True)
class UploadCapability:
    """Short-lived signed PUT capability — bearer secret, never log (OBJ-02)."""

    upload_url: str
    method: str
    expires_at: datetime
    allowed_mime_types: list[str]


@dataclass(frozen=True)
class DownloadCapability:
    """Short-lived signed GET capability — bearer secret, never log (OBJ-02)."""

    download_url: str
    method: str
    expires_at: datetime


class StorageAdapter(ABC):
    """Port for private evidence object storage."""

    @staticmethod
    def object_key(owner_id: UUID, receipt_id: UUID, asset_id: UUID) -> str:
        """Canonical opaque object key — no financial data in the path."""
        return f"originals/{owner_id}/{receipt_id}/{asset_id}"

    @abstractmethod
    async def generate_upload_capability(
        self,
        object_key: str,
        declared_mime_type: str,
        lifetime_seconds: int,
    ) -> UploadCapability:
        """Generate a short-lived signed PUT URL for direct client upload."""

    @abstractmethod
    async def generate_download_capability(
        self,
        object_key: str,
        generation: str,
        lifetime_seconds: int,
    ) -> DownloadCapability:
        """Generate a short-lived signed GET URL for image display.

        Must pin the generation so the URL retrieves the exact verified version (S-01, S-03).
        """

    @abstractmethod
    async def get_object_metadata(self, object_key: str) -> ObjectMetadata | None:
        """Return object metadata or None if the object does not exist."""

    @abstractmethod
    async def read_object_bytes(self, object_key: str, generation: str | None = None) -> bytes:
        """Download object bytes, optionally pinned to a specific generation (S-01).

        Raises StorageError if the object or generation is not found.
        """

    @abstractmethod
    async def is_healthy(self) -> bool:
        """Return True when the storage backend is reachable (readiness probe)."""
