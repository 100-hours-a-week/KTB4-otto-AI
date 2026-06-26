"""FastAPI 서버: LangChain RAG 체인을 REST API 로 노출."""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.ingest import build_index
from app.rag_chain import get_chain, reset_chain


# ----- 요청 / 응답 스키마 -----
class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, description="사용자 질문")


class QueryResponse(BaseModel):
    question: str
    answer: str
    contexts: List[str]
    sources: List[str]


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, description="사용자 질문")
    session_id: str = Field("default", description="대화 세션 식별자 (멀티턴 맥락 유지)")


class SearchHit(BaseModel):
    text: str
    source: str


# ----- lifespan: 시작 시 인덱스/체인 워밍업 -----
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        get_chain()  # Chroma 로드 + Gemini 초기화
        print("[startup] LangChain RAG 체인 준비 완료")
    except Exception as exc:  # 키 누락/인덱스 없음에도 서버는 뜨도록
        print(f"[startup] 체인 초기화 경고: {exc}")
    yield


app = FastAPI(
    title="otto RAG API",
    description="LangChain + Gemini 기반 RAG 파이프라인",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/reindex")
def reindex():
    """docs/ 문서를 다시 임베딩하여 Chroma 인덱스 재구축."""
    try:
        store = build_index()
        reset_chain()  # 새 인덱스로 체인 갱신
        return {"status": "reindexed", "vectors": store._collection.count()}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/search", response_model=List[SearchHit])
def search(q: str):
    """검색만 (LLM 호출 없음). 검색 품질 점검용."""
    try:
        return get_chain().search(q)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest):
    """단발성 질문에 RAG 로 답변 (대화 기록 없음)."""
    try:
        return QueryResponse(**get_chain().query(req.question))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/chat", response_model=QueryResponse)
def chat(req: ChatRequest):
    """멀티턴 대화. session_id 별로 이전 대화 맥락을 유지한다."""
    try:
        return QueryResponse(**get_chain().chat(req.question, req.session_id))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/chat/reset")
def chat_reset(session_id: str = "default"):
    """해당 세션의 대화 기록 초기화."""
    get_chain().reset_session(session_id)
    return {"status": "reset", "session_id": session_id}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.api:app", host="0.0.0.0", port=8000, reload=True)
