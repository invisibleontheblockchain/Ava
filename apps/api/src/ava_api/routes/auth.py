"""Auth — JWT dev + SAML/OIDC stubs (Phase 5)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException
from jose import jwt
from pydantic import BaseModel

from ava_api.config import get_settings
from ava_api.platform.ee import require_ee

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: str
    password: str = ""


class SsoRequest(BaseModel):
    provider: str  # saml | oidc
    token: str


@router.post("/login")
async def login(body: LoginRequest):
    settings = get_settings()
    payload = {
        "sub": body.email,
        "tenant_id": settings.default_tenant_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=24),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm="HS256")
    return {"access_token": token, "token_type": "bearer"}


@router.post("/sso")
async def sso_login(body: SsoRequest):
    require_ee("sso")
    if not body.token:
        raise HTTPException(400, "SSO token required")
    settings = get_settings()
    payload = {
        "sub": f"sso-{body.provider}",
        "tenant_id": settings.default_tenant_id,
        "provider": body.provider,
        "exp": datetime.now(timezone.utc) + timedelta(hours=8),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm="HS256")
    return {"access_token": token, "token_type": "bearer", "provider": body.provider}
