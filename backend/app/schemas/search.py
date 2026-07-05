from pydantic import BaseModel
from typing import Optional

class SearchBuilderRequest(BaseModel):
    topic: str
    study_type: Optional[str] = None
    purpose: Optional[str] = None

class SearchBuilderResponse(BaseModel):
    pubmed_query: str
    scopus_query: str
    embase_query: str
