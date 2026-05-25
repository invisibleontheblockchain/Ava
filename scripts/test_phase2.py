#!/usr/bin/env python3
"""Phase 2 go/no-go — 3-persona parallel batch + merge task (MOCK_LLM)."""

from __future__ import annotations

import asyncio
import os
import sys
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps", "api", "src"))
os.environ.setdefault("MOCK_LLM", "true")


async def main() -> int:
    from ava_api.agents.demo_plan import demo_three_persona_plan
    from ava_api.agents.l2_decomposer import get_task_parallel_batches
    from ava_api.agents.swarm_graph import run_swarm_pipeline
    from ava_api.db import RunModel, init_tables, get_session_factory

    await init_tables()
    plan = demo_three_persona_plan()
    batches = get_task_parallel_batches(plan)
    assert len(batches[0]) == 3, "first batch must be 3 parallel personas"
    print("PASS: L2 parallel batches", [[t.id for t in b] for b in batches])

    factory = get_session_factory()
    async with factory() as session:
        run = RunModel(thread_id=str(uuid.uuid4()), status="pending", mode="swarm", plan=plan.model_dump())
        session.add(run)
        await session.commit()
        run_id = run.id
        thread_id = run.thread_id

    final = await run_swarm_pipeline(
        run_id=run_id,
        plan=plan,
        thread_id=thread_id,
        resume=False,
    )
    assert not final.get("error"), final.get("error")
    results = final.get("task_results_map") or {}
    assert len(results) == 4, results
    assert all(r.get("status") == "complete" for r in results.values())
    print("PASS: swarm pipeline complete", list(results.keys()))

    final2 = await run_swarm_pipeline(
        run_id=run_id,
        plan=plan,
        thread_id=thread_id,
        resume=True,
    )
    assert not final2.get("error")
    print("PASS: swarm resume")

    print("\n=== Phase 2 go/no-go: ALL CHECKS PASSED ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
