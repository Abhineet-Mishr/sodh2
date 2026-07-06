from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.auth.auth_service import auth_service
from app.models.user import User
from app.services.credit.credit_service import reserve_credits, complete_credit_deduction, has_sufficient_credits
from app.core.config import DEDUPLICATE_CREDITS

from app.schemas.literature_responses import DeduplicateResponse
from app.services.analytics.analytics import generate_counts
from app.services.literature.artifact_manager import create_job, set_job_response, set_job_state
from app.services.literature.cleanup import cleanup_expired_artifacts
from app.services.literature.deduplicator import deduplicate_records
from app.services.literature.parser import detect_source_type, normalize_imported_dataframe, parse_bytes
from app.services.literature.normalizer import standardize_dataframe
from app.services.literature.pipeline import build_dataset_exports, preview_records, public_artifact_payload
from app.utils.helpers import parse_artifact_lifetime_minutes, parse_fuzzy_threshold

router = APIRouter(prefix="/api/literature", tags=["deduplicate"])


def _standardize_file(filename: str, content: bytes) -> pd.DataFrame:
    source_type = detect_source_type(filename)
    dataframe = parse_bytes(filename, content)
    if dataframe.empty:
        return dataframe
    if source_type == "CSV":
        dataframe = normalize_imported_dataframe(dataframe)
    return standardize_dataframe(dataframe, source_database=Path(filename).stem, source_type=source_type)


@router.post("/deduplicate", response_model=DeduplicateResponse)
async def deduplicate_files(
    files: list[UploadFile] = File(...),
    artifact_lifetime_minutes: int = Form(30),
    fuzzy_threshold: int = Form(90),
    current_user: User = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """Merge RIS/NBIB files, deduplicate them, and build screening exports."""
    cleanup_expired_artifacts()
    if not has_sufficient_credits(db, current_user.id, DEDUPLICATE_CREDITS):
        raise HTTPException(status_code=402, detail="Payment Required: Insufficient credits.")

    lifetime_minutes = parse_artifact_lifetime_minutes(artifact_lifetime_minutes)
    threshold = parse_fuzzy_threshold(fuzzy_threshold)

    if not files:
        raise HTTPException(status_code=400, detail="At least one file is required")

    seen_fingerprints: set[str] = set()
    frames: list[pd.DataFrame] = []
    source_counts: dict[str, int] = {}

    for uploaded in files:
        content = await uploaded.read()
        if not content:
            continue
        fingerprint = hashlib.sha256(uploaded.filename.encode("utf-8") + b"::" + content).hexdigest()
        if fingerprint in seen_fingerprints:
            continue
        seen_fingerprints.add(fingerprint)
        try:
            standardized = _standardize_file(uploaded.filename, content)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=f"{uploaded.filename}: {exc}") from exc
        if standardized.empty:
            continue
        source_counts[standardized["source_database"].iloc[0]] = source_counts.get(standardized["source_database"].iloc[0], 0) + len(standardized)
        frames.append(standardized)

    if not frames:
        raise HTTPException(status_code=400, detail="No records found")

    master_dataset = pd.concat(frames, ignore_index=True)
    if len(master_dataset) > 50_000:
        raise HTTPException(status_code=413, detail="Large file limit exceeded")

    dedupe_result = deduplicate_records(master_dataset, minimum_score=threshold)
    master_dataset = dedupe_result["master_dataset"]
    exact_title_dataset = dedupe_result["exact_title_dataset"]
    deduplicated_dataset = dedupe_result["deduplicated_dataset"]
    review_dataset = dedupe_result["review_dataset"]
    report = dedupe_result["report"]
    report.update(generate_counts(master_dataset, deduplicated_dataset))
    report["source_counts"] = source_counts

    job = create_job(pipeline_kind="deduplicate", artifact_lifetime_minutes=lifetime_minutes)
    ledger = reserve_credits(db, current_user.id, DEDUPLICATE_CREDITS, feature="deduplicate", job_id=job.job_id)
    complete_credit_deduction(db, ledger.id)
    set_job_state(
        job.job_id,
        master_dataset=master_dataset,
        exact_title_dataset=exact_title_dataset,
        deduplicated_dataset=deduplicated_dataset,
        review_dataset=review_dataset,
        report=report,
        source_counts=source_counts,
        finalized=False,
    )
    artifacts = build_dataset_exports(job.job_id, master_dataset, deduplicated_dataset, review_dataset, report, include_master=True)
    response = {
        "job_id": job.job_id,
        "preview": preview_records(deduplicated_dataset),
        "master_preview": preview_records(master_dataset),
        "review_preview": preview_records(review_dataset) if not review_dataset.empty else [],
        "report": report,
        "artifacts": public_artifact_payload(job.job_id, artifacts),
        "finalized": False,
    }
    set_job_response(job.job_id, response)
    return response
