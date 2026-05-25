"""Artifact storage — local filesystem or S3-compatible (Phase 4)."""

from __future__ import annotations

import uuid
from pathlib import Path

from ava_api.config import get_settings


def artifact_path(run_id: uuid.UUID, artifact_id: uuid.UUID, ext: str) -> Path:
    root = Path(get_settings().artifacts_dir) / str(run_id)
    root.mkdir(parents=True, exist_ok=True)
    return root / f"{artifact_id}{ext}"


def presigned_url(run_id: uuid.UUID, artifact_id: uuid.UUID, ext: str) -> str:
    settings = get_settings()
    if settings.storage_backend == "s3" and settings.s3_endpoint:
        return f"{settings.s3_endpoint}/{settings.s3_bucket}/{run_id}/{artifact_id}{ext}"
    return f"/runs/{run_id}/artifacts/{artifact_id}"
