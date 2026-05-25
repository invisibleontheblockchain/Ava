import json
from typing import Any

import redis.asyncio as redis

from ava_api.config import get_settings

CHANNEL_PREFIX = "ava:run:"


def channel_for_run(run_id: str) -> str:
    return f"{CHANNEL_PREFIX}{run_id}"


async def get_redis() -> redis.Redis:
    return redis.from_url(get_settings().redis_url, decode_responses=True)


async def publish_event(run_id: str, event: dict[str, Any]) -> None:
    client = await get_redis()
    try:
        await client.publish(channel_for_run(run_id), json.dumps(event))
    finally:
        await client.aclose()


async def subscribe_events(run_id: str):
    """Async generator yielding parsed SSE event dicts."""
    client = await get_redis()
    pubsub = client.pubsub()
    await pubsub.subscribe(channel_for_run(run_id))
    try:
        async for message in pubsub.listen():
            if message["type"] != "message":
                continue
            yield json.loads(message["data"])
    finally:
        await pubsub.unsubscribe(channel_for_run(run_id))
        await pubsub.aclose()
        await client.aclose()
