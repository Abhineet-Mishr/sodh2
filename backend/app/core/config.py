from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "SODH AI-powered Research Operating System"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"

    # Use SQLite for testing if Postgres isn't running locally in the sandbox
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "sodh_db"
    POSTGRES_PORT: str = "5432"

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        if os.environ.get("DATABASE_URL"):
            return os.environ.get("DATABASE_URL")

        # Check if we should use SQLite instead
        if os.environ.get("USE_SQLITE", "false").lower() == "true":
            return "sqlite:///./sodh.db"
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # JWT Settings
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days

    # CORS Settings
    BACKEND_CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    # Initial Credits
    INITIAL_USER_CREDITS: int = 50

    # LLM Settings
    DEFAULT_LLM_PROVIDER: str = "gemini" # gemini, gpt, deepseek, ollama
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    # External APIs
    PUBMED_API_KEY: str = ""  # Optional, but increases rate limits
    NCBI_TOOL_NAME: str = "SODH_DeepExplore"
    NCBI_EMAIL: str = "user@example.com"

    # Deep Explore Config
    DEFAULT_PAPER_LIMIT: int = 100
    FEATURE_A_CREDIT_COST: int = 5
    DEEP_EXPLORE_CREDIT_COST_100: int = 10
    DEEP_EXPLORE_CREDIT_COST_200: int = 15
    DEEP_EXPLORE_CREDIT_COST_300: int = 20

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore")

settings = Settings()
