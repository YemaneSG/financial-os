"""
S-02 verification: deployed Firebase Hosting serves the frozen CSP and all
required security headers. See implementation-contracts.md §6.

Tests: CICD-02, S-02, APP-03, NET-01.
"""

import re

import httpx
import pytest

REQUIRED_HEADERS = {
    "x-content-type-options": "nosniff",
    "referrer-policy": "no-referrer",
}

REQUIRED_HSTS_MIN_AGE = 31_536_000
REQUIRED_CSP_DIRECTIVES = [
    "default-src 'self'",
    "frame-ancestors 'none'",
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "img-src 'self' data: blob: https://storage.googleapis.com",
]
FORBIDDEN_CSP_VALUES = ["unsafe-inline", "unsafe-eval"]
REQUIRED_PERMISSIONS_CAMERA = "camera=(self)"


def _get_headers(url: str) -> dict[str, str]:
    resp = httpx.get(url, follow_redirects=True, timeout=15)
    # Return all headers as lower-case keys.
    return {k.lower(): v for k, v in resp.headers.items()}


@pytest.fixture(scope="module")
def deployed_headers(hosting_url: str) -> dict[str, str]:
    return _get_headers(f"{hosting_url}/index.html")


class TestCspHeaders:
    def test_csp_header_present(self, deployed_headers: dict[str, str]) -> None:
        assert "content-security-policy" in deployed_headers, (
            "Content-Security-Policy header is missing from the deployed response."
        )

    def test_required_csp_directives(self, deployed_headers: dict[str, str]) -> None:
        csp = deployed_headers.get("content-security-policy", "")
        for directive in REQUIRED_CSP_DIRECTIVES:
            assert directive in csp, (
                f"Required CSP directive missing: {directive!r}\nFull CSP: {csp}"
            )

    def test_no_unsafe_inline(self, deployed_headers: dict[str, str]) -> None:
        csp = deployed_headers.get("content-security-policy", "")
        assert "unsafe-inline" not in csp, "CSP contains 'unsafe-inline'. This violates S-02."

    def test_no_unsafe_eval(self, deployed_headers: dict[str, str]) -> None:
        csp = deployed_headers.get("content-security-policy", "")
        assert "unsafe-eval" not in csp, "CSP contains 'unsafe-eval'. This violates S-02."

    def test_hsts_present_and_correct(self, deployed_headers: dict[str, str]) -> None:
        hsts = deployed_headers.get("strict-transport-security", "")
        max_age = re.search(r"(?:^|;)\s*max-age=(\d+)", hsts, re.IGNORECASE)
        assert max_age and int(max_age.group(1)) >= REQUIRED_HSTS_MIN_AGE, (
            f"HSTS header missing or insufficient max-age. Got: {hsts!r}"
        )
        assert "includesubdomains" in hsts.lower()
        assert "preload" in hsts.lower()

    def test_x_content_type_options(self, deployed_headers: dict[str, str]) -> None:
        assert deployed_headers.get("x-content-type-options", "").lower() == "nosniff"

    def test_referrer_policy(self, deployed_headers: dict[str, str]) -> None:
        assert deployed_headers.get("referrer-policy", "").lower() == "no-referrer"

    def test_permissions_policy_camera(self, deployed_headers: dict[str, str]) -> None:
        pp = deployed_headers.get("permissions-policy", "")
        assert "camera=(self)" in pp or "camera=self" in pp, (
            f"Permissions-Policy missing camera=(self). Got: {pp!r}"
        )

    def test_permissions_policy_no_geolocation(self, deployed_headers: dict[str, str]) -> None:
        pp = deployed_headers.get("permissions-policy", "")
        # geolocation must be empty-set, not self.
        assert "geolocation=()" in pp or "geolocation=" not in pp, (
            f"Permissions-Policy should restrict geolocation. Got: {pp!r}"
        )
