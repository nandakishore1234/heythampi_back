"""Application configuration using Pydantic settings."""
from __future__ import annotations

from functools import lru_cache

from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    project_name: str = "HeyThambi"
    environment: str = "development"
    database_url: str
    alembic_database_url: str | None = None
    firebase_credentials_path: str = Field(..., alias="FIREBASE_CREDENTIALS_PATH")
    firebase_storage_bucket: str = Field(..., alias="FIREBASE_STORAGE_BUCKET")

    gemini_api_key: str = Field(..., alias="GEMINI_API_KEY")


    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @property
    def sync_database_url(self) -> str:
        """Return a sync-compatible SQLAlchemy URL for Alembic migrations."""
        return self.alembic_database_url or self.database_url

    @field_validator("firebase_credentials_path")
    @classmethod
    def validate_credentials_path(cls, value: str) -> str:
        path = Path(value)
        if not path.exists():
            raise ValueError(f"Firebase credentials file not found at {value}")
        return str(path)


@lru_cache
def get_settings() -> Settings:
    """Cache settings to avoid repeated environment parsing."""

    return Settings()


settings = get_settings()
