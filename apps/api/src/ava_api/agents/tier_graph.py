"""Four-tier orchestration: L1 → L2 → L2.5 Send → L3 (Phase 3)."""

from __future__ import annotations

import uuid

from ava_api.agents.l1_planner import run_l1_session
from ava_api.agents.swarm_graph import run_swarm_pipeline
from ava_api.schemas import ExecutionPlan
from ava_api.services.plan_canvas import plan_to_canvas_graph


async def run_full_tier_pipeline(
    *,
    run_id: uuid.UUID,
    brief: str,
    session_id: str,
    thread_id: str,
    user_id: str = "default",
    sync_canvas: bool = True,
    resume_swarm: bool = False,
) -> dict:
    l1 = await run_l1_session(
        session_id=session_id,
        brief=brief,
        thread_id=f"l1-{thread_id}",
        resume_confirm=True,
    )
    plan = ExecutionPlan.model_validate(l1["plan_json"])
    canvas_graph = plan_to_canvas_graph(plan) if sync_canvas else None
    swarm_result = await run_swarm_pipeline(
        run_id=run_id,
        plan=plan,
        thread_id=thread_id,
        resume=resume_swarm,
    )
    return {
        "l1": l1,
        "plan": plan.model_dump(),
        "canvas_graph": canvas_graph,
        "swarm": swarm_result,
    }
