import uuid
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ava_api.db import BlockOutputModel, FileArtifactModel, get_db
from ava_api.services.artifacts import artifacts_root

router = APIRouter(prefix="/runs", tags=["outputs"])


@router.get("/{run_id}/blocks/{block_id}/output")
async def get_block_output(
    run_id: UUID,
    block_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(BlockOutputModel)
        .where(BlockOutputModel.run_id == run_id)
        .where(BlockOutputModel.block_id == block_id)
        .order_by(BlockOutputModel.created_at.desc())
        .limit(1)
    )
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(404, "Block output not found")
    return {
        "block_id": block_id,
        "output_ref": str(row.id),
        "title": row.title,
        "output_type": row.output_type,
        "content": row.content,
        "meta": row.meta,
        "artifact_url": row.artifact_url,
    }


@router.get("/{run_id}/artifacts/{artifact_id}")
async def download_artifact(
    run_id: UUID,
    artifact_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    root = artifacts_root() / str(run_id)
    all_out = await db.execute(
        select(BlockOutputModel).where(BlockOutputModel.run_id == run_id)
    )
    out_row = None
    for row in all_out.scalars():
        if str((row.meta or {}).get("artifact_id")) == str(artifact_id):
            out_row = row
            break
    if out_row and out_row.artifact_url and out_row.artifact_url.startswith("http"):
        from fastapi.responses import RedirectResponse

        return RedirectResponse(out_row.artifact_url)

    for ext, media in (
        (".pptx", "application/vnd.openxmlformats-officedocument.presentationml.presentation"),
        (".docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
        (".xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        (".html", "text/html"),
        (".png", "image/png"),
    ):
        path = root / f"{artifact_id}{ext}"
        if path.is_file():
            return FileResponse(path, media_type=media, filename=f"ava-{artifact_id}{ext}")

    result = await db.execute(
        select(FileArtifactModel)
        .where(FileArtifactModel.id == artifact_id)
        .where(FileArtifactModel.run_id == run_id)
    )
    row = result.scalar_one_or_none()
    if row and Path(row.storage_path).is_file():
        return FileResponse(row.storage_path, media_type=row.media_type, filename=row.filename)

    raise HTTPException(404, "Artifact not found")
