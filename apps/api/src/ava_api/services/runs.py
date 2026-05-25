import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from ava_api.agents.demo_plan import demo_three_persona_plan
from ava_api.agents.swarm_graph import run_swarm_pipeline
from ava_api.db import CanvasModel, RunModel
from ava_api.executor.pipeline import run_pipeline
from ava_api.schemas import CanvasGraph, RunStatus
from ava_api.schemas import ExecutionPlan
from ava_api.services.events import publish_event
from ava_api.validation import validate_canvas_graph


async def create_canvas_run(session: AsyncSession, canvas_id: uuid.UUID) -> RunModel:
    canvas = await session.get(CanvasModel, canvas_id)
    if not canvas:
        raise ValueError("Canvas not found")

    run = RunModel(
        canvas_id=canvas_id,
        thread_id=str(uuid.uuid4()),
        status="pending",
        mode="canvas",
    )
    session.add(run)
    await session.flush()
    return run


async def create_swarm_run(
    session: AsyncSession,
    plan: ExecutionPlan,
    *,
    canvas_id: uuid.UUID | None = None,
) -> RunModel:
    run = RunModel(
        canvas_id=canvas_id,
        thread_id=str(uuid.uuid4()),
        status="pending",
        mode="swarm",
        plan=plan.model_dump(),
    )
    session.add(run)
    await session.flush()
    return run


async def update_run_status(
    session: AsyncSession, run_id: uuid.UUID, status: RunStatus, error: str | None = None
) -> None:
    run = await session.get(RunModel, run_id)
    if run:
        run.status = status
        if error:
            run.error = error
        await session.flush()


async def execute_run(run_id: uuid.UUID, *, resume: bool = False) -> None:
    from ava_api.db import get_session_factory

    factory = get_session_factory()

    async with factory() as session:
        run = await session.get(RunModel, run_id)
        if not run:
            raise ValueError("Run not found")
        await update_run_status(session, run_id, "running")
        await session.commit()
        mode = run.mode or "canvas"
        thread_id = run.thread_id
        canvas_id = run.canvas_id
        plan_data = run.plan

    try:
        if mode == "swarm":
            plan = ExecutionPlan.model_validate(plan_data or demo_three_persona_plan().model_dump())
            final = await run_swarm_pipeline(
                run_id=run_id,
                plan=plan,
                thread_id=thread_id,
                resume=resume,
            )
            status: RunStatus = "error" if final.get("error") else "complete"
            error = final.get("error")
        else:
            if not canvas_id:
                raise ValueError("Canvas run missing canvas_id")
            async with factory() as session:
                canvas = await session.get(CanvasModel, canvas_id)
                if not canvas:
                    raise ValueError("Canvas not found")
                graph = CanvasGraph.model_validate(canvas.graph)
            validate_canvas_graph(graph)
            final = await run_pipeline(
                run_id=run_id,
                canvas_id=canvas_id,
                canvas_graph=graph,
                thread_id=thread_id,
                resume=resume,
            )
            status = "error" if final.get("error") else "complete"
            error = final.get("error")

        async with factory() as session:
            await update_run_status(session, run_id, status, error)
            await session.commit()
    except Exception as exc:
        async with factory() as session:
            await update_run_status(session, run_id, "error", str(exc))
            await session.commit()
        await publish_event(str(run_id), {"type": "run_status", "status": "error", "error": str(exc)})
        raise


async def create_run(
    session: AsyncSession,
    *,
    canvas_id: uuid.UUID | None = None,
    mode: str = "canvas",
    plan: dict | None = None,
) -> RunModel:
    if mode == "swarm":
        plan_obj = ExecutionPlan.model_validate(plan or demo_three_persona_plan().model_dump())
        return await create_swarm_run(session, plan_obj, canvas_id=canvas_id)
    if not canvas_id:
        raise ValueError("canvas_id required for canvas mode")
    return await create_canvas_run(session, canvas_id)
