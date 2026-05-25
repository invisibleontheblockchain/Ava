"""L1 planning API (Phase 3)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ava_api.agents.l1_planner import run_l1_session
from ava_api.db import ConversationMessageModel, PlanningSessionModel, UserProfileModel, get_db
from ava_api.schemas import ExecutionPlan
from ava_api.services.plan_canvas import plan_to_canvas_graph
from ava_api.services.runs import create_run

router = APIRouter(prefix="/planning", tags=["planning"])


class StartPlanningRequest(BaseModel):
    brief: str
    user_id: str = "default"


class ConfirmPlanRequest(BaseModel):
    plan: ExecutionPlan | None = None
    canvas_id: uuid.UUID | None = None


@router.post("/sessions")
async def start_planning(body: StartPlanningRequest, db: AsyncSession = Depends(get_db)):
    session_id = str(uuid.uuid4())
    thread_id = f"plan-{session_id}"
    prefs_row = await db.execute(
        select(UserProfileModel).where(UserProfileModel.user_id == body.user_id)
    )
    prefs = prefs_row.scalar_one_or_none()
    user_preferences = (prefs.preferences if prefs else {}) or {}

    db.add(
        PlanningSessionModel(
            session_id=session_id,
            user_id=body.user_id,
            brief=body.brief,
            status="intake",
            thread_id=thread_id,
        )
    )
    db.add(ConversationMessageModel(session_id=session_id, role="user", content=body.brief))

    state = await run_l1_session(
        session_id=session_id,
        brief=body.brief,
        thread_id=thread_id,
        user_preferences=user_preferences,
        resume_confirm=False,
    )
    plan = ExecutionPlan.model_validate(state["plan_json"])
    sess_row = await db.execute(
        select(PlanningSessionModel).where(PlanningSessionModel.session_id == session_id)
    )
    sess = sess_row.scalar_one()
    sess.plan = plan.model_dump()
    sess.status = state.get("status", "awaiting_confirm")
    await db.commit()
    return {
        "session_id": session_id,
        "status": sess.status,
        "clarifications": state.get("clarifications", []),
        "plan": plan,
        "canvas_preview": plan_to_canvas_graph(plan),
    }


@router.post("/sessions/{session_id}/confirm")
async def confirm_plan(
    session_id: str,
    body: ConfirmPlanRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PlanningSessionModel).where(PlanningSessionModel.session_id == session_id)
    )
    sess = result.scalar_one_or_none()
    if not sess:
        raise HTTPException(404, "Session not found")
    plan = body.plan or ExecutionPlan.model_validate(sess.plan)
    run = await create_run(db, canvas_id=body.canvas_id, mode="swarm", plan=plan.model_dump())
    await db.commit()
    return {"run_id": run.id, "status": "queued", "plan": plan}
