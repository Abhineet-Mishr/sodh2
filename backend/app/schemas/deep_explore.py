from pydantic import BaseModel
from typing import Optional

class DeepExploreRequest(BaseModel):
    topic: str
    paper_limit: int = 100

class DeepExploreResponse(BaseModel):
    job_id: str
    status: str
