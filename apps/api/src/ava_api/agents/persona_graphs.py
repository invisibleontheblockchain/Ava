"""L2.5 — separate compiled LangGraph subgraph per persona (Document 2 Table 12)."""

from __future__ import annotations

import uuid
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph
from typing_extensions import NotRequired

from ava_api.agents.personas import execute_persona_task
from ava_api.schemas import ExecutionPlan, PersonaType, PlanTask

PERSONA_TYPES: list[PersonaType] = ["researcher", "analyst", "writer", "coder"]

_compiled: dict[str, Any] = {}


class PersonaTaskState(TypedDict):
    run_id: str
    plan_json: dict
    current_task: dict
    prior_results: dict[str, dict[str, Any]]
    task_results_map: NotRequired[dict[str, dict[str, Any]]]
    error: NotRequired[str | None]


def _make_persona_node(persona: PersonaType):
    async def node(state: PersonaTaskState) -> dict:
        task = PlanTask.model_validate(state["current_task"])
        if task.persona != persona:
            return {}
        plan = ExecutionPlan.model_validate(state["plan_json"])
        try:
            result = await execute_persona_task(
                run_id=uuid.UUID(state["run_id"]),
                plan=plan,
                task=task,
                prior_results=state.get("prior_results") or {},
            )
            return {"task_results_map": {task.id: result}}
        except Exception as exc:
            return {
                "error": str(exc),
                "task_results_map": {task.id: {"status": "error", "error": str(exc)}},
            }

    return node


def compile_persona_subgraph(persona: PersonaType):
    if persona in _compiled:
        return _compiled[persona]
    builder = StateGraph(PersonaTaskState)
    builder.add_node("execute", _make_persona_node(persona))
    builder.add_edge(START, "execute")
    builder.add_edge("execute", END)
    _compiled[persona] = builder.compile()
    return _compiled[persona]
