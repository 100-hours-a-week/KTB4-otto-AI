"""FastAPI 서버: RAG 파이프라인을 REST API로 노출."""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.rag_pipeline import get_pipeline
from app.vector_store import build_index


# ----- 요청/응답 스키마 -----
class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, description="사용자 질문")


class QueryResponse(BaseModel):
    question: str
    answer: str
    contexts: List[str]
    sources: List[str]


# ----- 앱 lifespan: 시작 시 인덱스/파이프라인 워밍업 -----
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        get_pipeline()  # 인덱스 로드 + LLM 초기화
        print("[startup] RAG 파이프라인 준비 완료")
    except Exception as exc:  # 인덱스 없거나 키 누락 시에도 서버는 뜨도록
        print(f"[startup] 파이프라인 초기화 경고: {exc}")
    yield


app = FastAPI(
    title="Gemini RAG API",
    description="Gemini 기반 RAG 파이프라인 REST API",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/reindex")
def reindex():
    """data/ 문서를 다시 임베딩하여 인덱스 재구축."""
    try:
        store = build_index()
        return {"status": "reindexed", "vectors": store.index.ntotal}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest):
    """질문에 RAG로 답변."""
    try:
        result = get_pipeline().query(req.question)
        return QueryResponse(**result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
