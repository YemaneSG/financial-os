from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from financial_os.auth import deps
from financial_os.auth.firebase import VerifiedOwner
from financial_os.config import Settings


@pytest.mark.asyncio
async def test_valid_non_owner_receives_403(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = Settings(owner_allowlist="google:approved-owner")
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(settings=settings)))

    async def verified_non_owner(token: str, active_settings: Settings) -> VerifiedOwner:
        assert token == "valid-token"  # noqa: S105 - synthetic test credential
        assert active_settings is settings
        return VerifiedOwner(
            subject_id="google:different-owner",
            auth_subject_id="",
            auth_time=1,
        )

    monkeypatch.setattr(deps, "verify_owner_token", verified_non_owner)

    with pytest.raises(HTTPException) as exc_info:
        await deps.get_verified_owner(
            request,  # type: ignore[arg-type]
            HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid-token"),
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == {"error_code": "FORBIDDEN", "message": "Access denied."}


@pytest.mark.asyncio
async def test_invalid_token_receives_401(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = Settings(owner_allowlist="google:approved-owner")
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(settings=settings)))

    async def invalid_token(token: str, active_settings: Settings) -> None:
        return None

    monkeypatch.setattr(deps, "verify_owner_token", invalid_token)

    with pytest.raises(HTTPException) as exc_info:
        await deps.get_verified_owner(
            request,  # type: ignore[arg-type]
            HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid-token"),
        )

    assert exc_info.value.status_code == 401


def test_cloud_environment_uses_production_posture() -> None:
    assert Settings(environment="dev").is_production is True
    assert Settings(environment="development").is_production is False
