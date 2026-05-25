"""Sandboxed HTML app artifacts (Phase 4/5)."""

from __future__ import annotations

import uuid
from pathlib import Path

import bleach


def sanitize_html(raw: str) -> str:
    allowed_tags = [
        "div",
        "p",
        "h1",
        "h2",
        "h3",
        "ul",
        "ol",
        "li",
        "table",
        "tr",
        "td",
        "th",
        "span",
        "strong",
        "em",
        "a",
    ]
    return bleach.clean(raw, tags=allowed_tags, strip=True)


def generate_app_html(
    *,
    title: str,
    body_html: str,
    output_dir: Path,
) -> uuid.UUID:
    output_dir.mkdir(parents=True, exist_ok=True)
    file_id = uuid.uuid4()
    safe = sanitize_html(body_html)
    csp = "default-src 'none'; style-src 'unsafe-inline'; img-src data:;"
    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>{title}</title>
<meta http-equiv="Content-Security-Policy" content="{csp}">
<style>body{{font-family:system-ui;margin:2rem;}}</style></head>
<body>{safe}</body></html>"""
    (output_dir / f"{file_id}.html").write_text(html, encoding="utf-8")
    return file_id
