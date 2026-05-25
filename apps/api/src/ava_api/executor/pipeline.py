"""Phase 1 LangGraph: single StateGraph, batch DAG executor inside one node loop."""

from __future__ import annotations

import uuid
from operator import add
from typing import Annotated, Any, TypedDict

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import END, StateGraph
from psycopg_pool import AsyncConnectionPool
from typing_extensions import NotRequired

from ava_api.executor.dag import build_digraph, get_parallel_batches
from ava_api.executor.runner import DAGExecutor
from ava_api.schemas import CanvasGraph
from ava_api.services.events import publish_event

_checkpointer: AsyncPostgresSaver | None = None
_pool: AsyncConnectionPool | None = None


def _merge_dicts(left: dict[str, str] | None, right: dict[str, str] | None) -> dict[str, str]:
    base = dict(left or {})
    base.update(right or {})
    return base


class PipelineState(TypedDict):
    """LangGraph state — primitives + UUID refs only (Document 2 §2)."""

    run_id: str
    canvas_id: str
    graph_json: dict
    batch_index: int
    completed_blocks: Annotated[list[str], add]
    block_status: Annotated[dict[str, str], _merge_dicts]
    output_refs: Annotated[dict[str, str], _merge_dicts]
    error: NotRequired[str | None]


async def get_checkpointer() -> AsyncPostgresSaver:
    global _checkpointer, _pool
    if _checkpointer is None:
        from ava_api.config import get_settings

        settings = get_settings()
        _pool = AsyncConnectionPool(
            conninfo=settings.langgraph_database_url,
            max_size=10,
            kwargs={"autocommit": True},
        )
        _checkpointer = AsyncPostgresSaver(_pool)
        await _checkpointer.setup()
    return _checkpointer


async def execute_batch(state: PipelineState) -> dict[str, Any]:
    """Single LangGraph node: run one parallel batch via DAGExecutor."""
    run_id = uuid.UUID(state["run_id"])
    graph = CanvasGraph.model_validate(state["graph_json"])
    batch_index = state.get("batch_index", 0)

    executor = DAGExecutor(graph, run_id)
    result = await executor.run_batch(batch_index)

    update: dict[str, Any] = {
        "batch_index": result["batch_index"],
        "output_refs": result.get("output_refs") or {},
        "block_status": result.get("block_status") or {},
        "completed_blocks": result.get("completed_blocks") or [],
    }
    if result.get("error"):
        update["error"] = result["error"]
    return update


def _route_after_batch(state: PipelineState) -> str:
    if state.get("error"):
        return "end"
    graph = CanvasGraph.model_validate(state["graph_json"])
    batches = get_parallel_batches(build_digraph(graph))
    if state.get("batch_index", 0) >= len(batches):
        return "end"
    return "continue"


def compile_phase1_graph():
    """Single-agent StateGraph — one execute_batch node, loop until DAG done."""
    builder = StateGraph(PipelineState)
    builder.add_node("execute_batch", execute_batch)
    builder.set_entry_point("execute_batch")
    builder.add_conditional_edges(
        "execute_batch",
        _route_after_batch,
        {"continue": "execute_batch", "end": END},
    )
    return builder


async def run_pipeline(
    *,
    run_id: uuid.UUID,
    canvas_id: uuid.UUID,
    canvas_graph: CanvasGraph,
    thread_id: str,
    resume: bool = False,
) -> PipelineState:
    checkpointer = await get_checkpointer()
    graph = compile_phase1_graph().compile(checkpointer=checkpointer)
    config = {"configurable": {"thread_id": thread_id}}

    input_state: PipelineState | None
    if resume:
        snap = await graph.aget_state(config)
        input_state = None if snap.values else {
            "run_id": str(run_id),
            "canvas_id": str(canvas_id),
            "graph_json": canvas_graph.model_dump(),
            "batch_index": 0,
            "completed_blocks": [],
            "block_status": {},
            "output_refs": {},
            "error": None,
        }
        resume = snap.values is not None
    else:
        input_state = {
            "run_id": str(run_id),
            "canvas_id": str(canvas_id),
            "graph_json": canvas_graph.model_dump(),
            "batch_index": 0,
            "completed_blocks": [],
            "block_status": {},
            "output_refs": {},
            "error": None,
        }

    final: PipelineState | None = None
    async for event in graph.astream(input_state, config=config):
        for _node, update in event.items():
            if not isinstance(update, dict):
                continue
            if final is None:
                if input_state is not None:
                    final = dict(input_state)  # type: ignore[arg-type]
                else:
                    snap_now = await graph.aget_state(config)
                    final = dict(snap_now.values or {})  # type: ignore[arg-type]
            for k, v in update.items():
                if k == "completed_blocks" and isinstance(v, list):
                    final[k] = list(final.get(k) or []) + v  # type: ignore[index]
                elif k in ("output_refs", "block_status") and isinstance(v, dict):
                    merged = dict(final.get(k) or {})
                    merged.update(v)
                    final[k] = merged  # type: ignore[index]
                else:
                    final[k] = v  # type: ignore[index]

    if final is None:
        snap = await graph.aget_state(config)
        final = dict(snap.values or {})  # type: ignore[arg-type]

    status = "error" if final.get("error") else "complete"
    await publish_event(
        str(run_id),
        {"type": "run_status", "status": status, "error": final.get("error")},
    )
    return final
