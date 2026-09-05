"""
Centralized application configuration.

All environment-driven settings live here so no other module reads
os.environ directly. Values are loaded from a .env file via
pydantic-settings.
"""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # =========================================================
    # GENERAL
    # =========================================================

    APP_NAME: str = "RecoverAI API"
    APP_ENV: str = "development"
    API_PREFIX: str = "/api"
    FRONTEND_URL: str = "http://127.0.0.1:5173"


    # =========================================================
    # CORS
    # =========================================================

    CORS_ORIGINS: str = (
        "http://localhost:5173,"
        "http://127.0.0.1:5173"
    )


    # =========================================================
    # MONGODB
    # =========================================================

    MONGODB_URI: str = ""
    MONGODB_DB_NAME: str = "recoverai"


    # =========================================================
    # AI / LLM
    # =========================================================

    LLM_API_KEY: str = ""


    # =========================================================
    # EMAIL
    # =========================================================

    
    EMAIL_HOST: str = "smtp.gmail.com"
    EMAIL_PORT: int = 587
    EMAIL_USERNAME: str = ""
    EMAIL_PASSWORD: str = ""
    EMAIL_FROM: str = ""
    BREVO_API_KEY: str = ""


    # =========================================================
    # PYDANTIC SETTINGS
    # =========================================================

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


    @property
    def cors_origins_list(self) -> List[str]:
        return [
            origin.strip()
            for origin in self.CORS_ORIGINS.split(",")
            if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    """
    Cached settings instance — .env is read once per process.
    """

    return Settings()