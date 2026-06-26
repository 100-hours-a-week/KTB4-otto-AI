"""환경 설정 (.env -> Settings) + LangSmith Tracing 활성화."""
from __future__ import annotations

import os
from functools import lru_cache

from langchain_core.rate_limiters import InMemoryRateLimiter
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- LLM / Embedding (Gemini) ---
    google_api_key: str = ""
    gemini_chat_model: str = "gemini-2.5-flash-lite"
    gemini_embed_model: str = "models/gemini-embedding-001"

    # --- 경로 / 컬렉션 ---
    docs_dir: str = "./docs"
    chroma_dir: str = "./chroma_db"
    collection_name: str = "rag_otto"

    # --- 검색 / 청크 파라미터 ---
    chunk_size: int = 400
    chunk_overlap: int = 80
    top_k: int = 3

    # --- 멀티턴 대화 기록: 프롬프트에 넣을 최근 메시지 최대 개수 ---
    # (대화가 길어져도 토큰 폭증/컨텍스트 초과를 막음. 6 = 최근 3턴)
    history_window: int = 6

    # --- Gemini 분당 호출 제한 ---
    gemini_rpm: int = 12

    # --- LangSmith Tracing ---
    langsmith_tracing: bool = False
    langsmith_api_key: str = ""
    langsmith_project: str = "otto-rag-langchain"
    langsmith_endpoint: str = "https://api.smith.langchain.com"


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    # LangSmith 는 표준 LANGCHAIN_* 환경변수로 동작
    if settings.langsmith_tracing and settings.langsmith_api_key:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = settings.langsmith_api_key
        os.environ["LANGCHAIN_PROJECT"] = settings.langsmith_project
        os.environ["LANGCHAIN_ENDPOINT"] = settings.langsmith_endpoint
    return settings


@lru_cache
def get_rate_limiter() -> InMemoryRateLimiter:
    """LLM 호출 속도 제한기 (여러 LLM 인스턴스가 공유)."""
    rpm = get_settings().gemini_rpm
    return InMemoryRateLimiter(
        requests_per_second=rpm / 60.0,
        check_every_n_seconds=0.5,
        max_bucket_size=1,
    )
