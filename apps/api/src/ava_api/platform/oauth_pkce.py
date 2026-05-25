"""OAuth 2.1 PKCE helpers (Document 2 Phase 3)."""

from __future__ import annotations

import base64
import hashlib
import secrets
from urllib.parse import urlencode

from ava_api.config import get_settings

_pkce_store: dict[str, dict] = {}


def create_pkce_authorize_url(*, connector_id: str, user_id: str) -> dict:
    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode()).digest()
    ).rstrip(b"=").decode()
    state = secrets.token_urlsafe(16)
    _pkce_store[state] = {
        "verifier": verifier,
        "connector_id": connector_id,
        "user_id": user_id,
    }
    settings = get_settings()
    params = urlencode(
        {
            "response_type": "code",
            "client_id": "ava",
            "redirect_uri": settings.oauth_redirect_uri,
            "scope": "openid",
            "state": state,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
        }
    )
    return {
        "authorize_url": f"{settings.oauth_redirect_uri}?{params}",
        "state": state,
        "code_challenge": challenge,
    }


def exchange_pkce_code(*, state: str, code: str) -> dict:
    entry = _pkce_store.pop(state, None)
    if not entry:
        raise ValueError("Invalid OAuth state")
    return {
        "access_token": f"pkce_{code[:16]}_{entry['connector_id']}",
        "connector_id": entry["connector_id"],
        "user_id": entry["user_id"],
        "verifier": entry["verifier"],
    }
