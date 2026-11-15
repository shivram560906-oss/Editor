"""Centralised application configuration.

All runtime settings (database URL, CORS origins) are
resolved from environment variables through a single :class:`Settings` object.
This keeps configuration in one auditable place and removes ad-hoc
``os.environ`` lookups scattered across the codebase.

A ``.env`` file is supported in development via :mod:`pydantic_settings`.
"""
from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from the environment / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Application ---
    APP_NAME: str = "Parashari Jyotish Software API"
    APP_VERSION: str = "2.0.0"
    CALCULATION_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    RELOAD: bool = False
    DEBUG: bool = False

    # --- Database ---
    DATABASE_URL: str = ""

    # --- CORS ---
    # Comma-separated list of allowed origins. Empty => local dev defaults.
    CORS_ORIGINS: str = ""

    # --- Rate limiting ---
    RATE_LIMIT_ENABLED: bool = True
    # e.g. "5/minute" for the heavy calculation endpoints.
    CALCULATE_RATE_LIMIT: str = "30/minute"

    @field_validator("ENVIRONMENT", mode="before")
    @classmethod
    def _validate_environment(cls, value: str) -> str:
        environment = (value or "development").strip().lower()
        if environment not in {"development", "test", "staging", "production"}:
            raise ValueError("ENVIRONMENT must be development, test, staging, or production")
        return environment

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def _default_database_url(cls, v: str) -> str:
        if v and v.strip():
            return v.strip()
        # Fall back to a local SQLite file inside the backend directory.
        import os
        db_path = os.path.normpath(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "jyotish.db")
        )
        return f"sqlite:///{db_path}"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT in {"staging", "production"}

    @property
    def cors_origin_list(self) -> List[str]:
        raw = (self.CORS_ORIGINS or "").strip()
        if raw:
            origins = [o.strip() for o in raw.split(",") if o.strip()]
            if "*" in origins:
                raise ValueError("Wildcard CORS_ORIGINS is not allowed with credentialed requests")
            return origins
        if self.is_production:
            raise ValueError("CORS_ORIGINS must be explicitly configured in staging/production")
        # Local development fallback only.
        return [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:4173",
            "http://127.0.0.1:4173",
        ]


@lru_cache
def get_settings() -> Settings:
    """Return a cached :class:`Settings` instance.

    Cached so repeated reads do not re-parse the environment / .env file.
    Tests can call ``get_settings.cache_clear()`` to reset.
    """
    return Settings()


settings = get_settings()
