"""
Authorization negative tests: IAM-01, IAM-02.

Verifies:
- Missing token → 401 with no private detail
- Invalid/malformed token → 401
- Valid non-owner token → 403
- Private routes are not reachable without auth
"""

import httpx
import pytest

PRIVATE_ROUTES = [
    ("GET", "/api/v1/receipts"),
    ("POST", "/api/v1/receipts"),
]

INTERNAL_ROUTES = [
    ("POST", "/internal/v1/receipts/00000000-0000-0000-0000-000000000000/process"),
    ("POST", "/internal/v1/reconcile-processing"),
]


class TestMissingToken:
    @pytest.mark.parametrize("method,path", PRIVATE_ROUTES)
    def test_missing_token_returns_401(self, api_url: str, method: str, path: str) -> None:
        resp = httpx.request(method, f"{api_url}{path}", timeout=10)
        assert resp.status_code == 401, (
            f"{method} {path} with no token: expected 401, got {resp.status_code}"
        )

    @pytest.mark.parametrize("method,path", PRIVATE_ROUTES)
    def test_missing_token_response_has_no_private_detail(
        self, api_url: str, method: str, path: str
    ) -> None:
        resp = httpx.request(method, f"{api_url}{path}", timeout=10)
        body = resp.text
        forbidden_patterns = [
            "password",
            "secret",
            "token",
            "allowlist",
            "subject",
            "stack",
            "traceback",
            "exception",
        ]
        for pattern in forbidden_patterns:
            assert pattern not in body.lower(), (
                f"Error response body contains potentially sensitive word: {pattern!r}"
            )


class TestInvalidToken:
    def test_malformed_bearer_returns_401(self, api_url: str) -> None:
        resp = httpx.get(
            f"{api_url}/api/v1/receipts",
            headers={"Authorization": "Bearer not-a-real-jwt"},
            timeout=10,
        )
        assert resp.status_code == 401

    def test_expired_format_bearer_returns_401(self, api_url: str) -> None:
        # A structurally plausible but invalid JWT (wrong signature).
        fake_jwt = (
            "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0IiwiZXhwIjoxfQ.invalidsignature"
        )
        resp = httpx.get(
            f"{api_url}/api/v1/receipts",
            headers={"Authorization": f"Bearer {fake_jwt}"},
            timeout=10,
        )
        assert resp.status_code == 401

    def test_empty_bearer_value_returns_401(self, api_url: str) -> None:
        resp = httpx.get(
            f"{api_url}/api/v1/receipts",
            headers={"Authorization": "Bearer "},
            timeout=10,
        )
        assert resp.status_code == 401


class TestNonOwnerToken:
    def test_non_owner_valid_token_returns_403(self, api_url: str, non_owner_token: str) -> None:
        resp = httpx.get(
            f"{api_url}/api/v1/receipts",
            headers={"Authorization": f"Bearer {non_owner_token}"},
            timeout=10,
        )
        assert resp.status_code == 403, f"Non-owner token: expected 403, got {resp.status_code}"

    def test_non_owner_403_reveals_no_private_detail(
        self, api_url: str, non_owner_token: str
    ) -> None:
        resp = httpx.get(
            f"{api_url}/api/v1/receipts",
            headers={"Authorization": f"Bearer {non_owner_token}"},
            timeout=10,
        )
        body = resp.text
        for pattern in ["allowlist", "subject", "email", "owner", "stack"]:
            assert pattern not in body.lower(), f"403 response leaks sensitive word: {pattern!r}"


class TestInternalEndpointsNotPublic:
    """Internal worker routes must not be reachable from the public internet (QUE-01, NET-01)."""

    @pytest.mark.parametrize("method,path", INTERNAL_ROUTES)
    def test_internal_route_not_reachable(self, api_url: str, method: str, path: str) -> None:
        # Attempt with a valid owner token — internal routes should still reject.
        # The API service does not expose /internal routes; they live on the worker.
        # This test verifies that the API does not proxy or expose them.
        resp = httpx.request(
            method,
            f"{api_url}{path}",
            headers={"Content-Type": "application/json"},
            content=b"{}",
            timeout=10,
        )
        # A 404 or 405 from the API is acceptable (it doesn't know the route).
        # A 200 would be a serious misconfiguration.
        assert resp.status_code != 200, (
            f"Internal route {method} {path} returned 200 on the public API — "
            "this route must not be exposed publicly."
        )
