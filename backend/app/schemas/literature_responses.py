from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ArtifactInfo(BaseModel):
    artifact_id: str
    filename: str
    download_url: str
    mime_type: str
    size_bytes: int


class ConvertResponse(BaseModel):
    job_id: str
    source_type: str
    conversion: str
    records: int
    preview: list[dict[str, Any]]
    download_name: str
    artifact: ArtifactInfo
    download_url: str


class DeduplicateResponse(BaseModel):
    job_id: str
    preview: list[dict[str, Any]]
    master_preview: list[dict[str, Any]]
    review_preview: list[dict[str, Any]]
    report: dict[str, Any]
    artifacts: dict[str, ArtifactInfo]
    finalized: bool


__all__ = ["ArtifactInfo", "ConvertResponse", "DeduplicateResponse"]
