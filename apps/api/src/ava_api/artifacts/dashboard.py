"""Dashboard artifact — Streamlit-style static HTML embed (Phase 4/5)."""

from __future__ import annotations

import json
import uuid
from pathlib import Path


def generate_dashboard_html(
    *,
    title: str,
    metrics: dict,
    output_dir: Path,
) -> uuid.UUID:
    output_dir.mkdir(parents=True, exist_ok=True)
    file_id = uuid.uuid4()
    data = json.dumps(metrics)
    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>{title}</title>
<script src="https://cdn.jsdelivr.net/npm/@observablehq/plot@0.6"></script>
<style>body{{font-family:system-ui;margin:2rem;}} .metric{{display:inline-block;margin:1rem;padding:1rem;border:1px solid #ccc;border-radius:8px;}}</style>
</head><body><h1>{title}</h1>
<div id="metrics"></div>
<script>
const metrics = {data};
const el = document.getElementById('metrics');
Object.entries(metrics).forEach(([k,v]) => {{
  const d = document.createElement('div');
  d.className = 'metric';
  d.innerHTML = '<strong>'+k+'</strong><br>'+v;
  el.appendChild(d);
}});
</script></body></html>"""
    (output_dir / f"{file_id}.html").write_text(html, encoding="utf-8")
    return file_id
