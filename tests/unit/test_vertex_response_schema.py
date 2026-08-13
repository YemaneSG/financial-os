from copy import deepcopy

import pytest
from vertexai.generative_models import GenerationConfig

from financial_os.adapters.extraction.vertex import (
    _to_vertex_schema_node,
    build_vertex_response_schema,
)
from financial_os.services.validation import load_extraction_schema


def test_vertex_schema_is_derived_without_mutating_canonical_contract() -> None:
    canonical = load_extraction_schema()
    before = deepcopy(canonical)

    provider_schema = build_vertex_response_schema()

    assert canonical == before
    assert provider_schema["properties"]["schema_version"]["enum"] == ["v1"]
    assert provider_schema["properties"]["merchant_raw"]["nullable"] is True
    assert set(provider_schema["required"]) == set(provider_schema["properties"])


def test_vertex_schema_requires_complete_line_item_shape() -> None:
    provider_schema = build_vertex_response_schema()
    line_item = provider_schema["$defs"]["LineItem"]

    assert set(line_item["required"]) == set(line_item["properties"])
    assert line_item["properties"]["quantity"]["nullable"] is True


def test_vertex_sdk_accepts_generated_response_schema() -> None:
    config = GenerationConfig(
        response_mime_type="application/json",
        response_schema=build_vertex_response_schema(),
        temperature=0,
    )

    assert config is not None


def test_vertex_schema_rejects_multiple_non_null_union_types() -> None:
    with pytest.raises(ValueError, match="exactly one non-null type"):
        _to_vertex_schema_node({"type": ["string", "integer", "null"]})
