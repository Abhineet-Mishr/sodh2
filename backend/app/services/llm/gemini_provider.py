import json
import httpx
from typing import Any, List
from app.services.llm.provider import LLMProvider
from app.core.config import settings

class GeminiProvider(LLMProvider):
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model = settings.GEMINI_MODEL
        self.base_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        self.embedding_url = "https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent"

    async def generate_json(self, prompt: str) -> Any:
        # Since we enforce JSON output from the LLM via prompt, we can use the API directly
        # and expect it to return JSON within markdown block ```json ... ``` or directly

        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseMimeType": "application/json"
            }
        }

        url = f"{self.base_url}?key={self.api_key}"

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=90.0)
            response.raise_for_status()

            data = response.json()
            try:
                # Gemini returns the text inside candidates[0].content.parts[0].text
                text_content = data["candidates"][0]["content"]["parts"][0]["text"]
                try:
                    return json.loads(text_content)
                except json.JSONDecodeError:
                    import re
                    match = re.search(r'```(?:json)?\s*(.*?)\s*```', text_content, re.DOTALL)
                    if match:
                        return json.loads(match.group(1))
                    raise
            except (KeyError, IndexError, json.JSONDecodeError) as e:
                raise ValueError(f"Failed to parse JSON from Gemini response: {str(e)} Content: {data.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')}")

    async def generate_embeddings(self, text: str) -> List[float]:
        headers = {"Content-Type": "application/json"}
        payload = {
            "model": "models/text-embedding-004",
            "content": {"parts": [{"text": text}]}
        }

        url = f"{self.embedding_url}?key={self.api_key}"

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=30.0)
            response.raise_for_status()

            data = response.json()
            try:
                return data["embedding"]["values"]
            except KeyError:
                raise ValueError("Failed to retrieve embeddings from Gemini response")
