"""Audit trail export (Phase 5 / SOC2-oriented)."""

from __future__ import annotations

import csv
import io
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ava_api.db import AuditLogModel, get_db
from ava_api.platform.ee import require_ee

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/export")
async def export_audit_logs(
    tenant_id: str = "default",
    db: AsyncSession = Depends(get_db),
):
    require_ee("audit_export")
    result = await db.execute(
        select(AuditLogModel)
        .where(AuditLogModel.tenant_id == tenant_id)
        .order_by(AuditLogModel.created_at.desc())
        .limit(10000)
    )
    rows = result.scalars().all()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["id", "tenant_id", "agent_id", "action", "target", "created_at", "meta"])
    for r in rows:
        writer.writerow(
            [
                str(r.id),
                r.tenant_id,
                r.agent_id,
                r.action,
                r.target,
                r.created_at.isoformat() if r.created_at else "",
                r.meta,
            ]
        )
    buf.seek(0)
    filename = f"ava-audit-{tenant_id}-{datetime.now(timezone.utc).date()}.csv"
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
