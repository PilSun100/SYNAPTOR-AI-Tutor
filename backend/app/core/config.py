from functools import cached_property
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_JWT_SECRET_KEY = "change-this-development-secret"
PRODUCTION_ENVIRONMENTS = {"production", "prod"}


class Settings(BaseSettings):
    app_name: str = "SYNAPTOR AI Tutor API"
    app_version: str = "0.1.0"
    environment: str = "development"
    gemini_api_key: str = ""
    embedding_model: str = "models/text-embedding-004"
    embedding_dimensions: int = 768
    database_url: str = f"sqlite:///{PROJECT_ROOT / 'data' / 'synaptor.db'}"
    upload_dir: str = str(PROJECT_ROOT / "data" / "uploads")
    max_upload_mb: int = 20
    cors_origins: str = "http://localhost:5173"
    jwt_secret_key: str = DEFAULT_JWT_SECRET_KEY
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

    @cached_property
    def is_production(self) -> bool:
        return self.environment.strip().lower() in PRODUCTION_ENVIRONMENTS

    def validate_runtime_security(self) -> None:
        if not self.is_production:
            return

        if self.jwt_secret_key == DEFAULT_JWT_SECRET_KEY or len(self.jwt_secret_key) < 32:
            raise RuntimeError(
                "Production 환경에서는 32자 이상의 고유한 JWT_SECRET_KEY를 설정해야 합니다."
            )


settings = Settings()
