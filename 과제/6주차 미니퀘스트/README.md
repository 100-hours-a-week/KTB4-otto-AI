# Gemini RAG 파이프라인 (구축 → 평가 → 배포)

Gemini API를 LLM으로 사용하여 **문서 로딩부터 응답 생성까지** RAG 아키텍처를 구축하고,
**RAGAS**로 파이프라인을 평가하며, **FastAPI**로 REST API로 배포하는 프로젝트입니다.

## 1. 아키텍처

```
                 ┌──────────── 인덱싱 (오프라인) ────────────┐
  data/*.md/pdf → 로딩 → 청킹 → Gemini 임베딩 → FAISS 인덱스 저장
                 └──────────────────────────────────────────┘

                 ┌──────────── 질의 (온라인) ───────────────┐
  질문 → 임베딩 → FAISS 유사도 검색(top-k) → 프롬프트 구성 →
        Gemini(gemini-1.5-flash) 생성 → 답변 + 출처
                 └──────────────────────────────────────────┘
```

| 단계 | 구현 파일 | 사용 기술 |
|------|-----------|-----------|
| 문서 로딩/청킹 | [app/document_loader.py](app/document_loader.py) | LangChain Loader, RecursiveCharacterTextSplitter |
| 임베딩/인덱싱 | [app/vector_store.py](app/vector_store.py) | Gemini `text-embedding-004`, FAISS |
| 검색+생성 | [app/rag_pipeline.py](app/rag_pipeline.py) | LCEL 체인, `gemini-1.5-flash` |
| 평가 | [evaluation/evaluate.py](evaluation/evaluate.py) | RAGAS (LLM-as-judge: Gemini) |
| 배포 | [app/main.py](app/main.py) | FastAPI, uvicorn |

## 2. 설치

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# .env 파일을 열어 GOOGLE_API_KEY 를 입력 (https://aistudio.google.com/app/apikey)
```

## 3. 인덱스 구축 & 빠른 테스트 (CLI)

```bash
python cli.py --build          # data/ 문서를 임베딩하여 FAISS 인덱스 생성
python cli.py "RAG가 뭐야?"     # 단일 질문
python cli.py                  # 대화형 모드
```

## 4. RAGAS 평가

```bash
python -m evaluation.evaluate
```

`evaluation/eval_dataset.json`의 질문/정답 쌍을 파이프라인에 흘려보낸 뒤,
다음 4개 지표를 계산해 콘솔과 `evaluation/ragas_result.csv`에 출력합니다.

- **faithfulness** — 답변이 검색 문맥에 충실한가 (환각 여부)
- **answer_relevancy** — 답변이 질문과 관련 있는가
- **context_precision** — 검색 문맥 중 유용한 비율
- **context_recall** — 정답을 뒷받침하는 문맥이 충분히 검색됐는가

## 5. FastAPI 배포

```bash
uvicorn app.main:app --reload --port 8000
```

- Swagger UI: http://localhost:8000/docs
- 엔드포인트:
  - `GET  /health` — 헬스 체크
  - `POST /reindex` — 문서 재인덱싱
  - `POST /query` — RAG 질의

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "RAGAS의 네 가지 핵심 지표는?"}'
```

응답 예시:
```json
{
  "question": "RAGAS의 네 가지 핵심 지표는?",
  "answer": "Faithfulness, Answer Relevancy, Context Precision, Context Recall 입니다.",
  "contexts": ["..."],
  "sources": ["gemini_eval.md"]
}
```

### 무료 등급(Free Tier) 할당량 주의
Google AI Studio 무료 키는 모델별 **분당/일일 요청 한도**가 매우 낮습니다
(예: `gemini-2.5-flash` ≈ 분당 5 / 일일 20요청). RAGAS는 한 문항당 여러 번의
심판 LLM 호출을 하므로 무료 키로는 금방 한도(`429 ResourceExhausted`)에 걸립니다.
이를 위해 `evaluate.py`는 다음 환경변수를 지원합니다.

| 환경변수 | 기본 | 설명 |
|----------|------|------|
| `EVAL_LIMIT` | 0(전체) | 평가할 문항 수 제한 |
| `EVAL_DELAY` | 0 | 파이프라인 질의 사이 대기(초) |
| `RAGAS_JUDGE_MODEL` | 채팅 모델 | 심판 LLM 모델 |
| `RAGAS_MAX_WORKERS` | 1 | 동시 호출 수(낮을수록 안전) |

```bash
# 무료 등급에서 소수 문항만 천천히 평가
EVAL_LIMIT=2 EVAL_DELAY=14 RAGAS_MAX_WORKERS=1 python -m evaluation.evaluate
```

전체 데이터셋을 안정적으로 평가하려면 Google Cloud 프로젝트에 **결제(billing)를 활성화**해
유료 등급 한도를 쓰는 것을 권장합니다. 일일 한도 소진 시 다음 날(태평양 시간 자정 기준)
리셋됩니다.

## 6. 커스터마이징
- 자신의 문서를 `data/`에 넣고 `python cli.py --build` 로 재인덱싱하세요.
- 청크 크기·top-k·모델은 `.env`(또는 [app/config.py](app/config.py))에서 조정합니다.
