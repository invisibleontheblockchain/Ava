from uuid import UUID

from arq import create_pool
from arq.connections import RedisSettings
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ava_api.agents.demo_plan import demo_three_persona_plan
from ava_api.agents.l2_decomposer import validate_plan
from ava_api.config import get_settings
from ava_api.db import get_db
from ava_api.schemas import RunResponse
from ava_api.schemas import ExecutionPlan, StartSwarmRunRequest
from ava_api.services.runs import create_swarm_run

router = APIRouter(prefix="/swarm", tags=["swarm"])


@router.post("/runs", response_model=RunResponse)
async def start_swarm_run(body: StartSwarmRunRequest, db: AsyncSession = Depends(get_db)):
    if body.use_demo_plan or not body.plan:
        plan = demo_three_persona_plan()
    else:
        plan = body.plan

    try:
        validate_plan(plan)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e

    run = await create_swarm_run(db, plan, canvas_id=body.canvas_id)
    await db.commit()

    redis = await create_pool(RedisSettings.from_dsn(get_settings().redis_url))
    await redis.enqueue_job("run_canvas_pipeline", str(run.id), resume=False)
    await redis.aclose()

    return RunResponse(
        id=run.id,
        canvas_id=run.canvas_id,
        status=run.status,  # type: ignore
        thread_id=run.thread_id,
        mode="swarm",
    )


@router.get("/demo-plan")
async def get_demo_plan() -> ExecutionPlan:
    return demo_three_persona_plan()
