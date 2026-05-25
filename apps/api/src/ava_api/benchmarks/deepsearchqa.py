"""DeepSearchQA harness (Phase 5 stretch — Document 2)."""

from __future__ import annotations

SAMPLE = [
    {"id": "dsq-1", "query": "Compare revenue trends", "expected_contains": "revenue"},
    {"id": "dsq-2", "query": "Summarize regulatory risks", "expected_contains": "risk"},
]


async def run_deepsearchqa_harness(*, limit: int = 10) -> dict:
    from ava_api.config import get_settings
    from ava_api.platform.routing import route_completion

    settings = get_settings()
    results = []
    correct = 0
    for item in SAMPLE[:limit]:
        if settings.mock_llm:
            answer = f"Analysis including {item['expected_contains']} from mock search."
            ok = item["expected_contains"] in answer.lower()
        else:
            answer, _, _ = await route_completion(
                system="Answer the research query concisely.",
                user=item["query"],
                task_type="research",
            )
            ok = item["expected_contains"] in answer.lower()
        if ok:
            correct += 1
        results.append({**item, "answer": answer[:500], "correct": ok})
    score = correct / max(len(results), 1)
    return {"harness": "deepsearchqa", "score": score, "results": results}
