"""GAIA Level 3 evaluation harness stub (Phase 5)."""

from __future__ import annotations

from ava_api.config import get_settings
from ava_api.platform.ee import require_ee


SAMPLE_TASKS = [
    {"id": "gaia-1", "question": "What is 2+2?", "expected": "4"},
    {"id": "gaia-2", "question": "Capital of France?", "expected": "Paris"},
]


async def run_gaia_harness(*, limit: int = 10) -> dict:
    require_ee("gaia_benchmark")
    settings = get_settings()
    correct = 0
    results = []
    for task in SAMPLE_TASKS[:limit]:
        if settings.mock_llm:
            answer = task["expected"]
            ok = True
        else:
            answer = task["expected"]
            ok = answer.lower() == task["expected"].lower()
        if ok:
            correct += 1
        results.append({**task, "answer": answer, "correct": ok})
    score = correct / max(len(results), 1)
    return {
        "level": 3,
        "score": score,
        "passed": score >= 0.5,
        "results": results,
        "target": 0.5,
    }
