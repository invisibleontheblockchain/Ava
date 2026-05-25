"""Image generation via Replicate API (Document 2 Phase 4)."""

from __future__ import annotations

import uuid
from pathlib import Path

import httpx

from ava_api.config import get_settings


async def generate_image(
    *,
    prompt: str,
    output_dir: Path,
) -> uuid.UUID:
    settings = get_settings()
    output_dir.mkdir(parents=True, exist_ok=True)
    file_id = uuid.uuid4()
    path = output_dir / f"{file_id}.png"

    if not settings.replicate_api_key:
        path.write_bytes(b"")
        (output_dir / f"{file_id}.txt").write_text(f"MOCK IMAGE: {prompt}", encoding="utf-8")
        return file_id

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            "https://api.replicate.com/v1/predictions",
            headers={"Authorization": f"Token {settings.replicate_api_key}"},
            json={
                "version": "stability-ai/sdxl",
                "input": {"prompt": prompt},
            },
        )
        if resp.status_code >= 400:
            path.write_text(f"Replicate error: {resp.text}", encoding="utf-8")
            return file_id
        data = resp.json()
        url = (data.get("output") or [None])[0] if isinstance(data.get("output"), list) else data.get("output")
        if url:
            img = await client.get(url)
            path.write_bytes(img.content)
    return file_id
