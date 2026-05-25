"""L2 Decomposer as nested LangGraph subgraph (Phase 2/3)."""

from __future__ import annotations

from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from ava_api.agents.l2_decomposer import get_task_parallel_batches, validate_plan
from ava_api.schemas import ExecutionPlan


class L2State(TypedDict):
    plan_json: dict
    batches: list[list[dict]]
    batch_index: int


async def decompose_node(state: L2State) -> dict:
    plan = ExecutionPlan.model_validate(state["plan_json"])
    validate_plan(plan)
    batches = get_task_parallel_batches(plan)
    return {
        "batches": [[t.model_dump() for t in batch] for batch in batches],
        "batch_index": 0,
    }


async def next_batch_node(state: L2State) -> dict:
    return {"batch_index": state.get("batch_index", 0) + 1}


def _route_batches(state: L2State) -> str:
    idx = state.get("batch_index", 0)
    batches = state.get("batches") or []
    if idx >= len(batches):
        return END
    return "next_batch"


def compile_l2_subgraph():
    builder = StateGraph(L2State)
    builder.add_node("decompose", decompose_node)
    builder.add_node("next_batch", next_batch_node)
    builder.add_edge(START, "decompose")
    builder.add_conditional_edges("decompose", _route_batches)
    builder.add_edge("next_batch", _route_batches)
    return builder.compile()
