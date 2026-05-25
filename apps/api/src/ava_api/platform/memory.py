"""Agent memory — pgvector when available, else JSON fallback (Document 2 §2/5)."""

from __future__ import annotations

import uuid

import numpy as np
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from ava_api.config import get_settings
from ava_api.db import AgentMemoryModel, get_engine

_use_pgvector: bool | None = None


async def _pgvector_enabled() -> bool:
    global _use_pgvector
    if _use_pgvector is not None:
        return _use_pgvector
    try:
        async with get_engine().connect() as conn:
            r = await conn.execute(
                text(
                    "SELECT 1 FROM pg_extension WHERE extname = 'vector'"
                )
            )
            _use_pgvector = r.scalar() is not None
    except Exception:
        _use_pgvector = False
    return _use_pgvector


def _embed(text: str, dim: int | None = None) -> list[float]:
    settings = get_settings()
    d = dim or settings.embedding_dimensions
    rng = np.random.default_rng(abs(hash(text)) % (2**32))
    vec = rng.standard_normal(d)
    vec = vec / (np.linalg.norm(vec) + 1e-9)
    return vec.tolist()


async def store_memory(
    session: AsyncSession,
    *,
    tenant_id: str,
    user_id: str,
    content: str,
    meta: dict | None = None,
) -> uuid.UUID:
    embedding = _embed(content)
    row = AgentMemoryModel(
        tenant_id=tenant_id,
        user_id=user_id,
        content=content,
        embedding=embedding,
        meta=meta or {},
    )
    session.add(row)
    await session.flush()
    if await _pgvector_enabled():
        try:
            vec_literal = "[" + ",".join(str(x) for x in embedding) + "]"
            await session.execute(
                text(
                    "UPDATE agent_memory SET embedding_vec = CAST(:vec AS vector) "
                    "WHERE id = :id"
                ),
                {"vec": vec_literal, "id": str(row.id)},
            )
        except Exception:
            pass
    return row.id


async def search_memory(
    session: AsyncSession,
    *,
    tenant_id: str,
    user_id: str,
    query: str,
    top_k: int = 5,
) -> list[dict]:
    if await _pgvector_enabled():
        try:
            q = _embed(query)
            vec_literal = "[" + ",".join(str(x) for x in q) + "]"
            result = await session.execute(
                text(
                    """
                    SELECT content, meta,
                           1 - (embedding_vec <=> CAST(:q AS vector)) AS score
                    FROM agent_memory
                    WHERE tenant_id = :tenant AND user_id = :user
                      AND embedding_vec IS NOT NULL
                    ORDER BY embedding_vec <=> CAST(:q AS vector)
                    LIMIT :k
                    """
                ),
                {"q": vec_literal, "tenant": tenant_id, "user": user_id, "k": top_k},
            )
            rows = result.fetchall()
            if rows:
                return [
                    {"content": r[0], "meta": r[1] or {}, "score": float(r[2])}
                    for r in rows
                ]
        except Exception:
            pass

    q = _embed(query)
    result = await session.execute(
        select(AgentMemoryModel)
        .where(AgentMemoryModel.tenant_id == tenant_id)
        .where(AgentMemoryModel.user_id == user_id)
        .limit(200)
    )
    rows = result.scalars().all()
    scored: list[tuple[float, AgentMemoryModel]] = []
    for row in rows:
        if not row.embedding:
            continue
        v = np.array(row.embedding)
        qv = np.array(q)
        score = float(np.dot(v, qv) / (np.linalg.norm(v) * np.linalg.norm(qv) + 1e-9))
        scored.append((score, row))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [
        {"content": r.content, "score": s, "meta": r.meta}
        for s, r in scored[:top_k]
    ]
