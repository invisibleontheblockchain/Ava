"""LiteLLM multi-model routing + confidence ensemble (Phase 4)."""

from __future__ import annotations

import asyncio
import json
import re

from litellm import acompletion

from ava_api.config import get_settings
from ava_api.platform.rate_limit import acquire_rate_limit


def _estimate_confidence(text: str) -> float:
    if not text or len(text) < 40:
        return 0.3
    if "uncertain" in text.lower() or "i don't know" in text.lower():
        return 0.35
    return 0.85


async def route_completion(
    *,
    system: str,
    user: str,
    model: str | None = None,
    temperature: float = 0.3,
    stream_callback=None,
    task_type: str = "general",
) -> tuple[str, str, int]:
    settings = get_settings()
    if settings.mock_llm:
        from ava_api.executor.blocks import mock_llm_response

        text = await mock_llm_response(system, user)
        if stream_callback:
            for w in text.split():
                await stream_callback(w + " ")
        return text, "mock", len(text.split())

    primary = model or _pick_model(task_type)
    await acquire_rate_limit(primary.split("/")[0] if "/" in primary else primary)
    text, tokens = await _single_completion(
        system, user, primary, temperature, stream_callback
    )
    confidence = _estimate_confidence(text)
    if confidence < settings.ensemble_confidence_threshold and len(settings.fallback_model_list) > 1:
        alt_models = [m for m in settings.fallback_model_list if m != primary][:2]
        texts = await asyncio.gather(
            *[
                _single_completion(system, user, m, temperature, None)
                for m in alt_models
            ]
        )
        candidates = [text] + [t[0] for t in texts]
        text = _synthesize_ensemble(candidates)
        return text, f"ensemble:{primary}", tokens
    return text, primary, tokens


def _pick_model(task_type: str) -> str:
    settings = get_settings()
    mapping = {
        "research": settings.fallback_model_list[0] if settings.fallback_model_list else settings.litellm_model,
        "analysis": settings.litellm_model,
        "writing": settings.litellm_model,
        "code": "gpt-4o",
    }
    return mapping.get(task_type, settings.litellm_model)


async def _single_completion(
    system: str,
    user: str,
    model: str,
    temperature: float,
    stream_callback,
) -> tuple[str, int]:
    messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    if stream_callback:
        response = await acompletion(model=model, messages=messages, temperature=temperature, stream=True)
        parts: list[str] = []
        async for chunk in response:
            delta = chunk.choices[0].delta.content or ""
            if delta:
                parts.append(delta)
                await stream_callback(delta)
        text = "".join(parts)
        return text, len(text.split())
    response = await acompletion(model=model, messages=messages, temperature=temperature)
    text = response.choices[0].message.content or ""
    return text, len(text.split())


def _synthesize_ensemble(candidates: list[str]) -> str:
    return (
        "ENSEMBLE SYNTHESIS (multi-model):\n\n"
        + "\n\n---\n\n".join(c[:1500] for c in candidates[:3])
    )
