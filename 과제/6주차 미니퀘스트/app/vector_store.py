"""FAISS 벡터스토어 구축/로드 (Gemini 임베딩 사용)."""
from __future__ import annotations

import os

from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.config import get_settings
from app.document_loader import load_and_split


def get_embeddings() -> GoogleGenerativeAIEmbeddings:
    settings = get_settings()
    return GoogleGenerativeAIEmbeddings(
        model=settings.gemini_embed_model,
        google_api_key=settings.google_api_key,
    )


def build_index(data_dir: str | None = None) -> FAISS:
    """문서를 임베딩하여 FAISS 인덱스를 만들고 디스크에 저장한다."""
    settings = get_settings()
    chunks = load_and_split(data_dir)
    store = FAISS.from_documents(chunks, get_embeddings())
    os.makedirs(settings.index_dir, exist_ok=True)
    store.save_local(settings.index_dir)
    print(f"[vector_store] {len(chunks)}개 청크 인덱싱 완료 -> {settings.index_dir}")
    return store


def load_index() -> FAISS:
    """저장된 FAISS 인덱스를 로드한다. 없으면 새로 빌드한다."""
    settings = get_settings()
    faiss_file = os.path.join(settings.index_dir, "index.faiss")
    if not os.path.exists(faiss_file):
        return build_index()
    return FAISS.load_local(
        settings.index_dir,
        get_embeddings(),
        allow_dangerous_deserialization=True,
    )
