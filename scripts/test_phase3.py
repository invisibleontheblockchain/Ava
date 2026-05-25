#!/usr/bin/env python3
"""Phase 3 go/no-go: L1 planning + connectors."""

import asyncio
import os
import sys

import httpx

API = os.environ.get("API_URL", "http://localhost:8000")


async def main() -> int:
    async with httpx.AsyncClient(timeout=120.0) as client:
        health = await client.get(f"{API}/health")
        health.raise_for_status()
        assert health.json().get("phase") >= 3

        plan_res = await client.post(
            f"{API}/planning/sessions",
            json={"brief": "Research AI agents and write a report", "user_id": "test"},
        )
        plan_res.raise_for_status()
        data = plan_res.json()
        session_id = data["session_id"]
        assert data.get("plan")

        confirm = await client.post(
            f"{API}/planning/sessions/{session_id}/confirm",
            json={},
        )
        confirm.raise_for_status()
        run_id = confirm.json()["run_id"]

        conn = await client.get(f"{API}/connectors")
        conn.raise_for_status()
        assert len(conn.json()) >= 3

        oauth = await client.post(
            f"{API}/connectors/oauth/connect",
            json={"user_id": "test", "connector_id": "google_drive"},
        )
        oauth.raise_for_status()

        fetch = await client.post(
            f"{API}/connectors/fetch",
            json={"user_id": "test", "connector_id": "google_drive", "resource": "doc-1"},
        )
        fetch.raise_for_status()
        assert "MOCK" in fetch.json()["content"] or len(fetch.json()["content"]) > 10

        print(f"Phase 3 OK — session={session_id} run={run_id}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
