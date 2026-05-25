"""OpenTelemetry + audit logging (Phase 5)."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from ava_api.config import get_settings
from ava_api.db import AuditLogModel

_tracer = None


def setup_tracing(app) -> None:
    global _tracer
    if not get_settings().enable_otel:
        return
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        provider = TracerProvider()
        trace.set_tracer_provider(provider)
        FastAPIInstrumentor.instrument_app(app)
        _tracer = trace.get_tracer("ava")
    except Exception:
        _tracer = None


async def audit_log(
    session: AsyncSession,
    *,
    tenant_id: str,
    agent_id: str,
    action: str,
    target: str,
    meta: dict | None = None,
) -> None:
    session.add(
        AuditLogModel(
            tenant_id=tenant_id,
            agent_id=agent_id,
            action=action,
            target=target,
            meta=meta or {},
        )
    )
    await session.flush()
