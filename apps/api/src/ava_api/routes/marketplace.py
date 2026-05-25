"""Connector marketplace (Phase 5)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ava_api.db import get_db
from ava_api.platform.connectors import BUILTIN_CONNECTORS, list_connectors, seed_connectors
from ava_api.platform.ee import require_ee

router = APIRouter(prefix="/marketplace", tags=["marketplace"])


@router.get("/connectors")
async def marketplace_list(db: AsyncSession = Depends(get_db)):
    await seed_connectors(db)
    await db.commit()
    installed = {c["id"] for c in await list_connectors(db)}
    catalog = []
    for c in BUILTIN_CONNECTORS:
        catalog.append({**c, "installed": c["id"] in installed, "verified": True})
    return {"connectors": catalog}


@router.post("/publish")
async def publish_connector(namespace: str, name: str):
    require_ee("marketplace_publish")
    if not namespace.startswith("com."):
        return {"error": "Namespace must use reverse-DNS (com.vendor.product)"}
    return {"published": True, "namespace": namespace, "name": name}
