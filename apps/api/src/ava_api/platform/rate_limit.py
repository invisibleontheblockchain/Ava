"""LiteLLM provider rate limiting (Document 2 §4 / stack table)."""

from __future__ import annotations

import asyncio
import time
from collections import defaultdict

from ava_api.config import get_settings

_buckets: dict[str, list[float]] = defaultdict(list)
_lock = asyncio.Lock()


async def acquire_rate_limit(provider_key: str = "default") -> None:
    settings = get_settings()
    limit = settings.llm_requests_per_minute
    window = 60.0
    async with _lock:
        now = time.time()
        _buckets[provider_key] = [t for t in _buckets[provider_key] if now - t < window]
        if len(_buckets[provider_key]) >= limit:
            sleep_for = window - (now - _buckets[provider_key][0]) + 0.05
            if sleep_for > 0:
                await asyncio.sleep(sleep_for)
        _buckets[provider_key].append(time.time())
