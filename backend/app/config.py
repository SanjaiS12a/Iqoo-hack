from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ClassMind API"
    database_url: str = "sqlite:///./classmind_control.db"
    grade_database_dir: str = "./grade_databases"
    grade_database_url_template: str | None = None
    upload_dir: str = "./uploads"
    jwt_secret: str = "change-this-secret-before-production"
    jwt_expire_minutes: int = 720
    ai_provider: str = "demo"
    openai_api_key: str | None = None
    openai_model: str = "gpt-5.4-mini"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"
    local_ai_base_url: str = "http://localhost:11434/v1"
    local_ai_model: str = "qwen2.5vl"
    cors_origins: str = "http://localhost:5173"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
