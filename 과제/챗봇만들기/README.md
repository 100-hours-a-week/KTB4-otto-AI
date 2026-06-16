# 한국어 챗봇

문장을 입력하면 다음 단어를 예측하고, 이를 autoregressive 하게 반복해 문장을 생성하는
한국어 챗봇. FastAPI 로 웹에서 사용할 수 있다.

## 구성
- `chatbot_model.py`, `train.py` : LSTM 기반 다음 단어 예측 모델 (직접 학습)
- `kogpt2_chatbot.py` : 사전학습 KoGPT2 기반 버전
- `app.py`, `static/index.html` : FastAPI 서버 + 채팅 UI
- `data/corpus.txt`, `artifacts/` : 학습 코퍼스 / 학습된 모델
- `rag/`, `rag_chroma/` : RAG 아키텍처 적용 버전

## 실행
```bash
pip install -r requirements.txt
python3 train.py                       # LSTM 모델 학습 (artifacts/ 저장)
python3 -m uvicorn app:app --reload    # http://127.0.0.1:8000
```

## API
| 메서드 | 경로 | 설명 |
|---|---|---|
| POST | `/chat` | `{"message": "..."}` → 답변 |
| GET | `/next-word?text=...` | 다음 단어 1개 예측 |
