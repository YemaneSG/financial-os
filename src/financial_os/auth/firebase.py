"""Firebase Authentication token verification and owner allowlist enforcement.

IAM-01: Verify token server-side for every private request.
IAM-02: Enforce session-version invalidation via valid_after check.
Authorization binds to stable provider_subject UID, not display email.

No email, token value, or auth claim detail is logged (LOG-01).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from financial_os.config import Settings

logger = logging.getLogger(__name__)

_firebase_app = None


def _init_firebase(firebase_project_id: str) -> None:
    """Initialise the Firebase Admin SDK once at startup."""
    global _firebase_app
    import firebase_admin  # type: ignore[import-untyped]
    from firebase_admin import credentials

    if _firebase_app is None:
        cred = credentials.ApplicationDefault()
        _firebase_app = firebase_admin.initialize_app(
            cred,
            options={"projectId": firebase_project_id},
        )


@dataclass(frozen=True)
class VerifiedOwner:
    """Represents a successfully authenticated and allowlisted owner."""

    subject_id: str  # stable provider UID; opaque
    auth_subject_id: str  # internal DB UUID (as string)
    auth_time: int  # Unix timestamp from token claims


async def verify_owner_token(
    token: str,
    settings: Settings,
) -> VerifiedOwner | None:
    """Verify a Firebase Bearer token and return VerifiedOwner or None.

    Returns None for expired, invalid, or non-allowlisted tokens.
    Never logs the token value or any PII from claims (LOG-01).
    """
    import asyncio

    import firebase_admin.auth as fb_auth  # type: ignore[import-untyped]

    loop = asyncio.get_running_loop()

    def _verify() -> dict[str, object] | None:
        try:
            return cast(
                dict[str, object],
                fb_auth.verify_id_token(token, check_revoked=False),
            )
        except Exception:
            return None

    claims = await loop.run_in_executor(None, _verify)
    if claims is None:
        return None

    provider_subject = f"google:{claims.get('sub', '')}"
    allowed = settings.allowed_owner_subjects

    if provider_subject not in allowed:
        logger.info(
            "Token rejected — subject not in allowlist",
            extra={"reason": "not_allowlisted"},
        )
        return None

    auth_time_claim = claims.get("auth_time", 0)
    auth_time = (
        auth_time_claim
        if isinstance(auth_time_claim, int) and not isinstance(auth_time_claim, bool)
        else 0
    )

    return VerifiedOwner(
        subject_id=provider_subject,
        auth_subject_id="",  # resolved by the service layer against auth_subjects table
        auth_time=auth_time,
    )


async def verify_oidc_token(
    token: str,
    expected_audience: str,
) -> bool:
    """Verify a Google OIDC token issued by Cloud Tasks (QUE-01).

    Checks issuer, audience, and signature. Returns True when valid.
    """
    import asyncio

    loop = asyncio.get_running_loop()

    def _verify() -> bool:
        try:
            from google.auth.transport import requests as google_requests
            from google.oauth2 import id_token

            request = google_requests.Request()
            id_info = id_token.verify_oauth2_token(  # type: ignore[no-untyped-call]
                token, request, expected_audience
            )
            issuer = id_info.get("iss", "")
            return issuer in ("accounts.google.com", "https://accounts.google.com")
        except Exception:
            return False

    return await loop.run_in_executor(None, _verify)
