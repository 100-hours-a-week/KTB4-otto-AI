"""
한국어 챗봇 FastAPI 서버 (과제 5-3)
====================================
사전학습 한국어 GPT 모델(KoGPT2)을 불러와, 입력 문장에 대한 응답을 생성하고
웹(브라우저) 및 REST API 로 제공한다.

- 다음 토큰 예측 (5-1):  kogpt2_chatbot.predict_next_token
- 토큰 생성을 반복하여 문장 완성 (5-2): kogpt2_chatbot.generate_reply
- FastAPI 웹 서비스 (5-3): 아래 엔드포인트 + static/index.html

실행:
    python3 -m uvicorn app:app --reload
    # 채팅 UI:   http://127.0.0.1:8000
    # API 문서:  http://127.0.0.1:8000/docs
"""

import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel

import kogpt2_chatbot as bot

app = FastAPI(title="한국어 챗봇 (KoGPT2)",
              description="사전학습 한국어 GPT 모델 기반 챗봇")


@app.on_event("startup")
def _startup():
    bot.load()   # 서버 시작 시 모델 1회 로딩


# ---- 요청/응답 스키마 ----
class ChatRequest(BaseModel):
    message: str
    max_new_tokens: int = 60
    temperature: float = 0.8


class ChatResponse(BaseModel):
    reply: str


# ---- API: 챗봇 응답 (5-2) ----
@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    reply = bot.generate_reply(
        req.message,
        max_new_tokens=req.max_new_tokens,
        temperature=req.temperature,
    )
    return ChatResponse(reply=reply)


# ---- API: 다음 토큰 1개만 예측 (5-1 확인용) ----
@app.get("/next-word")
def next_word(text: str, temperature: float = 0.8):
    token = bot.predict_next_token(text, temperature)
    return {"input": text, "next_token": token}


# ---- 웹 UI (5-3) ----
@app.get("/", response_class=HTMLResponse)
def index():
    html_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    return FileResponse(html_path)
