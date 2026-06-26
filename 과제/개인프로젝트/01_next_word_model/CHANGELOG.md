# CHANGELOG — 01_next_word_model (나만의 모델)

버전 규칙은 루트 [VERSIONING.md](../VERSIONING.md) 참고. 최신 버전이 맨 위.

## v2 — Python 3.14 대응 (2026-06-24)
- 의존성 핀을 3.14 검증 버전으로 상향: torch 2.12.1, transformers 5.12.1, fastapi 0.138.0, pydantic 2.13.4.
- FastAPI 앱(KoGPT2 경로) 3.14 실동작 확인: `GET /next-word`(다음 토큰), `POST /chat`(autoregressive 문장) 모두 200 OK.
- ⚠ LSTM 경로(`chatbot_model.py`/`train.py`)는 tensorflow 3.14 휠 부재로 미설치 → Python ≤3.13 별도 venv 필요. requirements 에 주석 처리.

## v1 — 베이스라인 (2026-06-24)
- 통합 시점 상태. LSTM 다음단어예측 + KoGPT2 + FastAPI 챗봇.
