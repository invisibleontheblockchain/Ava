"""Phase 2 swarm pipeline — L2 task batches + L2.5 personas via LangGraph Send API."""

from __future__ import annotations

import uuid
from operator import add
from typing import Annotated, Any, TypedDict

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Send
from typing_extensions import NotRequired

from ava_api.agents.l2_decomposer import get_task_parallel_batches, validate_plan
from ava_api.agents.persona_graphs import PERSONA_TYPES, compile_persona_subgraph
from ava_api.executor.pipeline import get_checkpointer
from ava_api.schemas import ExecutionPlan, PlanTask
from ava_api.services.events import publish_event


def _merge_results(
    left: dict[str, dict[str, Any]] | None,
    right: dict[str, dict[str, Any]] | None,
) -> dict[str, dict[str, Any]]:
    base = dict(left or {})
    base.update(right or {})
    return base


class SwarmState(TypedDict):
    run_id: str
    plan_json: dict
    task_batch_index: int
    task_results_map: Annotated[dict[str, dict[str, Any]], _merge_results]
    current_task: NotRequired[dict]
    error: NotRequired[str | None]


def _persona_node_name(persona: str) -> str:
    return f"run_persona_{persona}"


async def _run_persona_via_subgraph(state: SwarmState, persona: str) -> dict[str, Any]:
    """L2.5 — execute via persona-specific compiled subgraph."""
    task = PlanTask.model_validate(state["current_task"])
    if task.persona != persona:
        return {}
    subgraph = compile_persona_subgraph(persona)  # type: ignore[arg-type]
    prior = dict(state.get("task_results_map") or {})
    inner = await subgraph.ainvoke(
        {
            "run_id": state["run_id"],
            "plan_json": state["plan_json"],
            "current_task": state["current_task"],
            "prior_results": prior,
        }
    )
    if inner.get("error"):
        return {"error": inner["error"], "task_results_map": inner.get("task_results_map", {})}
    return {"task_results_map": inner.get("task_results_map", {})}


def _make_swarm_persona_node(persona: str):
    async def node(state: SwarmState) -> dict[str, Any]:
        return await _run_persona_via_subgraph(state, persona)

    return node


async def advance_batch(state: SwarmState) -> dict[str, Any]:
    return {"task_batch_index": state.get("task_batch_index", 0) + 1}


def _fan_out_to_persona_node(state: SwarmState) -> list[Send] | str:
    if state.get("error"):
        return END
    plan = ExecutionPlan.model_validate(state["plan_json"])
    batches = get_task_parallel_batches(plan)
    idx = state.get("task_batch_index", 0)
    if idx >= len(batches):
        return END
    batch = batches[idx]
    sends: list[Send] = []
    for task in batch:
        node_name = _persona_node_name(task.persona)
        sends.append(
            Send(
                node_name,
                {
                    "run_id": state["run_id"],
                    "plan_json": state["plan_json"],
                    "current_task": task.model_dump(),
                    "task_results_map": state.get("task_results_map") or {},
                },
            )
        )
    return sends


def compile_swarm_graph():
    builder = StateGraph(SwarmState)
    for persona in PERSONA_TYPES:
        builder.add_node(_persona_node_name(persona), _make_swarm_persona_node(persona))
        builder.add_edge(_persona_node_name(persona), "advance_batch")
    builder.add_node("advance_batch", advance_batch)
    builder.add_conditional_edges(START, _fan_out_to_persona_node)
    builder.add_conditional_edges("advance_batch", _fan_out_to_persona_node)
    return builder


async def run_swarm_pipeline(
    *,
    run_id: uuid.UUID,
    plan: ExecutionPlan,
    thread_id: str,
    resume: bool = False,
) -> SwarmState:
    validate_plan(plan)
    plan.run_id = str(run_id)

    checkpointer = await get_checkpointer()
    graph = compile_swarm_graph().compile(checkpointer=checkpointer)
    config = {"configurable": {"thread_id": thread_id}}

    input_state: SwarmState | None
    if resume:
        snap = await graph.aget_state(config)
        input_state = None if snap.values else {
            "run_id": str(run_id),
            "plan_json": plan.model_dump(),
            "task_batch_index": 0,
            "task_results_map": {},
            "error": None,
        }
    else:
        input_state = {
            "run_id": str(run_id),
            "plan_json": plan.model_dump(),
            "task_batch_index": 0,
            "task_results_map": {},
            "error": None,
        }

    await publish_event(str(run_id), {"type": "run_status", "status": "running", "mode": "swarm"})

    final: SwarmState | None = None
    async for event in graph.astream(input_state, config=config):
        for _node, update in event.items():
            if not isinstance(update, dict):
                continue
            if final is None:
                final = dict(input_state or (await graph.aget_state(config)).values or {})  # type: ignore
            for k, v in update.items():
                if k == "task_results_map" and isinstance(v, dict):
                    merged = dict(final.get("task_results_map") or {})
                    merged.update(v)
                    final["task_results_map"] = merged  # type: ignore
                else:
                    final[k] = v  # type: ignore

    if final is None:
        snap = await graph.aget_state(config)
        final = dict(snap.values or {})  # type: ignore

    status = "error" if final.get("error") else "complete"
    await publish_event(
        str(run_id),
        {"type": "run_status", "status": status, "mode": "swarm", "error": final.get("error")},
    )
    return final
