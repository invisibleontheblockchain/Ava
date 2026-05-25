"""L1 Planning assistant — intake, clarifications, plan, HITL confirm (Phase 3)."""

from __future__ import annotations

import json
import uuid
from typing import Annotated, TypedDict

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import END, START, StateGraph
from typing_extensions import NotRequired

from ava_api.agents.l2_decomposer import validate_plan
from ava_api.executor.pipeline import get_checkpointer
from ava_api.platform.routing import route_completion
from ava_api.schemas import ExecutionPlan, PlanTask


class L1State(TypedDict):
    session_id: str
    brief: str
    messages: Annotated[list[dict], lambda a, b: (a or []) + (b or [])]
    clarifications: list[str]
    plan_json: NotRequired[dict | None]
    status: str
    user_preferences: NotRequired[dict]


async def intake_node(state: L1State) -> dict:
    brief = state["brief"]
    prefs = state.get("user_preferences") or {}
    system = (
        "You are Ava L1 Planner. Given a user brief, decide if clarifying questions are needed. "
        "Return JSON: {\"clarifications\": [\"q1\", ...], \"notes\": \"...\"} with 0-3 questions max."
    )
    user = f"Brief:\n{brief}\n\nUser preferences:\n{json.dumps(prefs)}"
    text, _, _ = await route_completion(system=system, user=user, task_type="analysis")
    try:
        parsed = json.loads(text[text.find("{") : text.rfind("}") + 1])
        clarifications = (parsed.get("clarifications") or [])[:3]
    except Exception:
        clarifications = []
    if not clarifications and len(brief) < 40:
        clarifications = ["What is the primary deliverable format?"]
    return {
        "clarifications": clarifications,
        "messages": [{"role": "assistant", "content": text}],
        "status": "clarify" if clarifications else "planning",
    }


async def plan_node(state: L1State) -> dict:
    brief = state["brief"]
    clarifications = state.get("clarifications") or []
    system = (
        "Produce an ExecutionPlan JSON with fields: goal, estimated_duration_minutes, "
        "tasks (id, description, persona, dependencies, estimated_blocks, output_type), "
        "deliverables, clarifications_needed."
    )
    user = f"Brief: {brief}\nClarifications asked: {clarifications}\nGenerate 3-5 tasks with personas."
    text, _, _ = await route_completion(system=system, user=user, task_type="writing")
    tasks = [
        PlanTask(
            id="t1",
            description="Research upstream sources",
            persona="researcher",
            dependencies=[],
            estimated_blocks=["web", "prompt"],
        ),
        PlanTask(
            id="t2",
            description="Analyze findings",
            persona="analyst",
            dependencies=["t1"],
            estimated_blocks=["table", "prompt"],
        ),
        PlanTask(
            id="t3",
            description="Write deliverable",
            persona="writer",
            dependencies=["t1", "t2"],
            estimated_blocks=["report"],
        ),
    ]
    plan = ExecutionPlan(
        goal=brief[:500] or "User goal",
        estimated_duration_minutes=20,
        tasks=tasks,
        deliverables=["report"],
    )
    try:
        if "{" in text:
            raw = json.loads(text[text.find("{") : text.rfind("}") + 1])
            if raw.get("tasks"):
                plan = ExecutionPlan.model_validate({**plan.model_dump(), **raw})
    except Exception:
        pass
    validate_plan(plan)
    return {
        "plan_json": plan.model_dump(),
        "messages": [{"role": "assistant", "content": plan.model_dump_json()}],
        "status": "awaiting_confirm",
    }


async def human_confirm_node(state: L1State) -> dict:
    return {"status": "confirmed"}


async def compile_l1_graph(checkpointer=None):
    builder = StateGraph(L1State)
    builder.add_node("intake", intake_node)
    builder.add_node("plan", plan_node)
    builder.add_node("human_confirm", human_confirm_node)
    builder.add_edge(START, "intake")
    builder.add_edge("intake", "plan")
    builder.add_edge("plan", "human_confirm")
    builder.add_edge("human_confirm", END)
    if checkpointer is None:
        checkpointer = await get_checkpointer()
    return builder.compile(checkpointer=checkpointer, interrupt_before=["human_confirm"])


async def run_l1_session(
    *,
    session_id: str,
    brief: str,
    thread_id: str,
    user_preferences: dict | None = None,
    resume_confirm: bool = False,
) -> L1State:
    graph = await compile_l1_graph()
    config = {"configurable": {"thread_id": thread_id}}
    if resume_confirm:
        result = await graph.ainvoke(None, config=config)
        return result  # type: ignore
    initial: L1State = {
        "session_id": session_id,
        "brief": brief,
        "messages": [],
        "clarifications": [],
        "status": "intake",
        "user_preferences": user_preferences or {},
    }
    result = await graph.ainvoke(initial, config=config)
    return result  # type: ignore
