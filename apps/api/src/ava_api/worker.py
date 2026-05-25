"""ARQ worker — decouples HTTP from long-running LangGraph execution."""

import uuid

from arq.connections import RedisSettings

from ava_api.config import get_settings
from ava_api.services.runs import execute_run


async def run_canvas_pipeline(ctx, run_id: str, resume: bool = False) -> dict:
    await execute_run(uuid.UUID(run_id), resume=resume)
    return {"run_id": run_id, "ok": True}


class WorkerSettings:
    functions = [run_canvas_pipeline]
    redis_settings = RedisSettings.from_dsn(get_settings().redis_url)
    max_jobs = 10
    job_timeout = 3600  # 60+ min runs per blueprint Phase 4 target
