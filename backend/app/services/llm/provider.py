from abc import ABC, abstractmethod
from typing import Dict, Any, List

class LLMProvider(ABC):

    @abstractmethod
    async def generate_json(self, prompt: str) -> Any:
        """
        Sends the prompt to the LLM and expects a JSON response.
        Returns the parsed JSON as a Python dict or list.
        """
        pass

    @abstractmethod
    async def generate_embeddings(self, text: str) -> List[float]:
        """
        Generates vector embeddings for a given text.
        """
        pass
