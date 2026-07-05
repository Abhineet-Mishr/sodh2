from app.core.config import settings
from app.services.llm.provider import LLMProvider
from app.services.llm.gemini_provider import GeminiProvider

def get_llm_provider() -> LLMProvider:
    provider_name = settings.DEFAULT_LLM_PROVIDER.lower()

    if provider_name == "gemini":
        return GeminiProvider()
    # Support for gpt, deepseek, ollama could be added here
    else:
        raise ValueError(f"Unsupported LLM provider: {provider_name}")
