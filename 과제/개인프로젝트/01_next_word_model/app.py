import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel

import kogpt2_chatbot as bot

app = FastAPI(title="한국어 챗봇 (KoGPT2)",
              description="사전학습 한국어 GPT 모델 기반 챗봇")

@app.on_event("startup")
def _startup():
    bot.load()   

class ChatRequest(BaseModel):
    message: str
    max_new_tokens: int = 60
    temperature: float = 0.8

class ChatResponse(BaseModel):
    reply: str

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    reply = bot.generate_reply(
        req.message,
        max_new_tokens=req.max_new_tokens,
        temperature=req.temperature,
    )
    return ChatResponse(reply=reply)

@app.get("/next-word")
def next_word(text: str, temperature: float = 0.8):
    token = bot.predict_next_token(text, temperature)
    return {"input": text, "next_token": token}

@app.get("/", response_class=HTMLResponse)
def index():
    html_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    return FileResponse(html_path)
