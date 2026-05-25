"""L2 Decomposer — Plan JSON → task dependency batches (Document 2 Phase 2)."""

from __future__ import annotations

import networkx as nx

from ava_api.executor.dag import get_parallel_batches
from ava_api.schemas import ExecutionPlan, PlanTask


def build_task_digraph(plan: ExecutionPlan) -> nx.DiGraph:
    g = nx.DiGraph()
    for task in plan.tasks:
        g.add_node(task.id, task=task)
    task_ids = {t.id for t in plan.tasks}
    for task in plan.tasks:
        for dep in task.dependencies:
            if dep not in task_ids:
                raise ValueError(f"Unknown dependency {dep!r} for task {task.id}")
            g.add_edge(dep, task.id)
    if not nx.is_directed_acyclic_graph(g):
        raise ValueError("Plan task graph contains a cycle")
    return g


def get_task_parallel_batches(plan: ExecutionPlan) -> list[list[PlanTask]]:
    """Kahn batches over plan tasks — same algorithm as canvas DAG."""
    g = build_task_digraph(plan)
    batches: list[list[PlanTask]] = []
    for node_ids in get_parallel_batches(g):
        batch_tasks = [g.nodes[n]["task"] for n in node_ids]
        batches.append(batch_tasks)
    return batches


def validate_plan(plan: ExecutionPlan) -> None:
    if not plan.tasks:
        raise ValueError("Plan must contain at least one task")
    if plan.clarifications_needed:
        raise ValueError("Plan has unresolved clarifications — cannot dispatch")
    build_task_digraph(plan)
