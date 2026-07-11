from typing import List, Optional
from pydantic import BaseModel, Field

class ResearchSuggestionRequest(BaseModel):
    topic: str = Field(..., min_length=3, max_length=300, description="The biomedical research topic.")
    purpose: str = Field("General brainstorming", max_length=300, description="The purpose or context of the research.")

class ResearchSuggestionData(BaseModel):
    summary: str = Field(..., description="A short summary of the topic context.")
    research_gaps: List[str] = Field(default_factory=list, description="List of identified research gaps.")
    emerging_topics: List[str] = Field(default_factory=list, description="List of emerging topics in the field.")
    future_directions: List[str] = Field(default_factory=list, description="List of future research directions.")
    srma_topics: List[str] = Field(default_factory=list, description="Suggested Systematic Review and Meta-Analysis (SRMA) topics.")
    cohort_studies: List[str] = Field(default_factory=list, description="Suggested cohort study designs.")
    clinical_studies: List[str] = Field(default_factory=list, description="Suggested clinical study designs.")
    rct_ideas: List[str] = Field(default_factory=list, description="Suggested Randomized Controlled Trial (RCT) ideas.")
    ai_ml_opportunities: List[str] = Field(default_factory=list, description="Opportunities for AI/ML application.")
    interdisciplinary_ideas: List[str] = Field(default_factory=list, description="Novel interdisciplinary research ideas.")
    references: List[str] = Field(default_factory=list, description="Any provided references, if applicable.")

class ResearchSuggestionResponse(BaseModel):
    status: str
    topic: str
    model: str
    credits_used: int
    processing_time: float
    data: ResearchSuggestionData
