"""Security tests for POST /api/v1/receipts/search.

Verifies unauthenticated and non-owner requests are rejected.
Requires API_URL, VALID_OWNER_TOKEN, NON_OWNER_TOKEN (skipped when absent).
"""

import httpx

SEARCH_PATH = "/api/v1/receipts/search"


class TestSearchMissingToken:
    def test_missing_token_returns_401(self, api_url: str) -> None:
        resp = httpx.post(
            f"{api_url}{SEARCH_PATH}",
            json={},
            timeout=10,
        )
        assert resp.status_code == 401

    def test_missing_token_no_private_detail(self, api_url: str) -> None:
        resp = httpx.post(f"{api_url}{SEARCH_PATH}", json={}, timeout=10)
        body = resp.text
        for pattern in ["password", "secret", "token", "allowlist", "subject", "traceback"]:
            assert pattern not in body.lower(), (
                f"Error response body contains sensitive word: {pattern!r}"
            )


class TestSearchNonOwnerToken:
    def test_non_owner_returns_403(self, api_url: str, non_owner_token: str) -> None:
        resp = httpx.post(
            f"{api_url}{SEARCH_PATH}",
            headers={"Authorization": f"Bearer {non_owner_token}"},
            json={},
            timeout=10,
        )
        assert resp.status_code == 403

    def test_non_owner_no_private_detail(self, api_url: str, non_owner_token: str) -> None:
        resp = httpx.post(
            f"{api_url}{SEARCH_PATH}",
            headers={"Authorization": f"Bearer {non_owner_token}"},
            json={},
            timeout=10,
        )
        body = resp.text
        for pattern in ["allowlist", "subject", "email", "owner", "stack"]:
            assert pattern not in body.lower()


class TestSearchInputValidation:
    def test_query_too_long_rejected(self, api_url: str, valid_owner_token: str) -> None:
        long_query = "a" * 201
        resp = httpx.post(
            f"{api_url}{SEARCH_PATH}",
            headers={"Authorization": f"Bearer {valid_owner_token}"},
            json={"query": long_query},
            timeout=10,
        )
        assert resp.status_code == 422

    def test_limit_above_max_rejected(self, api_url: str, valid_owner_token: str) -> None:
        resp = httpx.post(
            f"{api_url}{SEARCH_PATH}",
            headers={"Authorization": f"Bearer {valid_owner_token}"},
            json={"limit": 51},
            timeout=10,
        )
        assert resp.status_code == 422

    def test_invalid_processing_status_rejected(self, api_url: str, valid_owner_token: str) -> None:
        resp = httpx.post(
            f"{api_url}{SEARCH_PATH}",
            headers={"Authorization": f"Bearer {valid_owner_token}"},
            json={"processing_status": ["bogus_status"]},
            timeout=10,
        )
        assert resp.status_code == 422
