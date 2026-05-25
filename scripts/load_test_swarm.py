#!/usr/bin/env python3
"""10 concurrent swarm runs load test (Document 2 Phase 5 go/no-go)."""

import asyncio
import os
import sys

import httpx

API = os.environ.get("API_URL", "http://localhost:8000")
CONCURRENCY = int(os.environ.get("CONCURRENCY", "10"))


async def one_swarm(client: httpx.AsyncClient, i: int) -> bool:
    r = await client.post(f"{API}/swarm/runs", json={"use_demo_plan": True})
    if r.status_code >= 400:
        print(f"[{i}] start failed: {r.text}")
        return False
    run_id = r.json()["id"]
    for _ in range(90):
        await asyncio.sleep(2)
        st = await client.get(f"{API}/runs/{run_id}")
        if st.json().get("status") in ("complete", "error"):
            ok = st.json().get("status") == "complete"
            print(f"[{i}] run {run_id} -> {st.json().get('status')}")
            return ok
    print(f"[{i}] timeout {run_id}")
    return False


async def main() -> int:
    async with httpx.AsyncClient(timeout=300.0) as client:
        results = await asyncio.gather(
            *[one_swarm(client, i) for i in range(CONCURRENCY)]
        )
    passed = sum(results)
    print(f"Load test: {passed}/{CONCURRENCY} completed")
    return 0 if passed >= CONCURRENCY * 0.8 else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
