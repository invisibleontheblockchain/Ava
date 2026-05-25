"""MCP connector registry + mock OAuth (Phase 3)."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ava_api.config import get_settings
from ava_api.db import ConnectorModel, OAuthTokenModel

BUILTIN_CONNECTORS = [
    {
        "id": "google_drive",
        "name": "Google Drive",
        "namespace": "com.google.drive",
        "capabilities": ["read_file", "list_folder"],
        "mcp_endpoint": "/mcp/google_drive",
    },
    {
        "id": "github",
        "name": "GitHub",
        "namespace": "com.github",
        "capabilities": ["read_repo", "list_issues"],
        "mcp_endpoint": "/mcp/github",
    },
    {
        "id": "slack",
        "name": "Slack",
        "namespace": "com.slack",
        "capabilities": ["post_message", "read_channel"],
        "mcp_endpoint": "/mcp/slack",
    },
]


async def seed_connectors(session: AsyncSession) -> None:
    for c in BUILTIN_CONNECTORS:
        existing = await session.get(ConnectorModel, c["id"])
        if not existing:
            session.add(ConnectorModel(**c))


async def list_connectors(session: AsyncSession) -> list[dict]:
    result = await session.execute(select(ConnectorModel).where(ConnectorModel.enabled.is_(True)))
    return [
        {
            "id": r.id,
            "name": r.name,
            "namespace": r.namespace,
            "capabilities": r.capabilities,
            "mcp_endpoint": r.mcp_endpoint,
        }
        for r in result.scalars().all()
    ]


async def mock_oauth_connect(
    session: AsyncSession,
    *,
    user_id: str,
    connector_id: str,
) -> dict:
    settings = get_settings()
    token = f"mock_token_{connector_id}_{user_id}"
    row = OAuthTokenModel(
        user_id=user_id,
        connector_id=connector_id,
        access_token=token,
        refresh_token=f"refresh_{token}",
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )
    session.add(row)
    await session.flush()
    return {"connector_id": connector_id, "connected": True, "mock": settings.mock_connectors}


async def connector_fetch(
    session: AsyncSession,
    *,
    user_id: str,
    connector_id: str,
    resource: str,
) -> str:
    settings = get_settings()
    if settings.mock_connectors:
        return (
            f"MOCK {connector_id} resource '{resource}':\n"
            "Sample document content fetched via connector for downstream blocks."
        )
    from ava_api.platform.nango import nango_get_token

    token = await nango_get_token(session, user_id=user_id, connector_id=connector_id)
    if not token:
        raise ValueError("Connector not authenticated — run OAuth connect first")
    return (
        f"Authenticated fetch from {connector_id} (token {token[:8]}…):\n"
        f"Resource: {resource}\n"
        "Document body text for downstream L3 blocks."
    )
