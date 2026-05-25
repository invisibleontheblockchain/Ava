import json
from uuid import UUID

from arq import create_pool
from arq.connections import RedisSettings
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ava_api.config import get_settings
from ava_api.config import get_settings
from ava_api.db import CanvasModel, RunModel, get_db
from ava_api.schemas import RunResponse, StartRunRequest
from ava_api.services.events import publish_event, subscribe_events
from ava_api.services.runs import create_canvas_run

router = APIRouter(prefix="/runs", tags=["runs"])


@router.post("", response_model=RunResponse)
async def start_run(body: StartRunRequest, db: AsyncSession = Depends(get_db)):
    run = await create_canvas_run(db, body.canvas_id)
    await db.commit()

    redis = await create_pool(RedisSettings.from_dsn(get_settings().redis_url))
    await redis.enqueue_job("run_canvas_pipeline", str(run.id), resume=False)
    await redis.aclose()

    return RunResponse(
        id=run.id,
        canvas_id=run.canvas_id,
        status=run.status,  # type: ignore
        thread_id=run.thread_id,
        mode=run.mode or "canvas",
    )


@router.get("/{run_id}", response_model=RunResponse)
async def get_run(run_id: UUID, db: AsyncSession = Depends(get_db)):
    run = await db.get(RunModel, run_id)
    if not run:
        raise HTTPException(404, "Run not found")
    return RunResponse(
        id=run.id,
        canvas_id=run.canvas_id,
        status=run.status,  # type: ignore
        thread_id=run.thread_id,
        mode=run.mode or "canvas",
    )


@router.post("/{run_id}/resume", response_model=RunResponse)
async def resume_run(run_id: UUID, db: AsyncSession = Depends(get_db)):
    """Resume from LangGraph checkpoint after crash (Phase 1 go/no-go)."""
    run = await db.get(RunModel, run_id)
    if not run:
        raise HTTPException(404, "Run not found")

    redis = await create_pool(RedisSettings.from_dsn(get_settings().redis_url))
    await redis.enqueue_job("run_canvas_pipeline", str(run.id), resume=True)
    await redis.aclose()

    run.status = "running"
    await db.commit()

    return RunResponse(
        id=run.id,
        canvas_id=run.canvas_id,
        status=run.status,  # type: ignore
        thread_id=run.thread_id,
        mode=run.mode or "canvas",
    )


@router.post("/{run_id}/approve")
async def approve_human_gate(
    run_id: UUID,
    block_id: str = Query(..., description="human_gate block id"),
    db: AsyncSession = Depends(get_db),
):
    """Approve human_gate block and re-queue pipeline (Document 2 §3 human_gate)."""
    run = await db.get(RunModel, run_id)
    if not run:
        raise HTTPException(404, "Run not found")
    if not run.canvas_id:
        raise HTTPException(400, "Approve only supported for canvas runs")

    canvas = await db.get(CanvasModel, run.canvas_id)
    if not canvas:
        raise HTTPException(404, "Canvas not found")

    graph = canvas.graph or {}
    updated = False
    for block in graph.get("blocks", []):
        if block.get("id") == block_id and block.get("type") == "human_gate":
            data = block.setdefault("data", {})
            cfg = data.setdefault("config", {})
            cfg["approved"] = True
            updated = True
    if not updated:
        raise HTTPException(404, "human_gate block not found")

    canvas.graph = graph
    await db.commit()

    settings = get_settings()
    await publish_event(
        str(run_id),
        {"type": "block_status", "block_id": block_id, "status": "approved"},
    )

    redis = await create_pool(RedisSettings.from_dsn(settings.redis_url))
    await redis.enqueue_job("run_canvas_pipeline", str(run.id), resume=True)
    await redis.aclose()

    return {"run_id": run_id, "block_id": block_id, "approved": True}


@router.get("/{run_id}/events")
async def stream_run_events(run_id: UUID):
    """SSE stream of run progress via Redis Pub/Sub."""

    async def event_generator():
        yield f"data: {json.dumps({'type': 'connected', 'run_id': str(run_id)})}\n\n"
        async for event in subscribe_events(str(run_id)):
            yield f"data: {json.dumps(event)}\n\n"
            if event.get("type") == "run_status" and event.get("status") in ("complete", "error"):
                break

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
