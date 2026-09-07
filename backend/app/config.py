from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ClassMind API"
    database_url: str = "sqlite:///./classmind.db"
    jwt_secret: str = "change-this-secret-before-production"
    jwt_expire_minutes: int = 720
    ai_provider: str = "demo"
    openai_api_key: str | None = None
    openai_model: str = "gpt-5.4-mini"
    cors_origins: str = "http://localhost:5173"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()

