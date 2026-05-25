"""Excel artifact generation (Phase 2/4/5)."""

from __future__ import annotations

import uuid
from pathlib import Path

import xlsxwriter


def generate_xlsx_from_rows(
    *,
    title: str,
    rows: list[dict],
    output_dir: Path,
) -> uuid.UUID:
    output_dir.mkdir(parents=True, exist_ok=True)
    file_id = uuid.uuid4()
    path = output_dir / f"{file_id}.xlsx"
    workbook = xlsxwriter.Workbook(str(path))
    sheet = workbook.add_worksheet(title[:31] or "Sheet1")
    headers = list(rows[0].keys()) if rows else ["col"]
    for col, h in enumerate(headers):
        sheet.write(0, col, h)
    for r_idx, row in enumerate(rows, start=1):
        for c_idx, h in enumerate(headers):
            sheet.write(r_idx, c_idx, str(row.get(h, "")))
    workbook.close()
    return file_id
