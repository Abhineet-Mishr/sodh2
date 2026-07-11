from slowapi import Limiter
from slowapi.util import get_remote_address
limiter = Limiter(key_func=get_remote_address)
from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
import uuid

from app.schemas.research_suggestions import ResearchSuggestionRequest, ResearchSuggestionResponse
from app.services.research_suggestions.research_suggestions import research_suggestion_service
from app.services.credit.credit_service import reserve_credits, complete_credit_deduction, has_sufficient_credits
from app.core.config import FEATURE_A_CREDITS
from app.services.auth.auth_service import auth_service
from app.models.user import User
from app.core.database import get_db

router = APIRouter(prefix="/api/literature", tags=["research-suggestions"])

@router.post("/research-suggestions", response_model=ResearchSuggestionResponse)
@limiter.limit("5/minute")
async def get_research_suggestions(
    request: Request,
    body: ResearchSuggestionRequest,
    current_user: User = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """Generate AI-assisted research brainstorming suggestions."""
    # Pre-check credits
    if not has_sufficient_credits(db, current_user.id, FEATURE_A_CREDITS):
         raise HTTPException(status_code=402, detail="Payment Required: Insufficient credits.")

    job_id = f"job_research_suggestions_{uuid.uuid4().hex[:8]}"
    ledger = reserve_credits(db, current_user.id, FEATURE_A_CREDITS, feature="research_suggestions", job_id=job_id)

    try:
        response = research_suggestion_service.generate_suggestions(body)
    except Exception as e:
        error_msg = str(e)
        if "Internal Configuration" in error_msg:
             raise HTTPException(status_code=500, detail=error_msg)
        if "AI processing" in error_msg or "invalid structured data" in error_msg:
             raise HTTPException(status_code=502, detail=error_msg)
        raise HTTPException(status_code=500, detail="Unexpected error during processing.")

    # Deduct credits only if successful
    complete_credit_deduction(db, ledger.id)
    return response
