"""Shared Pydantic primitives and error schema."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ApiError(BaseModel):
    """Privacy-safe error response. Never contains receipt content or credentials."""

    error_code: str
    message: str
    request_id: str | None = None


class UUIDStr(BaseModel):
    """Mixin for models with a UUID string field."""

    model_config = ConfigDict(from_attributes=True)


# Allowed MIME types for receipt assets (OBJ-03).
ALLOWED_ASSET_MIME_TYPES: frozenset[str] = frozenset(
    {
        "image/jpeg",
        "image/jpg",
        "image/png",
        "image/heic",
        "image/heif",
        "image/webp",
    }
)

# Magic byte signatures for decodable image content check (OBJ-03).
_MAGIC: dict[bytes, str] = {
    b"\xff\xd8\xff": "image/jpeg",
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"RIFF": "image/webp",  # further check: bytes[8:12] == b"WEBP"
}


def detect_mime_from_magic(data: bytes) -> str | None:
    """Return a MIME type string if the magic bytes match a known image format."""
    if data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    # HEIC/HEIF: ISO base media file format — ftyp box at byte 4
    if len(data) >= 12 and data[4:8] == b"ftyp":
        brand = data[8:12]
        if brand in (b"heic", b"heix", b"hevc", b"hevx", b"mif1", b"msf1"):
            return "image/heic"
    return None


def is_decodable_image(data: bytes) -> bool:
    """Return True if data starts with a recognised image magic signature."""
    return detect_mime_from_magic(data) is not None
