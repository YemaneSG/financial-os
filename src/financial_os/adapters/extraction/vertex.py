"""Vertex AI Gemini extraction adapter.

Sends ordered receipt images to Gemini Flash-class model via structured output.
The model has no tools, function calling, credentials, or browsing (AI-01).
Raw model output is returned unparsed for the caller to validate (AI-03).

Prompt and schema versions are pinned via configuration — never inlined as literals.
"""

from __future__ import annotations

import copy
import json
import logging
import time
from typing import Any

from financial_os.adapters.extraction.base import (
    AssetForExtraction,
    ExtractionAdapter,
    ExtractionResult,
)
from financial_os.services.validation import load_extraction_schema

logger = logging.getLogger(__name__)

_VERTEX_SCHEMA_FIELDS = {
    "$defs",
    "$ref",
    "additionalProperties",
    "anyOf",
    "description",
    "enum",
    "format",
    "items",
    "maxItems",
    "maxLength",
    "maxProperties",
    "maximum",
    "minItems",
    "minLength",
    "minProperties",
    "minimum",
    "nullable",
    "pattern",
    "properties",
    "propertyOrdering",
    "required",
    "title",
    "type",
}


def _to_vertex_schema_node(node: dict[str, Any]) -> dict[str, Any]:
    """Convert the canonical JSON Schema into Vertex's OpenAPI schema subset."""
    converted: dict[str, Any] = {}

    for key, value in node.items():
        if key == "const":
            converted["enum"] = [value]
            continue
        if key not in _VERTEX_SCHEMA_FIELDS:
            continue

        if key == "type" and isinstance(value, list):
            non_null_types = [item for item in value if item != "null"]
            if len(non_null_types) != 1:
                raise ValueError("Vertex schema fields must have exactly one non-null type")
            converted["type"] = non_null_types[0]
            converted["nullable"] = "null" in value
        elif key in {"properties", "$defs"}:
            converted[key] = {name: _to_vertex_schema_node(child) for name, child in value.items()}
        elif key in {"items", "additionalProperties"} and isinstance(value, dict):
            converted[key] = _to_vertex_schema_node(value)
        elif key == "anyOf":
            converted[key] = [_to_vertex_schema_node(child) for child in value]
        else:
            converted[key] = copy.deepcopy(value)

    # Controlled generation emits a stable, complete shape. Optional evidence
    # stays explicit as null, which the canonical contract permits.
    properties = converted.get("properties")
    if converted.get("type") == "object" and properties:
        converted["required"] = list(properties)

    return converted


def build_vertex_response_schema() -> dict[str, Any]:
    """Build a fresh provider schema from the frozen canonical contract."""
    return _to_vertex_schema_node(load_extraction_schema())


class VertexExtractionAdapter(ExtractionAdapter):
    """Extraction adapter backed by Vertex AI Gemini."""

    def __init__(
        self,
        project_id: str,
        location: str,
        model_id: str,
        prompt_version: str = "v1",
        schema_version: str = "v1",
    ) -> None:
        self._project_id = project_id
        self._location = location
        self._model_id = model_id
        self._prompt_version = prompt_version
        self._schema_version = schema_version

    @property
    def provider_name(self) -> str:
        return "vertex-ai"

    @property
    def model_id(self) -> str:
        return self._model_id

    @property
    def prompt_version(self) -> str:
        return self._prompt_version

    @property
    def schema_version(self) -> str:
        return self._schema_version

    def _build_prompt(self) -> str:
        return (
            "You are a precise receipt-data extractor. "
            "Extract structured financial data from the provided receipt image(s). "
            "Follow these rules strictly:\n"
            "- Use only information visibly present on the receipt.\n"
            "- Do not invent merchant names, dates, amounts, or line items.\n"
            "- All currency totals must be integer minor units (e.g. cents for USD).\n"
            "- Set fields to null when not evidenced on the receipt.\n"
            "- Do not infer timezone from location or merchant geography.\n"
            "- Payment method hint must never include full card numbers.\n"
            "- Respond only with the JSON structure; no markdown or explanation.\n"
            f"Schema version: {self._schema_version}"
        )

    async def extract(self, assets: list[AssetForExtraction]) -> ExtractionResult:
        import asyncio

        import vertexai
        from vertexai.generative_models import (
            GenerationConfig,
            GenerativeModel,
            Image,
            Part,
        )

        vertexai.init(project=self._project_id, location=self._location)
        model = GenerativeModel(self._model_id)

        parts: list[str | Image | Part] = [self._build_prompt()]
        for asset in sorted(assets, key=lambda a: a.ordinal):
            parts.append(Part.from_data(data=asset.data, mime_type=asset.mime_type))

        start = time.monotonic()

        loop = asyncio.get_running_loop()

        def _invoke() -> tuple[str, str | None]:
            response = model.generate_content(
                parts,
                generation_config=GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=build_vertex_response_schema(),
                    temperature=0,
                ),
            )
            raw_text = response.text
            request_id = None
            return raw_text, request_id

        raw_text, request_id = await loop.run_in_executor(None, _invoke)

        latency_ms = int((time.monotonic() - start) * 1000)

        try:
            parsed = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            logger.warning(
                "Extraction provider returned non-JSON response",
                extra={"latency_ms": latency_ms},
            )
            raise ValueError(f"Provider returned non-JSON: {exc}") from exc

        return ExtractionResult(
            raw=parsed,
            provider_request_id=request_id,
            latency_ms=latency_ms,
            estimated_cost_cents=None,
        )
