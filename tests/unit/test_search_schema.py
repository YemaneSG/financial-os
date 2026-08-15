"""Unit tests for SearchReceiptsRequest validation.

No database, no network.  Validates the Pydantic schema guards.
"""

from __future__ import annotations

from datetime import UTC

import pytest
from pydantic import ValidationError

from financial_os.schemas.search import SearchReceiptsRequest


def test_empty_request_valid():
    req = SearchReceiptsRequest()
    assert req.query is None
    assert req.processing_status == []
    assert req.sort == "effective_date_desc"
    assert req.limit == 20


def test_query_normalized():
    req = SearchReceiptsRequest(query="  Coffee  ")
    assert req.normalized_query == "coffee"


def test_query_too_long_rejected():
    with pytest.raises(ValidationError, match="query"):
        SearchReceiptsRequest(query="x" * 201)


def test_empty_query_string_rejected():
    with pytest.raises(ValidationError):
        SearchReceiptsRequest(query="")


def test_limit_bounds():
    assert SearchReceiptsRequest(limit=1).limit == 1
    assert SearchReceiptsRequest(limit=50).limit == 50
    with pytest.raises(ValidationError):
        SearchReceiptsRequest(limit=0)
    with pytest.raises(ValidationError):
        SearchReceiptsRequest(limit=51)


def test_invalid_processing_status_rejected():
    with pytest.raises(ValidationError):
        SearchReceiptsRequest(processing_status=["bogus"])


def test_valid_processing_statuses():
    req = SearchReceiptsRequest(processing_status=["extracted", "queued"])
    assert set(req.processing_status) == {"extracted", "queued"}


def test_duplicate_statuses_deduped():
    req = SearchReceiptsRequest(processing_status=["extracted", "extracted"])
    assert req.processing_status == ["extracted"]


def test_invalid_verification_status_rejected():
    with pytest.raises(ValidationError):
        SearchReceiptsRequest(verification_status=["invalid"])


def test_invalid_deduplication_status_rejected():
    with pytest.raises(ValidationError):
        SearchReceiptsRequest(deduplication_status=["invalid"])


def test_valid_deduplication_statuses():
    req = SearchReceiptsRequest(
        deduplication_status=["unchecked", "unique", "suspected_duplicate", "confirmed_duplicate"]
    )
    assert len(req.deduplication_status) == 4


def test_amount_range_valid():
    req = SearchReceiptsRequest(amount_min_minor=100, amount_max_minor=500)
    assert req.amount_min_minor == 100
    assert req.amount_max_minor == 500


def test_amount_range_equal_valid():
    req = SearchReceiptsRequest(amount_min_minor=300, amount_max_minor=300)
    assert req.amount_min_minor == 300


def test_amount_range_inverted_rejected():
    with pytest.raises(ValidationError, match="amount_min_minor"):
        SearchReceiptsRequest(amount_min_minor=500, amount_max_minor=100)


def test_date_range_inverted_rejected():
    from datetime import datetime

    with pytest.raises(ValidationError, match="date_from"):
        SearchReceiptsRequest(
            date_from=datetime(2026, 8, 15, tzinfo=UTC),
            date_to=datetime(2026, 1, 1, tzinfo=UTC),
        )


def test_sort_options():
    for sort in ("effective_date_desc", "effective_date_asc", "amount_desc", "amount_asc"):
        assert SearchReceiptsRequest(sort=sort).sort == sort


def test_invalid_sort_rejected():
    with pytest.raises(ValidationError):
        SearchReceiptsRequest(sort="bogus_sort")


def test_whitespace_only_query_rejected():
    with pytest.raises(ValidationError):
        SearchReceiptsRequest(query="   ")
