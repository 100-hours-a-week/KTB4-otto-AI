# 연구 데이터 RAG 챗봇

로컬 데이터(표 CSV/Excel + 문서 PDF/txt/md)에 접근해, 질문에 대해 실제 계산값과
문서 근거를 바탕으로 답하는 RAG 챗봇.

## 동작
```
질문 → retriever ( 문서: 임베딩 벡터검색 / 표: pandas 계산 )
     → llm_backend ( 근거 기반 답변 생성, local 또는 claude )
     → 답변 + 출처
```

## 구성
```
rag/
├── ingest.py          # 문서 → 청크 → 임베딩 → index/ 저장
├── retriever.py       # 벡터검색 + pandas 표 계산
├── llm_backend.py     # 답변 생성 (local / claude)
├── rag_app.py         # FastAPI 서버
├── static/index.html  # 채팅 UI
└── data/              # tables/ (CSV) + docs/ (문서)
```

## 실행
```bash
pip install sentence-transformers pandas openpyxl anthropic fastapi "uvicorn[standard]"
python3 ingest.py                          # 문서 인덱싱
python3 -m uvicorn rag_app:app --reload    # http://127.0.0.1:8000
```

## 데이터 추가
- 표: `data/tables/` 에 `.csv`/`.xlsx`
- 문서: `data/docs/` 에 `.md`/`.txt`/`.pdf` 넣고 `python3 ingest.py`

## API
| 메서드 | 경로 | 설명 |
|---|---|---|
| POST | `/chat` | 답변 + 표계산결과 + 문서출처 |
| GET | `/health` | 로딩 상태 |
