"""문서 로딩 + 청킹.

data/ 디렉토리의 .txt, .md, .pdf 파일을 읽어 LangChain Document 리스트로 변환하고,
RecursiveCharacterTextSplitter로 청크 단위로 분할한다.
"""
from __future__ import annotations

import glob
import os
from typing import List

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_core.documents import Document

from app.config import get_settings


def load_documents(data_dir: str | None = None) -> List[Document]:
    """data_dir 안의 지원 파일을 모두 로드한다."""
    settings = get_settings()
    data_dir = data_dir or settings.data_dir

    docs: List[Document] = []
    patterns = {
        "**/*.txt": TextLoader,
        "**/*.md": TextLoader,
        "**/*.pdf": PyPDFLoader,
    }

    for pattern, loader_cls in patterns.items():
        for path in glob.glob(os.path.join(data_dir, pattern), recursive=True):
            if loader_cls is TextLoader:
                loader = loader_cls(path, encoding="utf-8")
            else:
                loader = loader_cls(path)
            loaded = loader.load()
            for d in loaded:
                d.metadata.setdefault("source", os.path.basename(path))
            docs.extend(loaded)

    if not docs:
        raise FileNotFoundError(
            f"'{data_dir}' 에서 로드할 문서를 찾지 못했습니다 (.txt/.md/.pdf)."
        )
    return docs


def split_documents(docs: List[Document]) -> List[Document]:
    """문서를 청크로 분할한다."""
    settings = get_settings()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    return splitter.split_documents(docs)


def load_and_split(data_dir: str | None = None) -> List[Document]:
    return split_documents(load_documents(data_dir))
