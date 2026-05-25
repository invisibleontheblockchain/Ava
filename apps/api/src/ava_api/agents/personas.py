"""L2.5 Persona agents — scoped prompts and task execution (Phase 2)."""

from __future__ import annotations

import json
import uuid
from typing import Any

from ava_api.db import get_session_factory
from ava_api.executor.blocks import execute_block, run_llm
from ava_api.platform.memory import search_memory, store_memory
from ava_api.schemas import CanvasBlock
from ava_api.schemas import ExecutionPlan, PersonaType, PlanTask

PERSONA_TOOLS: dict[PersonaType, list[str]] = {
    "researcher": ["web", "prompt", "file", "connector"],
    "analyst": ["table", "excel", "prompt"],
    "writer": ["report", "memo", "presentation", "prompt"],
    "coder": ["code", "app", "prompt"],
}

PERSONA_SYSTEM_PROMPTS: dict[PersonaType, str] = {
    "researcher": (
        "You are the Researcher persona. Gather facts from sources, cite specifics, "
        "and produce structured raw findings. Prefer accuracy over synthesis."
    ),
    "analyst": (
        "You are the Analyst persona. Compare datasets, build tables, identify patterns, "
        "and produce quantitative or structured comparisons."
    ),
    "writer": (
        "You are the Writer persona. Turn research and analysis into clear prose, "
        "executive summaries, and client-ready narrative."
    ),
    "coder": (
        "You are the Coder persona. Produce concise technical notes, pseudocode, "
        "or implementation sketches when asked."
    ),
}


def _task_context_from_results(
    task: PlanTask,
    prior_results: dict[str, dict[str, Any]],
) -> dict[str, dict]:
    bundle: dict[str, dict] = {}
    for dep_id in task.dependencies:
        if dep_id in prior_results:
            r = prior_results[dep_id]
            bundle[dep_id] = {
                "title": f"{r.get('persona', 'task')}:{dep_id}",
                "type": "text",
                "content": r.get("content", ""),
            }
    return bundle


async def _run_estimated_block(
    *,
    run_id: uuid.UUID,
    block_type: str,
    task: PlanTask,
    context: dict[str, dict],
    block_index: int,
) -> str:
    """Execute one estimated block type for a persona task."""
    block_id = f"{task.id}-b{block_index}"
    data: dict[str, Any] = {
        "title": f"{task.persona}:{block_type}",
        "prompt": task.description,
        "config": {},
    }
    if block_type == "web":
        data["config"] = {"url": "https://example.com"}
        data["prompt"] = "https://example.com"

    block = CanvasBlock(
        id=block_id,
        type=block_type,  # type: ignore[arg-type]
        data=data,
        connections={"inputs": [], "outputs": []},
    )
    result = await execute_block(block, context, run_id=run_id)
    return result.get("content") or ""


async def execute_persona_task(
    *,
    run_id: uuid.UUID,
    plan: ExecutionPlan,
    task: PlanTask,
    prior_results: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Run a single plan task under its persona — sequential estimated_blocks then synthesis."""
    from ava_api.services.events import publish_event

    run_id_str = str(run_id)
    await publish_event(
        run_id_str,
        {
            "type": "persona_status",
            "task_id": task.id,
            "persona": task.persona,
            "status": "running",
        },
    )

    context = _task_context_from_results(task, prior_results)
    block_outputs: list[str] = []

    allowed = set(PERSONA_TOOLS.get(task.persona, ["prompt"]))
    blocks_to_run = [b for b in (task.estimated_blocks or ["prompt"]) if b in allowed] or ["prompt"]

    async with get_session_factory()() as mem_session:
        hits = await search_memory(
            mem_session,
            tenant_id="default",
            user_id="default",
            query=task.description,
        )
        if hits:
            context["memory"] = {"title": "memory", "type": "text", "content": hits[0]["content"]}
        await store_memory(
            mem_session,
            tenant_id="default",
            user_id="default",
            content=f"{task.persona}:{task.description}",
            meta={"task_id": task.id},
        )
        await mem_session.commit()

    for i, block_type in enumerate(blocks_to_run):
        try:
            content = await _run_estimated_block(
                run_id=run_id,
                block_type=block_type,
                task=task,
                context={**context, **{f"step-{j}": {"title": f"s{j}", "content": block_outputs[j]} for j in range(len(block_outputs))}},
                block_index=i,
            )
            block_outputs.append(content)
        except Exception as exc:
            await publish_event(
                run_id_str,
                {
                    "type": "persona_status",
                    "task_id": task.id,
                    "persona": task.persona,
                    "status": "error",
                    "error": str(exc),
                },
            )
            raise

    persona_system = PERSONA_SYSTEM_PROMPTS[task.persona]
    synthesis_user = json.dumps(
        {
            "goal": plan.goal,
            "task": task.description,
            "block_outputs": block_outputs,
            "output_type": task.output_type,
        },
        indent=2,
    )
    final_text, _ = await run_llm(
        system=persona_system,
        user=f"Synthesize the final {task.output_type} output for this task:\n{synthesis_user}",
    )

    result = {
        "task_id": task.id,
        "persona": task.persona,
        "content": final_text,
        "status": "complete",
    }
    await publish_event(
        run_id_str,
        {
            "type": "persona_complete",
            "task_id": task.id,
            "persona": task.persona,
            "output": {"content": final_text[:2000]},
        },
    )
    return result
