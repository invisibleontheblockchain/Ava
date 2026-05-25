"""MCP connectors + OAuth (Phase 3)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ava_api.db import get_db
from ava_api.platform.connectors import connector_fetch, list_connectors, seed_connectors
from ava_api.platform.mcp_server import mcp_discover
from ava_api.platform.nango import nango_connect
from ava_api.platform.oauth_pkce import create_pkce_authorize_url, exchange_pkce_code

router = APIRouter(prefix="/connectors", tags=["connectors"])


class OAuthConnectRequest(BaseModel):
    user_id: str = "default"
    connector_id: str


class FetchRequest(BaseModel):
    user_id: str = "default"
    connector_id: str
    resource: str = "sample-doc"


@router.get("")
async def get_connectors(db: AsyncSession = Depends(get_db)):
    await seed_connectors(db)
    await db.commit()
    return await list_connectors(db)


@router.get("/discover")
async def discover():
    return await mcp_discover()


@router.get("/oauth/authorize")
async def oauth_authorize(connector_id: str, user_id: str = "default"):
    return create_pkce_authorize_url(connector_id=connector_id, user_id=user_id)


@router.post("/oauth/callback")
async def oauth_callback(state: str, code: str, db: AsyncSession = Depends(get_db)):
    exchanged = exchange_pkce_code(state=state, code=code)
    result = await nango_connect(
        db,
        user_id=exchanged["user_id"],
        connector_id=exchanged["connector_id"],
    )
    await db.commit()
    return result


@router.post("/oauth/connect")
async def oauth_connect(body: OAuthConnectRequest, db: AsyncSession = Depends(get_db)):
    result = await nango_connect(
        db, user_id=body.user_id, connector_id=body.connector_id
    )
    await db.commit()
    return result


@router.post("/fetch")
async def fetch_resource(body: FetchRequest, db: AsyncSession = Depends(get_db)):
    text = await connector_fetch(
        db,
        user_id=body.user_id,
        connector_id=body.connector_id,
        resource=body.resource,
    )
    return {"content": text}
