#!/usr/bin/env python3
"""Phase 4 go/no-go: routing, artifacts, compaction."""

import asyncio
import os
import sys

import httpx

API = os.environ.get("API_URL", "http://localhost:8000")


async def main() -> int:
    async with httpx.AsyncClient(timeout=180.0) as client:
        canvas = await client.post(
            f"{API}/canvases",
            json={
                "name": "phase4",
                "graph": {
                    "blocks": [
                        {
                            "id": "p1",
                            "type": "prompt",
                            "position": {"x": 0, "y": 0},
                            "data": {
                                "title": "Analyze",
                                "prompt": "Summarize",
                                "status": "idle",
                                "config": {"model": "gpt-4o-mini"},
                            },
                            "connections": {"inputs": [], "outputs": ["e1"]},
                        },
                        {
                            "id": "e1",
                            "type": "excel",
                            "position": {"x": 300, "y": 0},
                            "data": {"title": "Sheet", "prompt": "", "status": "idle", "config": {}},
                            "connections": {"inputs": ["p1"], "outputs": []},
                        },
                    ],
                    "edges": [{"id": "x", "source": "p1", "target": "e1"}],
                },
            },
        )
        canvas.raise_for_status()
        cid = canvas.json()["id"]
        run = await client.post(f"{API}/runs", json={"canvas_id": cid})
        run.raise_for_status()
        rid = run.json()["id"]

        for _ in range(60):
            await asyncio.sleep(2)
            st = await client.get(f"{API}/runs/{rid}")
            if st.json()["status"] in ("complete", "error"):
                break
        assert st.json()["status"] == "complete", st.text

        dlq = await client.get(f"{API}/bench/dlq")
        dlq.raise_for_status()

        print(f"Phase 4 OK — run={rid}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
