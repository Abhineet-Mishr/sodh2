from fastapi import APIRouter, Depends
from app.schemas.search import SearchBuilderRequest, SearchBuilderResponse
from app.services.deep_explore import search_builder_service
# Un-comment auth dependency in production: from app.core.dependencies import get_current_user
# We might want this public or protected depending on business needs. Assuming public for MVP or user auth.
from app.core.dependencies import get_current_user
from app.models.user import User

router = APIRouter()

@router.post("/search-builder", response_model=SearchBuilderResponse)
async def build_search_queries(
    request: SearchBuilderRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Standalone Search Builder Endpoint (Feature C)
    Generates optimized search queries for PubMed, Scopus, and Embase.
    """
    # Does not deduct credits for now, or you could wrap in credit service.
    # TDD says standalone search builder, we can leave credit check out or add later.
    return await search_builder_service.generate_search_queries(request)
