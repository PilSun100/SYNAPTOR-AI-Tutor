from functools import cached_property
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    app_name: str = "Brain-Sync AI Tutor API"
    app_version: str = "0.1.0"
    gemini_api_key: str = ""
    database_url: str = f"sqlite:///{PROJECT_ROOT / 'data' / 'brain_sync.db'}"
    upload_dir: str = str(PROJECT_ROOT / "data" / "uploads")
    max_upload_mb: int = 20
    cors_origins: str = "http://localhost:5173"
    jwt_secret_key: str = "change-this-development-secret"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 14
    auto_create_tables: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @cached_property
    def cors_origin_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]


settings = Settings()
