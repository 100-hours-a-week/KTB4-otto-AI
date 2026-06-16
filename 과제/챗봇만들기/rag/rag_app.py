"""
연구 데이터 RAG 챗봇 - FastAPI 서버
=====================================
내 로컬 데이터(표 CSV/Excel + 문서)에 접근해, 질문에 대해
실제 계산값과 문서 근거를 바탕으로 답하는 챗봇.

  질문 → [retriever] 문서검색 + 표계산 → [llm_backend] 답변생성 → 응답

실행:
    # (1) 문서 인덱스 생성 (문서가 있을 때 1회)
    python3 ingest.py
    # (2) 서버 실행
    python3 -m uvicorn rag_app:app --reload
    # 채팅:  http://127.0.0.1:8000

Claude 로 답변 품질을 높이려면:
    export ANTHROPIC_API_KEY=sk-ant-...   # 키를 넣으면 자동으로 Claude 사용
"""

import os

# .env 파일이 있으면 환경변수로 로드 (ANTHROPIC_API_KEY 등) — 외부 의존성 없이 직접 파싱
def _load_dotenv():
    path = os.path.join(os.path.dirname(__file__), ".env")
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))

_load_dotenv()

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel

import retriever as rt
import llm_backend as llm

app = FastAPI(title="연구 데이터 RAG 챗봇")

RETRIEVER = None


@app.on_event("startup")
def _startup():
    global RETRIEVER
    # 문서 인덱스가 없으면 자동 생성
    if not os.path.exists(rt.INDEX_PATH):
        import ingest
        print("문서 인덱스가 없어 새로 생성합니다...")
        ingest.build_index()
    print("데이터/인덱스 로딩 중...")
    RETRIEVER = rt.Retriever()
    print(f"표 {len(RETRIEVER.tables)}개, 문서청크 {len(RETRIEVER.records)}개 로딩 완료.")
    print(f"답변 백엔드: {llm.get_backend_name()}")


class ChatRequest(BaseModel):
    message: str
    top_k: int = 3


class ChatResponse(BaseModel):
    reply: str
    backend: str
    table_results: list
    doc_sources: list


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    table_results = RETRIEVER.query_tables(req.message)
    doc_results = RETRIEVER.search_docs(req.message, top_k=req.top_k)
    overview = RETRIEVER.table_overview()

    reply = llm.answer(req.message, table_results, doc_results, overview)

    return ChatResponse(
        reply=reply,
        backend=llm.get_backend_name(),
        table_results=table_results,
        doc_sources=[{"source": d["source"], "score": round(d["score"], 3)}
                     for d in doc_results],
    )


@app.get("/health")
def health():
    return {"tables": list(RETRIEVER.tables.keys()),
            "doc_chunks": len(RETRIEVER.records),
            "backend": llm.get_backend_name()}


@app.get("/", response_class=HTMLResponse)
def index():
    return FileResponse(os.path.join(os.path.dirname(__file__), "static", "index.html"))
