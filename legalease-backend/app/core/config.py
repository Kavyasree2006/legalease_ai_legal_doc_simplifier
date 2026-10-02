from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "LegalEase API"
    environment: str = "development"
    secret_key: str = "change-me"
    access_token_expire_minutes: int = 1440
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/legalease"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "gemma3:4b"
    upload_dir: str = "storage/uploads"
    report_dir: str = "storage/reports"
    max_upload_size_mb: int = 25
    cors_origins: str = "http://localhost:5173"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [x.strip() for x in self.cors_origins.split(",") if x.strip()]

@lru_cache
def get_settings() -> Settings:
    return Settings()
