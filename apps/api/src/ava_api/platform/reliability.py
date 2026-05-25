"""ARQ DLQ + circuit breaker (Phase 4)."""

from __future__ import annotations

import asyncio
import time
from collections import defaultdict


_dlq: list[dict] = []
_failures: dict[str, list[float]] = defaultdict(list)
_open_until: dict[str, float] = {}


def record_failure(key: str, error: str, payload: dict) -> None:
    now = time.time()
    _failures[key].append(now)
    _failures[key] = [t for t in _failures[key] if now - t < 60]
    if len(_failures[key]) >= 5:
        _open_until[key] = now + 30
    _dlq.append({"key": key, "error": error, "payload": payload, "ts": now})


def circuit_open(key: str) -> bool:
    return time.time() < _open_until.get(key, 0)


def get_dlq() -> list[dict]:
    return list(_dlq[-100:])


async def retry_with_backoff(fn, *, key: str, max_attempts: int = 3):
    if circuit_open(key):
        raise RuntimeError(f"Circuit open for {key}")
    delay = 1.0
    last_exc = None
    for attempt in range(max_attempts):
        try:
            return await fn()
        except Exception as exc:
            last_exc = exc
            record_failure(key, str(exc), {"attempt": attempt})
            if attempt < max_attempts - 1:
                await asyncio.sleep(delay)
                delay *= 2
    raise last_exc  # type: ignore
