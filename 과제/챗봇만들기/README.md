# 과제 5 — 한국어 챗봇

문장을 넣으면 **다음 토큰(단어)을 예측**하는 모델을 사용하고, 이를 **반복 호출**해
완전한 문장을 만든 뒤, **FastAPI** 로 감싸 웹에서 대화할 수 있는 한국어 챗봇입니다.

두 가지 버전을 함께 제공합니다.
- **KoGPT2 버전 (권장 · 기본)** — SKT 사전학습 한국어 GPT(`skt/kogpt2-base-v2`)를 불러와 진짜 AI처럼 자연스러운 한국어를 생성. 코퍼스에 없는 문장도 답합니다.
- **LSTM 버전 (직접 학습)** — 작은 코퍼스로 다음 단어 예측 모델을 직접 만들어 학습하는 교육용 구현.

## 과제 요구사항 매핑
| 요구사항 | KoGPT2 버전 | LSTM 버전 |
|---|---|---|
| 5-1. 문장 → 다음 단어(토큰) 생성 모델 | `kogpt2_chatbot.predict_next_token` | `chatbot_model.predict_next_word` |
| 5-2. 모델을 반복 호출해 완전한 문장 생성 | `kogpt2_chatbot.generate_reply` | `chatbot_model.generate_sentence` |
| 5-3. FastAPI 로 웹에서 사용 | `app.py` (KoGPT2 사용) + `static/index.html` | 동일 UI |

## 구조
```
챗봇/
├── kogpt2_chatbot.py      # ⭐ KoGPT2 로딩·다음토큰예측·문장생성 (기본 엔진)
├── app.py                 # FastAPI 서버 (KoGPT2 사용)
├── static/index.html      # 채팅 웹 UI
│
├── chatbot_model.py       # (LSTM 버전) 토크나이저·모델·예측/생성 로직
├── train.py               # (LSTM 버전) 직접 학습 → artifacts/ 저장
├── data/corpus.txt        # (LSTM 버전) 한국어 학습 코퍼스
├── artifacts/             # (LSTM 버전) 학습 산출물
└── requirements.txt
```

## 사용법 (KoGPT2 버전 · 권장)
```bash
# 1) 의존성 설치
pip3 install -r requirements.txt

# 2) 웹 서버 실행 (최초 실행 시 모델 ~500MB 자동 다운로드)
python3 -m uvicorn app:app --reload
```
- 채팅 UI: http://127.0.0.1:8000
- API 문서(Swagger): http://127.0.0.1:8000/docs
> 학습이 필요 없습니다. 사전학습 모델을 그대로 불러와 사용합니다.

## API
| 메서드 | 경로 | 설명 |
|---|---|---|
| POST | `/chat` | `{"message": "오늘 기분이 안 좋아요"}` → `{"reply": "..."}` 완전한 문장 응답 (5-2) |
| GET | `/next-word?text=오늘 날씨가` | 다음 토큰 1개만 예측 (5-1 확인용) |

### 동작 원리
1. **다음 토큰 예측 (5-1)**: 입력 문장을 토큰화해 GPT 에 넣고, 마지막 위치의 logits 에 softmax·temperature 샘플링을 적용해 다음 토큰 하나를 고릅니다.
2. **문장 생성 (5-2)**: 다음 토큰 예측을 `max_new_tokens` 번 반복해(`model.generate`) 문장을 완성합니다. 질문-답변 대화 템플릿을 씌워 챗봇처럼 답하도록 유도하고, 반복 억제(repetition_penalty, no_repeat_ngram) 로 품질을 높입니다.
3. **웹 서비스 (5-3)**: FastAPI 가 모델을 1회 로딩해 두고 `/chat` 요청마다 답변을 생성해 반환하며, `static/index.html` 채팅 화면에서 바로 대화할 수 있습니다.

## (참고) LSTM 버전 직접 학습
```bash
python3 train.py        # data/corpus.txt 로 다음 단어 예측 모델 학습 → artifacts/
```
`app.py` 의 `import kogpt2_chatbot as bot` 부분을 `chatbot_model` 기반으로 바꾸면 직접 학습한 모델로도 서빙할 수 있습니다. 코퍼스(`data/corpus.txt`)에 문장을 추가하고 다시 학습하면 응답이 좋아집니다.
