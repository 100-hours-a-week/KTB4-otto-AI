# 버전 관리 규칙

이 워크스페이스는 단계(01~04)마다 **독립적으로** 버전을 올린다.
아직 git 은 쓰지 않으므로(추후 도입), 현재는 **각 모듈의 `CHANGELOG.md`** 가
버전의 단일 기준(source of truth)이다.

## 규칙
1. **폴더를 복사하지 않는다** (`v1/`, `v2/` 식 금지). 버전은 CHANGELOG 로 기록.
2. 버전 이름: `<모듈>-v<n>` — 예) `03_rag-v2`.
3. 기능을 의미있게 바꿀 때마다 해당 모듈 `CHANGELOG.md` 맨 위에 한 줄 추가.
4. 모델 가중치 등 바이너리는 **파일명에 버전**을 넣는다 — 예) `otto_gpt_v2.pt`.
   무엇이/왜 바뀌었는지는 CHANGELOG 에 기록.
5. git 도입 시: 각 CHANGELOG 의 버전을 `git tag <모듈>-v<n>` 으로 그대로 옮긴다.

## 현재 버전 (요약)

| 모듈 | 현재 | 상태 |
|---|---|---|
| 01_next_word_model | v2 | Python 3.14 대응 (KoGPT2 FastAPI 실동작 확인) |
| 02_otto_gpt | v6 | 모델 스케일업 57M→318M (GPT-2 medium급, 파라미터로 천장↑) |
| 03_rag/langchain_rag | v5 | RAGAS 평가 하네스(4대 지표) — 성능 측정 baseline 토대 |
| 04_agent | v8 | 318M 모델 연결 (OttoModel 318M 자동선택) + 환각 안전망 |

> 이 표와 각 CHANGELOG 는 기능을 올릴 때마다 함께 갱신한다.
