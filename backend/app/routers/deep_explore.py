from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.deep_explore_job import DeepExploreJob
from app.models.report_cache import ReportCache
from app.schemas.deep_explore import DeepExploreRequest, DeepExploreResponse
from app.services.deep_explore.orchestrator import execute_deep_explore_job
from app.services.credit.credit_service import reserve_credits
import uuid
import asyncio

router = APIRouter()

@router.post("/", response_model=DeepExploreResponse)
async def create_deep_explore_job(
    request: DeepExploreRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    credits_needed = 10
    if request.paper_limit >= 200:
        credits_needed = 15
    if request.paper_limit >= 300:
        credits_needed = 20

    job_id = f"de_{uuid.uuid4().hex[:8]}"

    try:
        reserve_credits(db, current_user.id, credits_needed, "Deep Explore", job_id)
    except ValueError as e:
        raise HTTPException(status_code=402, detail=str(e))

    job = DeepExploreJob(
        job_id=job_id,
        user_id=current_user.id,
        requested_topic=request.topic,
        normalized_topic=request.topic.lower().replace(" ", "_"),
        paper_limit=request.paper_limit,
        credits_used=credits_needed
    )
    db.add(job)
    db.commit()

    background_tasks.add_task(run_orchestrator, job_id)

    return DeepExploreResponse(job_id=job_id, status="QUEUED")

@router.get("/{job_id}")
async def get_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    job = db.query(DeepExploreJob).filter(DeepExploreJob.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this job")

    response_data = {
        "job_id": job.job_id,
        "status": job.status,
        "topic": job.requested_topic
    }

    if job.status == "COMPLETED" and job.report_cache_id:
        report = db.query(ReportCache).filter(ReportCache.cache_id == job.report_cache_id).first()
        if report:
            response_data["report"] = report.generated_report
            response_data["search_queries"] = job.search_queries

    return response_data

def run_orchestrator(job_id: str):
    from app.core.database import SessionLocal
    bg_db = SessionLocal()
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(execute_deep_explore_job(bg_db, job_id))
    finally:
        bg_db.close()
        loop.close()
