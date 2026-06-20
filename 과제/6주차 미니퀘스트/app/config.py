"""환경 설정 로딩 (.env -> Settings)."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    google_api_key: str = ""
    gemini_chat_model: str = "gemini-2.5-flash"
    gemini_embed_model: str = "models/gemini-embedding-001"

    data_dir: str = "./data"
    index_dir: str = "./index"

    chunk_size: int = 800
    chunk_overlap: int = 120
    top_k: int = 4


@lru_cache
def get_settings() -> Settings:
    return Settings()
