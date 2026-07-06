import time
import logging
from typing import Dict, Any

from pydantic import ValidationError

from .ai.gemini import GeminiProvider
from .ai.prompt_registry import prompt_registry
from ..schemas.research_suggestions import ResearchSuggestionRequest, ResearchSuggestionResponse, ResearchSuggestionData
from app.core.config import FEATURE_A_CREDITS

logger = logging.getLogger(__name__)

class ResearchSuggestionService:
    def __init__(self):
        # We can eventually inject providers based on config, hardcoded to Gemini for now
        self.provider = GeminiProvider()

    def generate_suggestions(self, request: ResearchSuggestionRequest) -> ResearchSuggestionResponse:
        start_time = time.time()

        # 1. Load system prompt
        try:
            system_instruction = prompt_registry.load_prompt(
                template_name="research_suggestions",
                variables={}
            )
        except Exception as e:
            logger.error(f"Failed to load prompt: {e}")
            raise Exception("Internal Configuration Error: Missing prompt template.")

        # 2. Construct User Input
        user_prompt = f"Research Topic:\n{request.topic}\n\nPurpose:\n{request.purpose}"

        # 3. Call AI Provider
        try:
            raw_response = self.provider.generate_structured_output(
                prompt=user_prompt,
                response_schema=ResearchSuggestionData,
                system_instruction=system_instruction,
                temperature=0.7,
                max_tokens=8192
            )
        except Exception as e:
            logger.error(f"AI Provider failed: {e}")
            raise Exception("AI processing failed. Please try again.")

        # 3. Validate Response Schema
        try:
            data = ResearchSuggestionData(**raw_response)
        except ValidationError as e:
            logger.error(f"Response validation failed: {e.errors()}")
            # Simple fallback for missing lists to empty lists, or generic message for summary
            fallback_data = self._attempt_fallback(raw_response)
            if not fallback_data:
                raise Exception("AI returned invalid structured data.")
            data = fallback_data

        processing_time = round(time.time() - start_time, 2)

        # 4. Deduct Credits

        # 5. Return Response
        return ResearchSuggestionResponse(
            status="success",
            topic=request.topic,
            model=self.provider.model_name,
            credits_used=FEATURE_A_CREDITS,
            processing_time=processing_time,
            data=data
        )

    def _attempt_fallback(self, raw_data: Dict[str, Any]) -> ResearchSuggestionData | None:
        """Attempt to salvage a partially malformed response."""
        try:
            fallback = {
                "summary": raw_data.get("summary", "N/A"),
                "research_gaps": raw_data.get("research_gaps", []),
                "emerging_topics": raw_data.get("emerging_topics", []),
                "future_directions": raw_data.get("future_directions", []),
                "srma_topics": raw_data.get("srma_topics", []),
                "cohort_studies": raw_data.get("cohort_studies", []),
                "clinical_studies": raw_data.get("clinical_studies", []),
                "rct_ideas": raw_data.get("rct_ideas", []),
                "ai_ml_opportunities": raw_data.get("ai_ml_opportunities", []),
                "interdisciplinary_ideas": raw_data.get("interdisciplinary_ideas", []),
                "references": raw_data.get("references", []),
            }
            # Ensure everything that should be a list is actually a list
            for key in fallback:
                 if key != "summary" and not isinstance(fallback[key], list):
                     fallback[key] = [fallback[key]] if fallback[key] else []
            return ResearchSuggestionData(**fallback)
        except Exception as e:
             logger.error(f"Fallback recovery failed: {e}")
             return None

research_suggestion_service = ResearchSuggestionService()
