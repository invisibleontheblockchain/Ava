"""L3 block executors — Phase 1 block types."""

from __future__ import annotations

import json
import uuid
from typing import Any

import httpx
from bs4 import BeautifulSoup
from ava_api.artifacts.pptx import generate_pptx_from_text
from ava_api.platform.routing import route_completion
from ava_api.config import get_settings
from ava_api.schemas import CanvasBlock


async def scrape_url(url: str, max_chars: int = 12000) -> str:
    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        response = await client.get(
            url,
            headers={"User-Agent": "Ava/0.1 (research agent)"},
        )
        response.raise_for_status()
    soup = BeautifulSoup(response.text, "lxml")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    text = soup.get_text(separator="\n", strip=True)
    return text[:max_chars]


async def mock_llm_response(system: str, user: str) -> str:
    """Deterministic mock for Phase 1 E2E without API keys."""
    if "upstream" in system.lower() or "context" in system.lower():
        return (
            "MOCK ANALYSIS:\n"
            "- Upstream web content was received in the context bundle.\n"
            "- Key themes extracted for the Note block.\n"
            "- Phase 1 pipeline validated end-to-end."
        )
    return f"MOCK OUTPUT for: {user[:120]}"


async def run_llm(
    *,
    system: str,
    user: str,
    model: str | None = None,
    temperature: float = 0.3,
    stream_callback=None,
    task_type: str = "general",
) -> tuple[str, int]:
    text, _model, tokens = await route_completion(
        system=system,
        user=user,
        model=model,
        temperature=temperature,
        stream_callback=stream_callback,
        task_type=task_type,
    )
    return text, tokens


def build_system_prompt(block: CanvasBlock, context: dict[str, dict]) -> str:
    context_str = json.dumps(context, indent=2) if context else "{}"
    data = block.data
    title = data.get("title", block.id)
    prompt = data.get("prompt", "")
    config = data.get("config") or {}
    extra_system = config.get("system_prompt") or ""
    return f"""You are executing canvas block: {title}
Block type: {block.type}

Upstream context from connected blocks:
{context_str}

{extra_system}

Your task:
{prompt}
"""


async def _maybe_export_docx(
    block: CanvasBlock,
    content: str,
    run_id: uuid.UUID | None,
    title: str,
) -> str | None:
    if run_id is None:
        return None
    from ava_api.artifacts.docx import generate_docx_from_text
    from ava_api.services.artifacts import artifacts_root

    file_id = generate_docx_from_text(
        title=title,
        body=content,
        output_dir=artifacts_root() / str(run_id),
    )
    return str(file_id)


async def _maybe_export_pptx(
    block: CanvasBlock,
    content: str,
    run_id: uuid.UUID | None,
) -> str | None:
    config = block.data.get("config") or {}
    if not config.get("export_pptx"):
        return None
    if run_id is None:
        return None
    from ava_api.services.artifacts import artifacts_root

    root = artifacts_root()
    title = block.data.get("title", block.id)
    file_id = generate_pptx_from_text(title=title, body=content, output_dir=root / str(run_id))
    return str(file_id)


async def execute_block(
    block: CanvasBlock,
    context: dict[str, dict],
    *,
    run_id: uuid.UUID | None = None,
    stream_callback=None,
) -> dict[str, Any]:
    data = block.data
    config = data.get("config") or {}
    title = data.get("title", block.id)
    settings = get_settings()

    if block.type == "web":
        url = config.get("url") or data.get("prompt", "")
        if settings.mock_llm:
            content = (
                f"MOCK WEB SCRAPE from {url}\n\n"
                "Sample page text for Phase 1 testing. "
                "This simulates scraped HTML converted to plain text."
            )
        else:
            if not url.startswith("http"):
                raise ValueError(f"Web block requires a valid URL, got: {url!r}")
            content = await scrape_url(url)
        return {"type": "text", "content": content, "title": title}

    if block.type == "prompt":
        system = build_system_prompt(block, context)
        user = data.get("prompt", "Process the upstream context.")
        text, tokens = await run_llm(
            system=system,
            user=user,
            model=config.get("model"),
            temperature=config.get("temperature") or 0.3,
            stream_callback=stream_callback,
        )
        return {"type": "text", "content": text, "title": title, "token_count": tokens}

    if block.type == "note":
        if context:
            combined = "\n\n".join(
                f"## {v.get('title', k)}\n{v.get('content', '')}" for k, v in context.items()
            )
            content = combined
        else:
            content = data.get("prompt", "")
        file_artifact_id = await _maybe_export_pptx(block, content, run_id)
        result: dict[str, Any] = {"type": "text", "content": content, "title": title}
        if file_artifact_id:
            result["artifact_id"] = file_artifact_id
        return result

    if block.type == "list":
        items = []
        if context:
            for v in context.values():
                lines = [ln.strip() for ln in (v.get("content") or "").splitlines() if ln.strip()]
                items.extend(lines[:20])
        content = json.dumps({"items": items[:50]}, indent=2)
        return {"type": "text", "content": content, "title": title}

    if block.type == "table":
        rows = []
        if context:
            for v in context.values():
                rows.append({"source": v.get("title", ""), "snippet": (v.get("content") or "")[:500]})
        content = json.dumps({"rows": rows}, indent=2)
        return {"type": "table", "content": content, "title": title}

    if block.type == "report":
        system = build_system_prompt(block, context)
        user = data.get("prompt", "Write a structured report.")
        text, tokens = await run_llm(system=system, user=user, stream_callback=stream_callback)
        artifact_id = await _maybe_export_docx(block, text, run_id, title)
        result = {"type": "text", "content": text, "title": title, "token_count": tokens}
        if artifact_id:
            result["artifact_id"] = artifact_id
        return result

    if block.type == "memo":
        system = build_system_prompt(block, context)
        user = data.get("prompt", "Write an internal memo.")
        text, _ = await run_llm(system=system, user=user)
        return {"type": "text", "content": text, "title": title}

    if block.type == "file":
        path = config.get("file_path") or data.get("prompt", "")
        if settings.mock_llm:
            content = f"MOCK FILE INGEST: {path}\n\nSimulated file text content."
        else:
            content = f"File block requires configured storage — path: {path}"
        return {"type": "text", "content": content, "title": title}

    if block.type == "youtube":
        url = config.get("youtube_url") or config.get("url") or data.get("prompt", "")
        if settings.mock_llm:
            content = f"MOCK YOUTUBE TRANSCRIPT from {url}\n\nSample transcript lines for testing."
        else:
            content = f"YouTube ingestion not fully wired — URL: {url}"
        return {"type": "text", "content": content, "title": title}

    if block.type == "image":
        prompt = data.get("prompt", "Generate an image description.")
        from ava_api.artifacts.replicate import generate_image
        from ava_api.services.artifacts import artifacts_root

        if run_id:
            file_id = await generate_image(
                prompt=prompt,
                output_dir=artifacts_root() / str(run_id),
            )
            return {
                "type": "image_ref",
                "content": prompt,
                "title": title,
                "artifact_id": str(file_id),
            }
        return {"type": "image_ref", "content": f"MOCK IMAGE: {prompt}", "title": title}

    if block.type == "excel":
        rows = []
        if context:
            for v in context.values():
                rows.append({"source": v.get("title", ""), "value": (v.get("content") or "")[:200]})
        if not rows:
            rows = [{"metric": "sample", "value": "1"}]
        from ava_api.artifacts.excel import generate_xlsx_from_rows
        from ava_api.services.artifacts import artifacts_root

        if run_id:
            file_id = generate_xlsx_from_rows(
                title=title,
                rows=rows,
                output_dir=artifacts_root() / str(run_id),
            )
            return {"type": "file_ref", "content": json.dumps(rows), "title": title, "artifact_id": str(file_id)}
        return {"type": "table", "content": json.dumps({"rows": rows}), "title": title}

    if block.type == "presentation":
        system = build_system_prompt(block, context)
        text, _ = await run_llm(system=system, user=data.get("prompt", "Slide deck outline."), task_type="writing")
        file_artifact_id = await _maybe_export_pptx(block, text, run_id)
        result = {"type": "text", "content": text, "title": title}
        if file_artifact_id:
            result["artifact_id"] = file_artifact_id
        return result

    if block.type == "dashboard":
        metrics = {"blocks": len(context), "status": "ok"}
        if context:
            for k, v in list(context.items())[:5]:
                metrics[k] = len(v.get("content") or "")
        from ava_api.artifacts.dashboard import generate_dashboard_html
        from ava_api.services.artifacts import artifacts_root

        if run_id:
            file_id = generate_dashboard_html(
                title=title,
                metrics=metrics,
                output_dir=artifacts_root() / str(run_id),
            )
            return {"type": "file_ref", "content": json.dumps(metrics), "title": title, "artifact_id": str(file_id)}
        return {"type": "text", "content": json.dumps(metrics), "title": title}

    if block.type == "app":
        system = build_system_prompt(block, context)
        html_body, _ = await run_llm(
            system=system + "\nReturn safe HTML fragment only.",
            user=data.get("prompt", "Build a simple dashboard UI."),
            task_type="code",
        )
        from ava_api.artifacts.app_html import generate_app_html
        from ava_api.services.artifacts import artifacts_root

        if run_id:
            file_id = generate_app_html(title=title, body_html=html_body, output_dir=artifacts_root() / str(run_id))
            return {"type": "file_ref", "content": html_body[:2000], "title": title, "artifact_id": str(file_id)}
        return {"type": "text", "content": html_body, "title": title}

    if block.type == "code":
        system = "You are a code block. Return concise runnable Python or pseudocode."
        text, _ = await run_llm(system=system, user=data.get("prompt", "print('hello')"), task_type="code")
        if settings.mock_llm:
            exec_result = "MOCK: code validated (sandbox disabled in mock mode)"
        else:
            exec_result = "Sandbox execution: preview only in OSS build"
        return {"type": "text", "content": f"{text}\n\n# {exec_result}", "title": title}

    if block.type == "connector":
        from ava_api.db import get_session_factory
        from ava_api.platform.connectors import connector_fetch

        connector_id = config.get("connector_id") or "google_drive"
        resource = config.get("resource") or data.get("prompt", "sample-doc")
        async with get_session_factory()() as session:
            content = await connector_fetch(
                session,
                user_id="default",
                connector_id=connector_id,
                resource=resource,
            )
        return {"type": "text", "content": content, "title": title}

    if block.type == "human_gate":
        approved = config.get("approved", False)
        if not approved:
            return {
                "type": "text",
                "content": f"AWAITING HUMAN APPROVAL — POST /runs/{run_id}/approve?block_id={block.id}",
                "title": title,
                "meta": {"paused": True},
            }
        combined = "\n".join(v.get("content", "") for v in context.values()) if context else data.get("prompt", "")
        return {"type": "text", "content": combined or "Approved.", "title": title}

    raise ValueError(f"Unsupported block type: {block.type}")
