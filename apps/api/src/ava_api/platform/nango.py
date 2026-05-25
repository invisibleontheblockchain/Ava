"""Nango token vault integration (Document 2 §5 — self-hosted or cloud)."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from ava_api.config import get_settings
from ava_api.db import OAuthTokenModel


async def nango_connect(
    session: AsyncSession,
    *,
    user_id: str,
    connector_id: str,
    connection_id: str | None = None,
) -> dict:
    settings = get_settings()
    if not settings.nango_url or not settings.nango_secret_key:
        from ava_api.platform.connectors import mock_oauth_connect

        return await mock_oauth_connect(session, user_id=user_id, connector_id=connector_id)

    headers = {"Authorization": f"Bearer {settings.nango_secret_key}"}
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{settings.nango_url.rstrip('/')}/connection",
            headers=headers,
            json={
                "provider_config_key": connector_id,
                "connection_id": connection_id or f"{user_id}-{connector_id}",
            },
        )
        if resp.status_code >= 400:
            raise ValueError(f"Nango connect failed: {resp.text}")
        data = resp.json()
    token = data.get("credentials", {}).get("access_token") or data.get("access_token", "")
    row = OAuthTokenModel(
        user_id=user_id,
        connector_id=connector_id,
        access_token=token,
        refresh_token=data.get("refresh_token"),
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )
    session.add(row)
    await session.flush()
    return {"connector_id": connector_id, "connected": True, "nango": True}


async def nango_get_token(session: AsyncSession, *, user_id: str, connector_id: str) -> str | None:
    settings = get_settings()
    if settings.nango_url and settings.nango_secret_key:
        headers = {"Authorization": f"Bearer {settings.nango_secret_key}"}
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                f"{settings.nango_url.rstrip('/')}/connection/{user_id}-{connector_id}",
                headers=headers,
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("credentials", {}).get("access_token")
    from sqlalchemy import select

    result = await session.execute(
        select(OAuthTokenModel)
        .where(OAuthTokenModel.user_id == user_id)
        .where(OAuthTokenModel.connector_id == connector_id)
    )
    row = result.scalar_one_or_none()
    return row.access_token if row else None
