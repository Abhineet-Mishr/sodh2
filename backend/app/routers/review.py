from __future__ import annotations

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.auth.auth_service import auth_service
from app.models.user import User

from app.schemas.literature_requests import ReviewDecisionPayload, ThresholdUpdatePayload
from app.schemas.literature_responses import DeduplicateResponse
from app.services.analytics.analytics import generate_counts
from app.services.literature.artifact_manager import get_job, serialize_artifact, set_job_response, set_job_state
from app.services.literature.cleanup import cleanup_expired_artifacts
from app.services.literature.deduplicator import apply_review_decisions, recompute_fuzzy_stage
from app.services.literature.pipeline import build_dataset_exports, preview_records, public_artifact_payload

router = APIRouter(prefix="/api/literature", tags=["review"])


def _job_or_404(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/jobs/{job_id}/review")
def save_review_decisions(job_id: str, payload: ReviewDecisionPayload, current_user: User = Depends(auth_service.get_current_user), db: Session = Depends(get_db)):
    """Persist reviewer selections without regenerating exports."""
    cleanup_expired_artifacts()
    job = _job_or_404(job_id)
    job.review_decisions = dict(payload.decisions)
    review_dataset = job.review_dataset.copy().reset_index(drop=True)
    if "decision" not in review_dataset.columns:
        review_dataset["decision"] = "Review"
    for index, row in review_dataset.iterrows():
        review_id = str(row.get("review_id", ""))
        if review_id in payload.decisions:
            review_dataset.at[index, "decision"] = payload.decisions[review_id]
    set_job_state(job_id, review_dataset=review_dataset)
    response_preview = preview_records(review_dataset)
    response = job.response.copy()
    response["review_preview"] = response_preview
    set_job_response(job_id, response)
    return {"job_id": job_id, "saved": True, "review_preview": response_preview}


@router.post("/jobs/{job_id}/fuzzy-threshold", response_model=DeduplicateResponse)
def update_fuzzy_threshold(job_id: str, payload: ThresholdUpdatePayload, current_user: User = Depends(auth_service.get_current_user), db: Session = Depends(get_db)):
    """Recompute only the fuzzy stage from the existing exact-title dataset."""
    cleanup_expired_artifacts()
    job = _job_or_404(job_id)
    fuzzy_result = recompute_fuzzy_stage(job.exact_title_dataset, minimum_score=payload.fuzzy_threshold)
    deduplicated_dataset = fuzzy_result["deduplicated_dataset"]
    review_dataset = fuzzy_result["review_dataset"]
    review_ids = set(review_dataset.get("review_id", []))
    preserved_decisions = {
        review_id: decision
        for review_id, decision in job.review_decisions.items()
        if review_id in review_ids
    }
    if preserved_decisions:
        review_dataset = review_dataset.copy()
        for index, row in review_dataset.iterrows():
            review_id = str(row.get("review_id", ""))
            if review_id in preserved_decisions:
                review_dataset.at[index, "decision"] = preserved_decisions[review_id]
    report = dict(job.report)
    report.update(fuzzy_result["report"])
    report.update(generate_counts(job.master_dataset, deduplicated_dataset))
    report["source_counts"] = job.source_counts

    artifacts = build_dataset_exports(job_id, job.master_dataset, deduplicated_dataset, review_dataset, report, include_master=False)
    artifacts_payload = {"master_dataset_csv": serialize_artifact(job_id, job.artifacts["master_dataset_csv"]), **public_artifact_payload(job_id, artifacts)}
    response = {
        "job_id": job_id,
        "preview": preview_records(deduplicated_dataset),
        "master_preview": preview_records(job.master_dataset),
        "review_preview": preview_records(review_dataset) if not review_dataset.empty else [],
        "report": report,
        "artifacts": artifacts_payload,
        "finalized": False,
    }
    set_job_state(
        job_id,
        deduplicated_dataset=deduplicated_dataset,
        review_dataset=review_dataset,
        report=report,
        review_decisions=preserved_decisions,
        finalized=False,
    )
    set_job_response(job_id, response)
    return response


@router.post("/jobs/{job_id}/finalize", response_model=DeduplicateResponse)
def finalize_review(job_id: str, payload: ReviewDecisionPayload):
    """Apply reviewer choices and regenerate the final export bundle."""
    cleanup_expired_artifacts()
    job = _job_or_404(job_id)
    finalized_dataset, review_dataset, review_report = apply_review_decisions(job.exact_title_dataset, job.review_dataset, payload.decisions)
    report = dict(job.report)
    report.update(review_report)
    report.update(generate_counts(job.master_dataset, finalized_dataset))
    report["source_counts"] = job.source_counts

    artifacts = build_dataset_exports(job_id, job.master_dataset, finalized_dataset, review_dataset, report, include_master=False)
    artifacts_payload = {"master_dataset_csv": serialize_artifact(job_id, job.artifacts["master_dataset_csv"]), **public_artifact_payload(job_id, artifacts)}
    response = {
        "job_id": job_id,
        "preview": preview_records(finalized_dataset),
        "master_preview": preview_records(job.master_dataset),
        "review_preview": preview_records(review_dataset),
        "report": report,
        "artifacts": artifacts_payload,
        "finalized": True,
    }
    set_job_state(
        job_id,
        deduplicated_dataset=finalized_dataset,
        review_dataset=review_dataset,
        report=report,
        review_decisions=dict(payload.decisions),
        finalized=True,
    )
    set_job_response(job_id, response)
    return response
