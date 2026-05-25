#!/usr/bin/env python3
"""Phase 5 go/no-go: 17 blocks, marketplace, GAIA stub."""

import asyncio
import os
import sys

import httpx

API = os.environ.get("API_URL", "http://localhost:8000")


async def main() -> int:
    async with httpx.AsyncClient(timeout=60.0) as client:
        h = await client.get(f"{API}/health")
        h.raise_for_status()
        assert h.json()["phase"] == 5

        market = await client.get(f"{API}/marketplace/connectors")
        market.raise_for_status()
        assert len(market.json()["connectors"]) >= 3

        gaia = await client.post(f"{API}/bench/gaia?limit=2")
        if gaia.status_code == 402:
            print("GAIA skipped (EE license not set) — OK for OSS")
        else:
            gaia.raise_for_status()
            assert "score" in gaia.json()

        login = await client.post(
            f"{API}/auth/login",
            json={"email": "dev@ava.local"},
        )
        login.raise_for_status()
        assert login.json().get("access_token")

        print("Phase 5 API checks OK")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
