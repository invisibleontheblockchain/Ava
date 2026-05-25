"""Enterprise Edition license gate (Phase 5)."""

from __future__ import annotations

from fastapi import HTTPException

from ava_api.config import get_settings

EE_FEATURES = {"sso", "audit_export", "marketplace_publish", "gaia_benchmark"}


def require_ee(feature: str) -> None:
    settings = get_settings()
    if feature not in EE_FEATURES:
        return
    if not settings.ee_license_key:
        raise HTTPException(
            402,
            f"Feature '{feature}' requires Ava Enterprise license (set EE_LICENSE_KEY)",
        )


def is_ee_enabled() -> bool:
    return bool(get_settings().ee_license_key)
