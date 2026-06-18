# RAG 챗봇 (ChromaDB)

챗봇에 RAG(Retrieval-Augmented Generation) 아키텍처를 적용한 버전.
sentence-transformers 임베딩 + ChromaDB 벡터 검색을 사용한다.

## 학습 방식
- 파라메트릭: 모델 가중치에 지식 저장 (직접 파인튜닝 — `finetune_v2_colab.ipynb`)
- 논파라메트릭: 외부 벡터DB 검색 (ChromaDB RAG — `rag_pipeline.py`)

## 파이프라인
```
문서 → 청킹 → 임베딩 → ChromaDB 저장
질문 → 임베딩 → 유사도 검색 → 프롬프트 보강 → LLM 답변
```

## 실행
```bash
pip install chromadb sentence-transformers transformers torch fastapi "uvicorn[standard]"
cp .env.example .env
python3 build_db.py
python3 -m uvicorn app:app --reload   # http://127.0.0.1:8000
```

## LLM 백엔드 (`LLM_BACKEND`)
| 값 | 설명 |
|---|---|
| `finetuned` (기본) | 직접 파인튜닝한 모델 (`FINETUNED_MODEL_PATH`) |
| `local` | 검색 문서를 정리해 답함 (환각 없음) |
| `kogpt2` | 사전학습 KoGPT2 |
| `claude` | `ANTHROPIC_API_KEY` 설정 시 Claude |

## 파인튜닝 모델 학습
`finetune_v2_colab.ipynb` 를 Colab(GPU)에서 실행해 polyglot-ko-1.3b 를 LoRA 로 파인튜닝하고
HuggingFace Hub 에 업로드한다. 그 모델 이름을 `FINETUNED_MODEL_PATH` 에 지정한다.

## 배포
`../hf_space/` 의 파일로 HuggingFace Space(Gradio)에 배포하면 파인튜닝 모델을 웹에서 사용할 수 있다.

## 구성
```
rag_chroma/
├── rag_pipeline.py     # 청킹·임베딩·ChromaDB·검색
├── generator.py        # 프롬프트 보강 + LLM (finetuned/local/kogpt2/claude)
├── build_db.py
├── finetune_v2_colab.ipynb
├── docs/               # 지식 문서
└── static/index.html
```
