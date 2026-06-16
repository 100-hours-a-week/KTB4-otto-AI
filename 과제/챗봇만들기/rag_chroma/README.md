# RAG 챗봇 (ChromaDB) — 파라메트릭 + 논파라메트릭 학습

우리가 만든 챗봇에 **RAG(Retrieval-Augmented Generation)** 아키텍처를 적용하고,
**두 가지 학습 방식**을 모두 갖춘 버전입니다.

## 파라메트릭 학습 vs 논파라메트릭 학습
| | 파라메트릭(parametric) | 논파라메트릭(non-parametric) |
|---|---|---|
| 지식 저장 위치 | **모델 가중치 안** | **외부 벡터DB(ChromaDB)** |
| 방법 | **파인튜닝** (가중치 갱신) | **RAG 검색** (가중치 불변) |
| 비유 | 머리에 외워서 답함 | 책을 찾아보고 답함 |
| 구현 | `finetune_kogpt2_colab.ipynb` | `rag_pipeline.py` |
| 새 지식 추가 | 재학습 필요 | 문서만 추가 |

이 챗봇은 **파인튜닝한 모델(파라메트릭)** 에 **RAG로 검색한 문서(논파라메트릭)** 를
함께 넣어 답하도록 결합할 수 있습니다 (`LLM_BACKEND=finetuned`).

수업 스택 그대로 **sentence-transformers(임베딩) + ChromaDB(Vector DB)** 를 사용합니다.

## 수업 파이프라인 ↔ 코드 매핑
| 수업 단계 | 구현 위치 |
|---|---|
| 문서 로딩 · 전처리 | `rag_pipeline.load_documents`, `preprocess` |
| **청킹** (Delimiter `##` 기준 + Fixed-size 보조, overlap) | `rag_pipeline.chunk_text` |
| **임베딩** (sentence-transformers, MiniLM 계열) | `rag_pipeline.get_embedding_function` |
| **Vector DB 저장** (ChromaDB, `hnsw:space=cosine`) | `rag_pipeline.build_index` |
| 질문 임베딩 · **유사도 검색** (코사인/HNSW) | `rag_pipeline.search` → `collection.query` |
| **프롬프트 보강** | `generator.build_prompt` |
| **LLM 답변 생성** | `generator.generate` |
| 웹 서비스 (FastAPI) | `app.py` + `static/index.html` |

## 구조
```
rag_chroma/
├── docs/                  # 지식 문서 (.md) — 챗봇이 검색해 답할 내용
├── rag_pipeline.py        # 청킹·임베딩·ChromaDB 저장·유사도 검색 (RAG 핵심)
├── generator.py           # 프롬프트 보강 + LLM 답변 (local/kogpt2/claude)
├── build_db.py            # 인덱싱 실행 스크립트
├── app.py                 # FastAPI 서버
├── static/index.html      # 채팅 UI
└── chroma_db/             # ChromaDB 영구 저장 (자동 생성)
```

## 두 가지 모드 (`RAG_SOURCE`)
| 모드 | 검색 소스 | 설명 |
|---|---|---|
| `web` | **실시간 웹** | Gemini 2.5 Flash 의 Google 검색으로 **무엇이든** 답함 (최신 정보 가능) |
| `docs` | 로컬 문서(ChromaDB) | `docs/` 에 넣은 내 문서 안에서만 정확히 답함 |

### 웹 모드 (무엇이든 물어보세요)
```bash
cp .env.example .env          # .env 에 GEMINI_API_KEY 채우기
# (키 발급: https://aistudio.google.com/app/apikey)
python3 -m uvicorn app:app --reload     # RAG_SOURCE=web 이 .env 에 있음
```
질문 → Gemini 가 Google 검색 → 근거(웹 출처)와 함께 한국어로 답변.

## 사용법 (로컬 문서 모드)
```bash
# 1) 의존성 설치
pip3 install chromadb sentence-transformers fastapi "uvicorn[standard]"

# 2) 문서 인덱싱 (ChromaDB 저장) — 최초 1회
python3 build_db.py

# 3) 서버 실행
python3 -m uvicorn app:app --reload
#  채팅:  http://127.0.0.1:8000
```
> 서버는 인덱스가 없으면 시작 시 자동으로 만들어 줍니다.

## LLM 백엔드 선택 (환경변수 `LLM_BACKEND`)
| 값 | 학습 방식 | 설명 |
|---|---|---|
| `local` (기본) | 논파라메트릭만 | 검색된 근거 문서를 정리해 답함 — 환각 없음, 추가 설치 불필요 |
| `kogpt2` | 사전학습 | 사전학습 KoGPT2 로 생성 (`~/챗봇/kogpt2_chatbot.py`) |
| `finetuned` | **파라메트릭+논파라메트릭** | 파인튜닝한 KoGPT2 + RAG 문서로 생성 |
| `claude` | 논파라메트릭 | `ANTHROPIC_API_KEY` 가 있으면 Claude 로 자연스럽게 생성 |
- 키가 있으면 자동으로 `claude`, 없으면 `local` 로 동작합니다.

## 파라메트릭 학습(파인튜닝) 사용법
1. **Colab 에서 파인튜닝** — `finetune_kogpt2_colab.ipynb` 를 Colab(GPU)에 올려 실행.
   HuggingFace 한국어 데이터셋(KoAlpaca)으로 KoGPT2 를 학습합니다.
2. **학습된 모델 가져오기** — HF Hub 에 올리거나 zip 으로 받아 로컬에 둠.
3. **챗봇에 연결**:
   ```bash
   export FINETUNED_MODEL_PATH=your-username/kogpt2-koalpaca   # HF 이름
   #   또는 로컬 경로:  export FINETUNED_MODEL_PATH=./kogpt2-finetuned
   export LLM_BACKEND=finetuned
   python3 -m uvicorn app:app --reload
   ```
> 이러면 **파인튜닝된 모델(파라메트릭)** 이 **RAG 검색 문서(논파라메트릭)** 를 참고해 답합니다.

## 핵심 개념 (수업 정리)
- **RAG**: 질문을 LLM 에 바로 넣지 않고, 관련 문서를 먼저 검색해 프롬프트에 넣어 답하게 하는 구조.
- **ChromaDB**: 임베딩 벡터 + 원문 + 메타데이터를 함께 저장하고 HNSW 인덱스로 빠르게 유사도 검색하는 Vector DB.
- **코사인 유사도**: 질문 벡터와 문서 벡터의 방향 유사도. ChromaDB 의 distance(거리, 작을수록 유사)를 `1 - distance` 로 변환해 사용.

## 내 문서로 바꾸기
`docs/` 에 `.md`/`.txt` 를 넣고 `python3 build_db.py` 를 다시 실행하면 됩니다.

## API
| 메서드 | 경로 | 설명 |
|---|---|---|
| POST | `/chat` | `{"message":"..."}` → 답변 + 검색 출처 |
| GET | `/search?q=...` | 검색 단계만 확인 (RAG 동작 시연용) |
