from app.services.llm.factory import get_llm_provider
from app.services.llm.prompt_loader import load_prompt
from app.schemas.search import SearchBuilderRequest, SearchBuilderResponse

async def generate_search_queries(request: SearchBuilderRequest) -> SearchBuilderResponse:
    llm = get_llm_provider()

    prompt = load_prompt(
        "search_builder/query_expansion.md",
        TOPIC=request.topic,
        STUDY_TYPE=request.study_type or "",
        PURPOSE=request.purpose or ""
    )

    result_json = await llm.generate_json(prompt)

    return SearchBuilderResponse(**result_json)
