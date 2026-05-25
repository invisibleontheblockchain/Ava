import uuid
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from ava_api.config import get_settings
from ava_api.db import FileArtifactModel


async def register_file_artifact(
    session: AsyncSession,
    *,
    run_id: uuid.UUID,
    block_id: str,
    filename: str,
    media_type: str,
    storage_path: Path,
) -> uuid.UUID:
    row = FileArtifactModel(
        run_id=run_id,
        block_id=block_id,
        filename=filename,
        media_type=media_type,
        storage_path=str(storage_path),
    )
    session.add(row)
    await session.flush()
    return row.id


def artifacts_root() -> Path:
    return Path(get_settings().artifacts_dir).resolve()
