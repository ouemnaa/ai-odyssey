"""Application configuration"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # App Configuration
    DEBUG: bool = False
    APP_NAME: str = "Blockchain Forensics API"
    APP_VERSION: str = "1.0.0"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database
    DATABASE_URL: str = "sqlite:///./forensics.db"
    ASYNC_DATABASE_URL: str = "sqlite+aiosqlite:///./forensics.db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_ENABLED: bool = False

    # API Keys
    BITQUERY_API_KEY: str = "ory_at_GvkHmlXX6ZDpF96XMfO9J4pEk-ZdqPAMzqcEKCATCAI.KIdkp5fUfNMeBjoxi49d4onFazuqXCFYgHAGadfHG8Q"

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173"
    ]

    # Task Configuration
    TASK_QUEUE_TYPE: str = "background"  # "background" or "celery"
    MAX_ANALYSIS_DURATION_MINUTES: int = 30

    # Analysis Defaults
    DEFAULT_DAYS_BACK: int = 7
    DEFAULT_SAMPLE_SIZE: int = 1000
    MAX_SAMPLE_SIZE: int = 10000

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()
