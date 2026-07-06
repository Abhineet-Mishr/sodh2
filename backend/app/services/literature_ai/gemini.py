import json
import logging
from typing import Any, Dict

from google import genai
from google.genai import types
from pydantic import BaseModel

from .base import BaseLLMProvider
from ...config import GEMINI_API_KEY, GEMINI_MODEL

logger = logging.getLogger(__name__)

class GeminiProvider(BaseLLMProvider):
    def __init__(self):
        if not GEMINI_API_KEY:
            logger.warning("GEMINI_API_KEY is not set. API calls will fail.")
            # Set a dummy key to prevent SDK initialization from crashing on startup
            self.client = genai.Client(api_key="DUMMY_KEY_FOR_TESTING")
        else:
            self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.model_name = GEMINI_MODEL

    def generate_structured_output(self, prompt: str, response_schema: Any, system_instruction: str = None, temperature: float = 0.7, max_tokens: int = 1024) -> Dict[str, Any]:
        """Generates structured JSON output from Gemini based on the given prompt and schema."""
        logger.info(f"Calling Gemini ({self.model_name})")

        try:
            config_args = {
                "response_mime_type": "application/json",
                "response_schema": response_schema,
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            }
            if system_instruction:
                config_args["system_instruction"] = system_instruction

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(**config_args),
            )

            if not response.text:
                 raise Exception("Gemini returned empty text.")

            logger.info(f"Tokens - prompt: {response.usage_metadata.prompt_token_count if response.usage_metadata else 'N/A'}, completion: {response.usage_metadata.candidates_token_count if response.usage_metadata else 'N/A'}")

            return json.loads(response.text)
        except json.JSONDecodeError as e:
             logger.error(f"Failed to parse JSON from Gemini: {e}")
             logger.debug(f"Raw Gemini output: {response.text}")
             raise Exception("Invalid JSON returned from AI provider.")
        except Exception as e:
            logger.error(f"Gemini API Error: {str(e)}")
            raise Exception(f"AI Provider Error: {str(e)}")
