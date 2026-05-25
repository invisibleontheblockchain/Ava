#!/usr/bin/env python3
"""
Phase 1 go/no-go test (Document 2).

Requires: postgres + redis running, API not required (runs pipeline in-process).

Usage:
  MOCK_LLM=true DATABASE_URL=... LANGGRAPH_DATABASE_URL=... REDIS_URL=... \
    python scripts/test_phase1.py
"""

from __future__ import annotations

import asyncio
import os
import sys
import uuid

# Add API package to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps", "api", "src"))

os.environ.setdefault("MOCK_LLM", "true")


async def main() -> int:
    from ava_api.db import CanvasModel, RunModel, get_session_factory, init_tables
    from ava_api.executor.pipeline import run_pipeline
    from ava_api.schemas import CanvasBlock, CanvasEdge, CanvasGraph
    from ava_api.services.outputs import get_block_output
    from ava_api.validation import validate_canvas_graph

    await init_tables()

    graph = CanvasGraph(
        blocks=[
            CanvasBlock(
                id="web-1",
                type="web",
                position={"x": 0, "y": 0},
                data={
                    "title": "Web",
                    "config": {"url": "https://example.com"},
                    "prompt": "https://example.com",
                },
                connections={"inputs": [], "outputs": ["prompt-1"]},
            ),
            CanvasBlock(
                id="prompt-1",
                type="prompt",
                position={"x": 200, "y": 0},
                data={
                    "title": "Prompt",
                    "prompt": "Summarize upstream content.",
                },
                connections={"inputs": ["web-1"], "outputs": ["note-1"]},
            ),
            CanvasBlock(
                id="note-1",
                type="note",
                position={"x": 400, "y": 0},
                data={"title": "Note", "prompt": "Final output"},
                connections={"inputs": ["prompt-1"], "outputs": []},
            ),
        ],
        edges=[
            CanvasEdge(id="e1", source="web-1", target="prompt-1"),
            CanvasEdge(id="e2", source="prompt-1", target="note-1"),
        ],
    )
    validate_canvas_graph(graph)

    factory = get_session_factory()
    async with factory() as session:
        canvas = CanvasModel(name="phase1-test", graph=graph.model_dump())
        session.add(canvas)
        await session.flush()
        run = RunModel(canvas_id=canvas.id, thread_id=str(uuid.uuid4()), status="pending")
        session.add(run)
        await session.commit()
        run_id = run.id
        canvas_id = canvas.id
        thread_id = run.thread_id

    print(f"Run {run_id} thread {thread_id}")

    final = await run_pipeline(
        run_id=run_id,
        canvas_id=canvas_id,
        canvas_graph=graph,
        thread_id=thread_id,
        resume=False,
    )
    assert not final.get("error"), final.get("error")
    print("PASS: pipeline complete")

    async with factory() as session:
        web_out = await get_block_output(session, run_id, "web-1")
        prompt_out = await get_block_output(session, run_id, "prompt-1")
        note_out = await get_block_output(session, run_id, "note-1")

    assert web_out and "MOCK WEB" in (web_out.content or ""), "web scrape failed"
    print("PASS: web block output")

    assert prompt_out and "MOCK ANALYSIS" in (prompt_out.content or ""), "prompt missing context"
    print("PASS: prompt received upstream context")

    assert note_out and len(note_out.content or "") > 10, "note empty"
    print("PASS: note final output")

    # Resume smoke test — should skip completed blocks
    final2 = await run_pipeline(
        run_id=run_id,
        canvas_id=canvas_id,
        canvas_graph=graph,
        thread_id=thread_id,
        resume=True,
    )
    assert not final2.get("error"), final2.get("error")
    print("PASS: checkpoint resume")

    print("\n=== Phase 1 go/no-go: ALL CHECKS PASSED ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
