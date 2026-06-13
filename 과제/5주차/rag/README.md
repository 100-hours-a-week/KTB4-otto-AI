# 연구 데이터 RAG 챗봇

내 **로컬 데이터(표 CSV/Excel + 문서 PDF/txt/md)** 에 접근해, 질문에 대해
**실제 계산값**과 **문서 근거**를 바탕으로 답하는 챗봇입니다.

기본은 **API 키 없이 로컬·무료**로 동작하고, `ANTHROPIC_API_KEY` 를 넣으면
**Claude** 가 자동으로 더 자연스럽게 답하도록 설계되어 있습니다(교체 가능).

## 동작 구조 (RAG)
```
질문
 └─> retriever.py
       ├─ 문서: 임베딩 벡터검색으로 관련 청크 top-k 검색 (ko-sroberta)
       └─ 표:   pandas 로 실제 계산 (평균/최대/최소/합계/표준편차/개수)
 └─> llm_backend.py  (근거를 바탕으로 답변 생성)
       ├─ local  : 근거를 정확히 정리 (환각 없음, API 불필요) — 기본
       └─ claude : ANTHROPIC_API_KEY 있으면 자연어로 답변
 └─> 답변 + 출처
```
> 검색·계산은 100% 로컬이라 **항상 정확한 값**을 사용하고, LLM 은 그 근거를
> 풀어 쓰는 역할만 합니다(없는 수치를 지어내지 않음).

## 구조
```
rag/
├── data/
│   ├── tables/experiment_results.csv   # 표 데이터 (샘플: 촉매농도-수율 실험)
│   └── docs/experiment_notes.md        # 문서 (샘플: 실험 노트)
├── ingest.py          # 문서 → 청크 → 임베딩 → index/ 저장
├── retriever.py       # 벡터검색 + pandas 표 계산
├── llm_backend.py     # 답변 생성 (local / claude 자동 선택)
├── rag_app.py         # FastAPI 서버
├── static/index.html  # 채팅 UI
└── index/             # 생성된 임베딩 인덱스
```

## 사용법
```bash
# 1) 의존성 설치
pip3 install sentence-transformers pandas openpyxl anthropic fastapi "uvicorn[standard]"

# 2) (문서가 있으면) 인덱스 생성
python3 ingest.py

# 3) 서버 실행
python3 -m uvicorn rag_app:app --reload
#  채팅: http://127.0.0.1:8000   /  상태: http://127.0.0.1:8000/health
```

### 내 데이터 넣는 법
- **표**: `data/tables/` 에 `.csv` 또는 `.xlsx` 를 넣으면 자동 인식 (재시작만 하면 됨).
- **문서**: `data/docs/` 에 `.md/.txt/.pdf` 를 넣고 `python3 ingest.py` 로 다시 인덱싱.
  (PDF 는 `pip3 install pypdf` 필요)

### Claude 로 답변 품질 높이기
1. https://console.anthropic.com → **API Keys → Create Key** 에서 `sk-ant-...` 키 발급
2. `.env` 파일을 만들고 키를 넣기:
   ```bash
   cp .env.example .env
   # .env 를 열어 ANTHROPIC_API_KEY 값에 본인 키를 붙여넣기
   ```
3. 서버 실행 → 자동으로 Claude 백엔드 사용:
   ```bash
   python3 -m uvicorn rag_app:app --reload
   ```
- 키가 없으면 자동으로 `local` 백엔드로 동작합니다(설치 그대로 무료).
- 답변 화면 우측 상단 `backend:` 배지로 현재 엔진(local/claude)을 확인할 수 있습니다.
- 모델은 `.env` 의 `CLAUDE_MODEL` 로 변경 가능(기본 `claude-sonnet-4-6`, 더 똑똑하게는 `claude-opus-4-8`).

### 내 데이터를 한 번에 가져오기
구글 드라이브 동기화 폴더나 다운로드 폴더에서 파일을 자동 분류해 가져옵니다:
```bash
python3 import_data.py "/경로/실험데이터폴더"
```
- `.csv/.xlsx` → 표로, `.md/.txt/.pdf` → 문서로 자동 분류 후 인덱스 재생성.

## 질문 예시
- `high 그룹 yield_percent 평균은?`  → 표에서 실제 계산 (74.62%)
- `yield_percent 최댓값은?`          → 80.1%
- `control 그룹 purity_percent 평균` → 88.2%
- `최적 반응 조건이 뭐야?`           → 문서에서 근거 검색
- `촉매 농도가 수율에 어떤 영향을 줘?` → 문서 + 표 결합

## API
| 메서드 | 경로 | 설명 |
|---|---|---|
| POST | `/chat` | `{"message": "..."}` → 답변 + 표계산결과 + 문서출처 |
| GET | `/health` | 로딩된 표/문서청크 수, 현재 backend |
