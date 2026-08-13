"""Abstract extraction adapter interface — the ReceiptExtractor port.

The extraction runtime has no tools, credentials, browsing, or action authority (AI-01).
Model output is validated against the versioned JSON Schema before any field is
persisted (AI-03, VAL-001).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class AssetForExtraction:
    """One image asset ready for extraction, with EXIF stripped."""

    ordinal: int
    data: bytes
    mime_type: str
    sha256: str


@dataclass
class ExtractionResult:
    """Raw structured response from the extraction provider after JSON parsing.

    This is validated against contracts/extraction-result.schema.json before
    any field is written to receipt_revisions or line_item_revisions.
    """

    raw: dict[str, Any]
    provider_request_id: str | None
    latency_ms: int
    estimated_cost_cents: float | None


class ExtractionAdapter(ABC):
    """Port for the replaceable multimodal receipt extractor."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Safe provider name for provenance records (e.g. 'vertex-ai')."""

    @property
    @abstractmethod
    def model_id(self) -> str:
        """Exact model identifier recorded per run."""

    @property
    @abstractmethod
    def prompt_version(self) -> str:
        """Versioned prompt identifier recorded per run."""

    @property
    @abstractmethod
    def schema_version(self) -> str:
        """Schema version the adapter targets (must be 'v1' for Wave 1)."""

    @abstractmethod
    async def extract(self, assets: list[AssetForExtraction]) -> ExtractionResult:
        """Invoke the extraction provider and return the raw structured result.

        The returned ExtractionResult.raw will be validated by the caller.
        This method must not perform any side effects beyond the API call.
        It must not log image bytes, raw model output, or any receipt content.
        """
