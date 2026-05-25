"""Sync ExecutionPlan → React Flow canvas graph (Phase 3)."""

from __future__ import annotations

from ava_api.schemas import ExecutionPlan


def plan_to_canvas_graph(plan: ExecutionPlan) -> dict:
    blocks = []
    edges = []
    x = 80
    for i, task in enumerate(plan.tasks):
        block_id = f"task-{task.id}"
        blocks.append(
            {
                "id": block_id,
                "type": task.estimated_blocks[0] if task.estimated_blocks else "prompt",
                "position": {"x": x, "y": 80 + (i % 3) * 120},
                "data": {
                    "title": f"{task.persona}: {task.id}",
                    "prompt": task.description,
                    "status": "idle",
                    "config": {},
                },
                "connections": {
                    "inputs": [f"task-{d}" for d in task.dependencies],
                    "outputs": [],
                },
            }
        )
        x += 280
        for dep in task.dependencies:
            edges.append(
                {
                    "id": f"e-{dep}-{task.id}",
                    "source": f"task-{dep}",
                    "target": block_id,
                }
            )
    for b in blocks:
        outs = [e["target"] for e in edges if e["source"] == b["id"]]
        b["connections"]["outputs"] = outs
    return {"blocks": blocks, "edges": edges}
