"""Benchmarks + ops endpoints (Phase 5)."""

from __future__ import annotations

from fastapi import APIRouter

from ava_api.benchmarks.deepsearchqa import run_deepsearchqa_harness
from ava_api.benchmarks.gaia import run_gaia_harness
from ava_api.platform.reliability import get_dlq

router = APIRouter(prefix="/bench", tags=["bench"])


@router.post("/gaia")
async def gaia_run(limit: int = 10):
    return await run_gaia_harness(limit=limit)


@router.get("/dlq")
async def dead_letter_queue():
    return {"items": get_dlq()}


@router.post("/deepsearchqa")
async def deepsearchqa_run(limit: int = 10):
    return await run_deepsearchqa_harness(limit=limit)
