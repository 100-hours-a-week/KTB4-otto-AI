import os

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
