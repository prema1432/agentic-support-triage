"""Application settings loaded from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Agentic Support Triage API"
    mongo_url: str = "mongodb://localhost:27017"
    mongo_db: str = "support_triage"
    llm_provider: str = "mock"
    openai_api_key: str | None = None
    cors_origins: str = "http://localhost:5173"

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
