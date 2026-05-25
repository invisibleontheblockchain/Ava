"""FastMCP connector server (Document 2 §5 — Streamable HTTP)."""

from __future__ import annotations

from fastmcp import FastMCP

from ava_api.db import get_session_factory
from ava_api.platform.connectors import BUILTIN_CONNECTORS, connector_fetch

mcp = FastMCP("Ava Connectors")


@mcp.tool()
async def list_connector_capabilities() -> list[dict]:
    """MCP discover — list built-in connector capabilities."""
    return BUILTIN_CONNECTORS


@mcp.tool()
async def fetch_connector_resource(
    connector_id: str,
    resource: str,
    user_id: str = "default",
) -> str:
    """Fetch text from Google Drive, GitHub, or Slack via connector."""
    async with get_session_factory()() as session:
        return await connector_fetch(
            session,
            user_id=user_id,
            connector_id=connector_id,
            resource=resource,
        )


async def mcp_discover() -> dict:
    return {
        "protocol": "mcp",
        "transport": "streamable-http",
        "path": "/mcp",
        "tools": ["list_connector_capabilities", "fetch_connector_resource"],
        "servers": [c["id"] for c in BUILTIN_CONNECTORS],
    }


def mount_mcp(app) -> None:
    """Mount FastMCP Streamable HTTP transport on FastAPI app."""
    try:
        mcp_app = mcp.http_app(path="/")
        app.mount("/mcp", mcp_app)
    except Exception:
        pass
