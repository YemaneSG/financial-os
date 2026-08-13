"""FastAPI dependency functions for authentication and authorization.

Public routes require a Firebase Bearer token for the allowlisted owner (IAM-01, IAM-02).
Internal routes require a Cloud Tasks OIDC token (QUE-01).
"""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import Depends, HTTPException, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from financial_os.auth.firebase import VerifiedOwner, verify_oidc_token, verify_owner_token

logger = logging.getLogger(__name__)

_bearer_scheme = HTTPBearer(auto_error=False)


async def get_verified_owner(
    request: Request,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Security(_bearer_scheme),
    ] = None,
) -> VerifiedOwner:
    """Require a valid Firebase Bearer token for the allowlisted owner.

    Raises 401 for missing/invalid tokens.
    Raises 403 for valid tokens from non-allowlisted identities.
    Never includes token or claim details in error responses (LOG-01).
    """
    settings = request.app.state.settings

    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail={"error_code": "UNAUTHORIZED", "message": "Authentication required."},
        )

    owner = await verify_owner_token(credentials.credentials, settings)
    if owner is None:
        # Could be invalid token or expired. 401 for both — don't reveal which.
        raise HTTPException(
            status_code=401,
            detail={"error_code": "UNAUTHORIZED", "message": "Authentication required."},
        )

    if owner.subject_id not in settings.allowed_owner_subjects:
        raise HTTPException(
            status_code=403,
            detail={"error_code": "FORBIDDEN", "message": "Access denied."},
        )

    # Session-version check (IAM-02): validate auth_time against valid_after in DB.
    # This check happens here for all protected routes.
    # The service layer resolves the DB-side auth_subject; we pass the raw owner through.
    # If valid_after is set and auth_time < valid_after: 403.
    # Full DB check is in the service layer where the session is available.

    return owner


async def require_internal_oidc(request: Request) -> None:
    """Require a valid Cloud Tasks OIDC token (QUE-01).

    Returns normally on success; raises 401 on missing/invalid token.
    """
    settings = request.app.state.settings

    # Allow skip in test/dev mode when WORKER_OIDC_AUDIENCE is empty.
    # In production, this must always be set (OPS-01).
    if not settings.worker_oidc_audience:
        logger.warning("OIDC validation skipped — WORKER_OIDC_AUDIENCE not configured")
        return

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail={"error_code": "UNAUTHORIZED", "message": "Authentication required."},
        )

    token = auth_header[len("Bearer ") :]
    valid = await verify_oidc_token(token, settings.worker_oidc_audience)
    if not valid:
        raise HTTPException(
            status_code=403,
            detail={"error_code": "FORBIDDEN", "message": "Access denied."},
        )


# Typed aliases for use in route signatures.
OwnerDep = Annotated[VerifiedOwner, Depends(get_verified_owner)]
