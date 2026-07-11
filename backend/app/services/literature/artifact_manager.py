from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from app.core.config import TEMP_DIR

logger = logging.getLogger(__name__)
TEMP_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class ArtifactRecord:
    """Persisted metadata for a generated file."""

    artifact_id: str
    logical_name: str
    filename: str
    path: str
    mime_type: str
    size_bytes: int
    created_at: datetime


@dataclass
class JobRecord:
    """In-memory job state for a literature processing run."""

    job_id: str
    created_at: datetime
    expires_at: datetime
    artifact_lifetime_minutes: int
    pipeline_kind: str
    master_dataset: Any = None
    exact_title_dataset: Any = None
    deduplicated_dataset: Any = None
    review_dataset: Any = None
    report: dict[str, Any] = field(default_factory=dict)
    source_counts: dict[str, int] = field(default_factory=dict)
    review_decisions: dict[str, str] = field(default_factory=dict)
    finalized: bool = False
    response: dict[str, Any] = field(default_factory=dict)
    artifacts: dict[str, ArtifactRecord] = field(default_factory=dict)


_JOBS: dict[str, JobRecord] = {}
_ARTIFACT_INDEX: dict[tuple[str, str], ArtifactRecord] = {}
_EXPIRED_JOBS: dict[str, dict[str, Any]] = {}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_job(*, pipeline_kind: str, artifact_lifetime_minutes: int) -> JobRecord:
    """Create a new in-memory job with an expiration timestamp."""
    job_id = uuid.uuid4().hex
    created_at = _now()
    expires_at = created_at + timedelta(minutes=artifact_lifetime_minutes)
    job = JobRecord(
        job_id=job_id,
        created_at=created_at,
        expires_at=expires_at,
        artifact_lifetime_minutes=artifact_lifetime_minutes,
        pipeline_kind=pipeline_kind,
    )
    _JOBS[job_id] = job
    logger.info(
        "job_created job_id=%s pipeline_kind=%s lifetime_minutes=%s expires_at=%s",
        job_id,
        pipeline_kind,
        artifact_lifetime_minutes,
        expires_at.isoformat(),
    )
    return job


def get_job(job_id: str) -> JobRecord | None:
    """Return the active job record if it still exists."""
    return _JOBS.get(job_id)


def get_expired_status(job_id: str) -> dict[str, Any] | None:
    """Return tombstone metadata for a cleanup-expired job."""
    return _EXPIRED_JOBS.get(job_id)


def _delete_file(path: str) -> None:
    file_path = Path(path)
    try:
        if file_path.exists():
            file_path.unlink()
            logger.info("artifact_file_deleted path=%s", path)
    except Exception:
        logger.exception("artifact_file_delete_failed path=%s", path)


def _remove_artifact(job: JobRecord, logical_name: str) -> None:
    record = job.artifacts.pop(logical_name, None)
    if not record:
        return
    _ARTIFACT_INDEX.pop((job.job_id, record.artifact_id), None)
    _delete_file(record.path)


def store_artifact(job_id: str, logical_name: str, filename: str, content: bytes, mime_type: str) -> ArtifactRecord:
    """Write an artifact to disk and register it in memory."""
    job = _JOBS[job_id]
    _remove_artifact(job, logical_name)

    artifact_id = uuid.uuid4().hex
    path = TEMP_DIR / f"{artifact_id}_{filename}"
    path.write_bytes(content)
    record = ArtifactRecord(
        artifact_id=artifact_id,
        logical_name=logical_name,
        filename=filename,
        path=str(path),
        mime_type=mime_type,
        size_bytes=len(content),
        created_at=_now(),
    )
    job.artifacts[logical_name] = record
    _ARTIFACT_INDEX[(job_id, artifact_id)] = record
    logger.info(
        "artifact_created job_id=%s logical_name=%s artifact_id=%s filename=%s path=%s exists=%s size_bytes=%s mime_type=%s",
        job_id,
        logical_name,
        artifact_id,
        filename,
        path,
        path.exists(),
        len(content),
        mime_type,
    )
    logger.info(
        "artifact_registered job_id=%s logical_name=%s artifact_id=%s registry_size=%s",
        job_id,
        logical_name,
        artifact_id,
        len(_ARTIFACT_INDEX),
    )
    return record


def replace_artifact(job_id: str, logical_name: str, filename: str, content: bytes, mime_type: str) -> ArtifactRecord:
    """Replace an existing artifact without touching earlier pipeline outputs."""
    return store_artifact(job_id, logical_name, filename, content, mime_type)


def get_artifact(job_id: str, artifact_id: str) -> ArtifactRecord | None:
    """Look up a registered artifact."""
    logger.info("artifact_lookup job_id=%s artifact_id=%s", job_id, artifact_id)
    return _ARTIFACT_INDEX.get((job_id, artifact_id))


def set_job_response(job_id: str, response: dict[str, Any]) -> None:
    job = _JOBS[job_id]
    job.response = response


def get_job_response(job_id: str) -> dict[str, Any] | None:
    job = _JOBS.get(job_id)
    return job.response if job else None


def set_job_state(
    job_id: str,
    *,
    master_dataset: Any | None = None,
    exact_title_dataset: Any | None = None,
    deduplicated_dataset: Any | None = None,
    review_dataset: Any | None = None,
    report: dict[str, Any] | None = None,
    source_counts: dict[str, int] | None = None,
    review_decisions: dict[str, str] | None = None,
    finalized: bool | None = None,
) -> None:
    job = _JOBS[job_id]
    if master_dataset is not None:
        job.master_dataset = master_dataset
    if exact_title_dataset is not None:
        job.exact_title_dataset = exact_title_dataset
    if deduplicated_dataset is not None:
        job.deduplicated_dataset = deduplicated_dataset
    if review_dataset is not None:
        job.review_dataset = review_dataset
    if report is not None:
        job.report = report
    if source_counts is not None:
        job.source_counts = source_counts
    if review_decisions is not None:
        job.review_decisions = review_decisions
    if finalized is not None:
        job.finalized = finalized


def cleanup_expired_artifacts() -> int:
    """Delete expired jobs, their artifacts, and tombstone them for friendly errors."""
    now = _now()
    expired_job_ids = [job_id for job_id, job in list(_JOBS.items()) if job.expires_at <= now]
    for job_id in expired_job_ids:
        job = _JOBS.pop(job_id)
        logger.info("cleanup_expired_job job_id=%s expired_at=%s", job_id, job.expires_at.isoformat())
        for record in list(job.artifacts.values()):
            _ARTIFACT_INDEX.pop((job_id, record.artifact_id), None)
            _delete_file(record.path)
        _EXPIRED_JOBS[job_id] = {"status": "expired", "expired_at": job.expires_at.isoformat()}
        job.response = {}
    return len(expired_job_ids)


def resolve_download(job_id: str, artifact_id: str) -> tuple[str, ArtifactRecord | None]:
    """Resolve a download request and classify the error state if missing."""
    job = _JOBS.get(job_id)
    if job and job.expires_at <= _now():
        cleanup_expired_artifacts()
        job = _JOBS.get(job_id)
    if not job:
        if job_id in _EXPIRED_JOBS:
            return "expired", None
        return "deleted", None

    artifact = get_artifact(job_id, artifact_id)
    if not artifact:
        return "deleted", None

    path = Path(artifact.path)
    logger.info("artifact_file_check job_id=%s artifact_id=%s path=%s exists=%s", job_id, artifact_id, path, path.exists())
    if not path.exists():
        return "deleted", None
    return "ok", artifact


def serialize_artifact(job_id: str, artifact: ArtifactRecord) -> dict[str, Any]:
    return {
        "artifact_id": artifact.artifact_id,
        "filename": artifact.filename,
        "download_url": (
            f"https://sodh-5bsu.onrender.com"
            f"/api/literature/download/{job_id}/{artifact.artifact_id}"
        ),
        "mime_type": artifact.mime_type,
        "size_bytes": artifact.size_bytes,
    }


def tombstone_message(job_id: str) -> str | None:
    status = _EXPIRED_JOBS.get(job_id)
    if status and status.get("status") == "expired":
        return "Download expired"
    return None
