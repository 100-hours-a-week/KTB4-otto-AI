# RAG 챗봇 (ChromaDB / 웹검색)

챗봇에 RAG(Retrieval-Augmented Generation) 아키텍처를 적용한 버전.
sentence-transformers 임베딩 + ChromaDB 벡터 검색을 사용한다.

## 학습 방식
- 파라메트릭: 모델 가중치에 지식 저장 (KoGPT2 파인튜닝 — `finetune_kogpt2_colab.ipynb`)
- 논파라메트릭: 외부 벡터DB 검색 (ChromaDB RAG — `rag_pipeline.py`)

## 파이프라인
```
문서 → 청킹 → 임베딩 → ChromaDB 저장
질문 → 임베딩 → 유사도 검색 → 프롬프트 보강 → LLM 답변
```

## 모드 (`RAG_SOURCE`)
| 모드 | 검색 소스 | 설명 |
|---|---|---|
| `web` | 실시간 웹 | Gemini 2.5 Flash + Google 검색으로 무엇이든 답변 |
| `docs` | 로컬 문서(ChromaDB) | `docs/` 문서 안에서 답변 |

## 실행
```bash
pip install chromadb sentence-transformers google-genai fastapi "uvicorn[standard]"
cp .env.example .env          # GEMINI_API_KEY 채우기
python3 build_db.py           # (docs 모드) ChromaDB 인덱싱
python3 -m uvicorn app:app --reload   # http://127.0.0.1:8000
```

## LLM 백엔드 (`LLM_BACKEND`, docs 모드)
| 값 | 설명 |
|---|---|
| `local` | 검색 문서를 정리해 답함 (환각 없음) |
| `kogpt2` | 사전학습 KoGPT2 |
| `finetuned` | 파인튜닝 KoGPT2 (`FINETUNED_MODEL_PATH`) |
| `claude` | `ANTHROPIC_API_KEY` 설정 시 Claude |

## 구성
```
rag_chroma/
├── rag_pipeline.py     # 청킹·임베딩·ChromaDB·검색
├── generator.py        # 프롬프트 보강 + LLM (local/kogpt2/finetuned/claude/gemini-web)
├── web_search.py
├── build_db.py
├── finetune_kogpt2_colab.ipynb
├── docs/               # 지식 문서
└── static/index.html
```
