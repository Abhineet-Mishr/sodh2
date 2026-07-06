export interface ResearchSuggestionRequest {
  topic: string;
  purpose?: string;
}

export interface ResearchSuggestionData {
  summary: string;
  research_gaps: string[];
  emerging_topics: string[];
  future_directions: string[];
  srma_topics: string[];
  cohort_studies: string[];
  clinical_studies: string[];
  rct_ideas: string[];
  ai_ml_opportunities: string[];
  interdisciplinary_ideas: string[];
  references: string[];
}

export interface ResearchSuggestionResponse {
  status: string;
  topic: string;
  model: string;
  credits_used: number;
  processing_time: number;
  data: ResearchSuggestionData;
}
