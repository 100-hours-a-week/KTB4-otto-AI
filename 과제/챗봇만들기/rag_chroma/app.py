import os

def _load_dotenv():
    p = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
_load_dotenv()

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel

import rag_pipeline as rag
import generator as gen

app = FastAPI(title="RAG 챗봇 (ChromaDB)")

@app.on_event("startup")
def _startup():
    
    if RAG_SOURCE != "web":
        try:
            rag.get_collection().count()
        except Exception:
            print("ChromaDB 인덱스가 없어 새로 생성합니다...")
            rag.build_index()
    print(f"검색 소스: {RAG_SOURCE} | LLM 백엔드: {'gemini-web' if RAG_SOURCE=='web' else gen.get_backend_name()}")

RAG_SOURCE = os.environ.get("RAG_SOURCE", "docs").lower()

class ChatRequest(BaseModel):
    message: str
    n_results: int = 3

class ChatResponse(BaseModel):
    reply: str
    backend: str
    sources: list

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    
    if RAG_SOURCE == "web":
        reply, sources = gen.answer_gemini_web(req.message)
        return ChatResponse(reply=reply, backend="gemini-web", sources=sources)

    hits = rag.search(req.message, n_results=req.n_results)
    reply = gen.generate(req.message, hits)
    return ChatResponse(
        reply=reply,
        backend=gen.get_backend_name(),
        sources=[{"source": h["source"], "similarity": h["similarity"]} for h in hits],
    )

@app.get("/search")   
def search_only(q: str, n_results: int = 3):
    return {"query": q, "results": rag.search(q, n_results=n_results)}

@app.get("/", response_class=HTMLResponse)
def index():
    return FileResponse(os.path.join(os.path.dirname(__file__), "static", "index.html"))
