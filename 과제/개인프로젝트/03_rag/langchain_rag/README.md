# otto RAG

LangChain + Gemini 기반 RAG 파이프라인. FastAPI REST API 로 제공하고, LangSmith 로
Tracing 및 Dataset 평가를 수행한다.

문서 도메인: 스타트업코드/어댑터즈 서비스 안내 + AI 부트캠프 커리큘럼 (`docs/`).

## 구성

검색·프롬프트·모델·파서가 모두 Runnable 로 LCEL 체인(`rag_chain`)으로 연결된다.

```
질문 ──▶ retriever ──▶ format_docs ──▶ ChatPromptTemplate ──▶ Gemini ──▶ StrOutputParser ──▶ 답변
                 └────────────────────────────────────────────────────▶ 근거 문서/출처
```

| 단계 | 사용 컴포넌트 |
|---|---|
| 문서 로딩 | `TextLoader` / `PyPDFLoader` |
| 청킹 | `RecursiveCharacterTextSplitter` |
| 임베딩 | `GoogleGenerativeAIEmbeddings` |
| 벡터스토어 | `langchain_chroma.Chroma` |
| 프롬프트 | `ChatPromptTemplate` (system/human) |
| LLM | `ChatGoogleGenerativeAI` |
| 파이프라인 | LCEL `retriever | prompt | llm | parser` |

`app/rag_chain.py` 의 `RAGChain` 은 `RunnablePassthrough.assign` 으로 검색을 1회만 하고
그 결과를 답변 생성과 출처 표시에 함께 사용한다.

## 설치 & 실행

```bash
cd langchain_rag
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env        # GOOGLE_API_KEY 입력

python -m app.ingest        # 인덱스 구축

python cli.py "어댑터즈 구독료 얼마야?"
python cli.py               # 대화형 모드
```

## FastAPI

```bash
python -m uvicorn app.api:app --reload --port 8000
# 문서: http://127.0.0.1:8000/docs
```

| 메서드 | 경로 | 설명 |
|---|---|---|
| GET  | `/health`  | 헬스체크 |
| POST | `/query`   | `{"question": "..."}` → 답변 + contexts + sources |
| GET  | `/search?q=...` | 검색만 (retriever 결과) |
| POST | `/reindex` | `docs/` 재임베딩 |

```bash
curl -X POST http://127.0.0.1:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question":"부트캠프 환불 정책 알려줘"}'
```

## LangSmith Tracing + 평가

`.env` 에 키를 넣으면 모든 체인 실행이 LangSmith 에 자동 기록된다.

```
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=lsv2_...        # https://smith.langchain.com 에서 발급
LANGSMITH_PROJECT=otto-rag-langchain
```

평가셋: `evaluation/dataset.jsonl` (질문 / 기준정답 / 기대출처 11문항, '문서에 없음' 케이스 포함).

```bash
python -m evaluation.eval_langsmith            # 로컬 평가
python -m evaluation.eval_langsmith --limit 4  # 앞 4문항만
python -m evaluation.eval_langsmith --langsmith  # LangSmith Dataset 업로드 + 클라우드 평가
```

평가 지표
- **correctness**: Gemini LLM-judge 로 기준정답과 사실 일치 여부 (CORRECT/INCORRECT)
- **source_match**: 기대 출처 문서가 검색 결과에 포함됐는지

> Gemini 무료 티어는 모델별 일일 한도가 다르다(`gemini-2.5-flash`=20/일,
> `gemini-2.5-flash-lite`=1000/일). 평가는 문항당 답변+judge 2콜이 들므로 한도가 큰
> `flash-lite` 를 기본값으로 사용한다. 분당 한도는 `GEMINI_RPM` 으로 조절.

## 구조

```
langchain_rag/
├── app/
│   ├── config.py       # 설정 + LangSmith + RateLimiter
│   ├── ingest.py       # 로딩→청킹→임베딩→Chroma
│   ├── rag_chain.py    # LCEL RAG 체인
│   └── api.py          # FastAPI
├── evaluation/
│   ├── dataset.jsonl
│   └── eval_langsmith.py
├── docs/
├── cli.py
└── requirements.txt
```
