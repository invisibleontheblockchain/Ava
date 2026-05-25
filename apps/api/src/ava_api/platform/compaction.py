"""Context compaction for 80+ minute runs (Phase 4)."""

from __future__ import annotations

import json

from ava_api.platform.routing import route_completion


async def compact_context_bundle(bundle: dict[str, dict], max_chars: int = 8000) -> dict[str, dict]:
    raw = json.dumps(bundle, indent=0)
    if len(raw) <= max_chars:
        return bundle
    text, _, _ = await route_completion(
        system="Compress upstream agent context. Preserve facts, remove redundancy.",
        user=f"Compact this context to under {max_chars} characters:\n{raw[:50000]}",
        task_type="analysis",
    )
    return {"compacted": {"title": "compacted_context", "type": "text", "content": text[:max_chars]}}
