from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseLLMProvider(ABC):
    @abstractmethod
    def generate_structured_output(self, prompt: str, response_schema: Any, system_instruction: str = None, temperature: float = 0.7, max_tokens: int = 1024) -> Dict[str, Any]:
        """Generates structured JSON output from the LLM based on the given prompt and schema."""
        pass
