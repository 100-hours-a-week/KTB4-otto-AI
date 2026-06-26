"""문서 로딩 -> 청킹 -> 임베딩 -> Chroma 저장."""
from __future__ import annotations

import os
from typing import List

import chromadb
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import get_settings


def get_embeddings() -> GoogleGenerativeAIEmbeddings:
    settings = get_settings()
    return GoogleGenerativeAIEmbeddings(
        model=settings.gemini_embed_model,
        google_api_key=settings.google_api_key,
    )


def load_documents(docs_dir: str | None = None) -> List[Document]:
    """docs_dir 안의 .md/.txt/.pdf 를 LangChain Document 리스트로 로드."""
    settings = get_settings()
    docs_dir = docs_dir or settings.docs_dir

    documents: List[Document] = []
    for name in sorted(os.listdir(docs_dir)):
        path = os.path.join(docs_dir, name)
        if not os.path.isfile(path):
            continue
        ext = os.path.splitext(name)[1].lower()
        if ext in (".md", ".txt"):
            loader = TextLoader(path, encoding="utf-8")
        elif ext == ".pdf":
            loader = PyPDFLoader(path)
        else:
            continue
        loaded = loader.load()
        for d in loaded:
            d.metadata["source"] = name  # 출처를 파일명으로 표준화
        documents.extend(loaded)

    if not documents:
        raise FileNotFoundError(f"'{docs_dir}' 에 로드할 문서가 없습니다 (.md/.txt/.pdf).")
    return documents


def split_documents(documents: List[Document]) -> List[Document]:
    settings = get_settings()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n## ", "\n\n", "\n", ". ", " ", ""],
    )
    return splitter.split_documents(documents)


def build_index(docs_dir: str | None = None) -> Chroma:
    """문서를 임베딩하여 Chroma 인덱스를 (재)구축하고 디스크에 저장한다."""
    settings = get_settings()

    # 디렉토리 삭제 대신 컬렉션만 비워 재구축 (서버 가동 중 재인덱싱 안전)
    client = chromadb.PersistentClient(path=settings.chroma_dir)
    try:
        client.delete_collection(settings.collection_name)
    except Exception:
        pass

    chunks = split_documents(load_documents(docs_dir))
    store = Chroma.from_documents(
        documents=chunks,
        embedding=get_embeddings(),
        collection_name=settings.collection_name,
        persist_directory=settings.chroma_dir,
        client=client,
        collection_metadata={"hnsw:space": "cosine"},
    )
    print(f"[ingest] 청크 {len(chunks)}개 인덱싱 완료 -> {settings.chroma_dir}")
    return store


def load_index() -> Chroma:
    """저장된 Chroma 인덱스를 로드한다. 없으면 새로 빌드한다."""
    settings = get_settings()
    if not os.path.exists(settings.chroma_dir):
        return build_index()
    return Chroma(
        collection_name=settings.collection_name,
        embedding_function=get_embeddings(),
        persist_directory=settings.chroma_dir,
    )


if __name__ == "__main__":
    build_index()
