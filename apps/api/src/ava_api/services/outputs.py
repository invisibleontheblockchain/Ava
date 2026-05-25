import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ava_api.db import BlockOutputModel
from ava_api.platform.storage import presigned_url


async def persist_block_output(
    session: AsyncSession,
    *,
    run_id: uuid.UUID,
    block_id: str,
    title: str,
    output_type: str,
    content: str | None,
    meta: dict | None = None,
) -> uuid.UUID:
    artifact_id = (meta or {}).get("artifact_id")
    artifact_url = None
    if artifact_id:
        ext = (meta or {}).get("file_ext", ".bin")
        artifact_url = presigned_url(run_id, uuid.UUID(str(artifact_id)), ext)

    row = BlockOutputModel(
        run_id=run_id,
        block_id=block_id,
        title=title,
        output_type=output_type,
        content=content,
        meta=meta or {},
        artifact_url=artifact_url,
    )
    session.add(row)
    await session.flush()
    return row.id


async def get_block_output(
    session: AsyncSession, run_id: uuid.UUID, block_id: str
) -> BlockOutputModel | None:
    result = await session.execute(
        select(BlockOutputModel)
        .where(BlockOutputModel.run_id == run_id)
        .where(BlockOutputModel.block_id == block_id)
        .order_by(BlockOutputModel.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def build_context_bundle(
    session: AsyncSession,
    run_id: uuid.UUID,
    upstream_ids: list[str],
) -> dict[str, dict]:
    bundle: dict[str, dict] = {}
    for block_id in upstream_ids:
        row = await get_block_output(session, run_id, block_id)
        if row:
            bundle[block_id] = {
                "title": row.title,
                "type": row.output_type,
                "content": row.content or "",
            }
    if len(str(bundle)) > 12000:
        from ava_api.platform.compaction import compact_context_bundle

        bundle = await compact_context_bundle(bundle)
    return bundle
