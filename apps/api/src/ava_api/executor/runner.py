"""DAG execution engine — Kahn batches + asyncio.gather (Document 2 §2)."""

from __future__ import annotations

import asyncio
import uuid
from typing import Any, Callable, Awaitable

from ava_api.db import get_session_factory
from ava_api.executor.blocks import execute_block
from ava_api.executor.dag import block_by_id, build_digraph, get_parallel_batches, upstream_ids
from ava_api.schemas import CanvasGraph
from ava_api.services.events import publish_event
from ava_api.services.outputs import build_context_bundle, get_block_output, persist_block_output

StreamCallback = Callable[[str], Awaitable[None]]


async def _is_block_complete(run_id: uuid.UUID, block_id: str) -> bool:
    async with get_session_factory()() as session:
        row = await get_block_output(session, run_id, block_id)
        return row is not None


async def execute_single_block(
    *,
    run_id: uuid.UUID,
    block_id: str,
    graph: CanvasGraph,
    stream_callback: StreamCallback | None = None,
) -> dict[str, Any]:
    blocks = block_by_id(graph)
    block = blocks[block_id]
    run_id_str = str(run_id)

    await publish_event(
        run_id_str,
        {"type": "block_status", "block_id": block_id, "status": "running"},
    )

    async def token_cb(token: str) -> None:
        if stream_callback:
            await stream_callback(token)
        await publish_event(
            run_id_str,
            {"type": "token", "block_id": block_id, "token": token},
        )

    try:
        async with get_session_factory()() as session:
            upstream = upstream_ids(block, graph)
            context = await build_context_bundle(session, run_id, upstream)

            use_stream = block.type == "prompt"
            result = await execute_block(
                block,
                context,
                run_id=run_id,
                stream_callback=token_cb if use_stream else None,
            )

            meta = {
                "token_count": result.get("token_count"),
                "artifact_id": result.get("artifact_id"),
            }
            if result.get("artifact_id"):
                meta["file_ext"] = {
                    "file_ref": ".bin",
                    "image_ref": ".png",
                }.get(result.get("type", "text"), ".bin")

            output_ref = await persist_block_output(
                session,
                run_id=run_id,
                block_id=block_id,
                title=result.get("title", block_id),
                output_type=result.get("type", "text"),
                content=result.get("content"),
                meta=meta,
            )
            from ava_api.platform.observability import audit_log

            await audit_log(
                session,
                tenant_id="default",
                agent_id=f"l3:{block.type}",
                action="block_complete",
                target=block_id,
                meta={"run_id": str(run_id), "output_ref": str(output_ref)},
            )
            await session.commit()

        ref_str = str(output_ref)
        preview = (result.get("content") or "")[:2000]
        await publish_event(
            run_id_str,
            {
                "type": "block_complete",
                "block_id": block_id,
                "status": "complete",
                "output": {
                    "type": result.get("type", "text"),
                    "content": preview,
                    "artifact_id": ref_str,
                    "file_artifact_id": result.get("artifact_id"),
                },
            },
        )
        return {
            "block_id": block_id,
            "output_ref": ref_str,
            "status": "complete",
            "error": None,
        }
    except Exception as exc:
        await publish_event(
            run_id_str,
            {
                "type": "block_status",
                "block_id": block_id,
                "status": "error",
                "error": str(exc),
            },
        )
        return {"block_id": block_id, "output_ref": None, "status": "error", "error": str(exc)}


class DAGExecutor:
    """Topological parallel batches — blueprint DAGExecutor pattern."""

    def __init__(self, graph: CanvasGraph, run_id: uuid.UUID):
        self.graph = graph
        self.run_id = run_id
        self.digraph = build_digraph(graph)
        self.batches = get_parallel_batches(self.digraph)

    async def run_batch(self, batch_index: int) -> dict[str, Any]:
        """Execute a single parallel batch by index."""
        if batch_index >= len(self.batches):
            return {
                "output_refs": {},
                "block_status": {},
                "completed_blocks": [],
                "batch_index": batch_index,
                "error": None,
            }
        batch = self.batches[batch_index]
        output_refs: dict[str, str] = {}
        block_status: dict[str, str] = {}
        completed: list[str] = []

        to_run: list[str] = []
        for block_id in batch:
            if await _is_block_complete(self.run_id, block_id):
                async with get_session_factory()() as session:
                    row = await get_block_output(session, self.run_id, block_id)
                if row:
                    output_refs[block_id] = str(row.id)
                    block_status[block_id] = "complete"
                    completed.append(block_id)
                continue
            to_run.append(block_id)

        if to_run:
            results = await asyncio.gather(
                *[
                    execute_single_block(
                        run_id=self.run_id,
                        block_id=bid,
                        graph=self.graph,
                    )
                    for bid in to_run
                ]
            )
            for r in results:
                bid = r["block_id"]
                block_status[bid] = r["status"]
                if r["status"] == "complete" and r["output_ref"]:
                    output_refs[bid] = r["output_ref"]
                    completed.append(bid)
                elif r["error"]:
                    return {
                        "output_refs": output_refs,
                        "block_status": block_status,
                        "completed_blocks": completed,
                        "batch_index": batch_index,
                        "error": r["error"],
                    }

        return {
            "output_refs": output_refs,
            "block_status": block_status,
            "completed_blocks": completed,
            "batch_index": batch_index + 1,
            "error": None,
        }

    async def run(
        self,
        *,
        start_batch: int = 0,
        skip_completed: bool = False,
    ) -> dict[str, Any]:
        output_refs: dict[str, str] = {}
        block_status: dict[str, str] = {}
        completed: list[str] = []
        error: str | None = None

        for batch_idx in range(start_batch, len(self.batches)):
            batch_result = await self.run_batch(batch_idx)
            output_refs.update(batch_result.get("output_refs") or {})
            block_status.update(batch_result.get("block_status") or {})
            completed.extend(batch_result.get("completed_blocks") or [])
            if batch_result.get("error"):
                return {
                    "output_refs": output_refs,
                    "block_status": block_status,
                    "completed_blocks": completed,
                    "batch_index": batch_idx,
                    "error": batch_result["error"],
                }

        return {
            "output_refs": output_refs,
            "block_status": block_status,
            "completed_blocks": completed,
            "batch_index": len(self.batches),
            "error": None,
        }
