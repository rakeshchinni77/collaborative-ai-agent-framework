from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Centralized application configuration loaded from environment variables.
    Uses Pydantic Settings for validation and type safety.
    """

    # LLM Configuration
    LLM_API_KEY: str = Field(..., description="API key for LLM provider")

    # Application Configuration
    API_PORT: int = Field(8000, description="Port on which the FastAPI app runs")

    # Database Configuration
    DATABASE_URL: str = Field(..., description="PostgreSQL connection URL")

    # Redis Configuration
    REDIS_URL: str = Field(..., description="Redis connection URL")

    # Celery Configuration
    CELERY_BROKER_URL: str = Field(..., description="Celery broker URL")
    CELERY_RESULT_BACKEND: str = Field(..., description="Celery result backend URL")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """
    Returns a cached Settings instance.
    Ensures settings are loaded only once per process.
    """
    return Settings()


# Singleton settings instance for import across the app
settings = get_settings()
