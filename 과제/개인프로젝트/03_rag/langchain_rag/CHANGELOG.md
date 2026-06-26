# CHANGELOG — 03_rag/langchain_rag

버전 규칙은 루트 [VERSIONING.md](../../VERSIONING.md) 참고. 최신 버전이 맨 위.

## v5 — RAGAS 평가 하네스 (2026-06-24)
- **RAGAS 표준 4대 지표** 도입: Faithfulness / Answer Relevancy / Context Precision / Context Recall.
  → 이후 모든 성능 업그레이드를 "몇 점 → 몇 점"으로 측정·증명하는 토대(baseline).
- `evaluation/eval_ragas.py` 신규. 평가자(judge) LLM/임베딩은 우리 스택과 동일하게 Gemini 주입.
- 호환성 우회: RAGAS 0.4.3 이 사라진 `langchain_community.chat_models.vertexai` 를 import 하는
  버그 → 스크립트 상단에서 빈 shim 으로 우회(우리는 Gemini 직접 주입이라 미사용).
- 검증: 설치(3.14, langchain 1.x 무충돌)·import·dataset 로드·judge/메트릭 배선 OK.
  ⚠ **baseline 실측은 미완** — Gemini chat 무료티어 일일 20회 소진(429). quota 리셋(태평양 자정)/유료 키 시
  `python -m evaluation.eval_ragas --limit 3` 으로 실행. (지표 4종은 문항당 다회 호출이라 호출량 큼)

## v4 — 대화 기록 트리밍 (2026-06-24)
- **`trim_messages`** 로 프롬프트에 넣는 기록을 '최근 N개'(`history_window`=6, 약 3턴)로 제한.
  → 대화가 길어져도 매 턴 토큰 폭증/컨텍스트 초과로 깨지는 잠재 버그 차단.
- `strategy="last"`, `token_counter=len`(메시지 개수 기준), `start_on="human"`(human/ai 쌍 정렬).
- 체인 진입부에서 트리밍 → 재작성(contextualize)·답변 단계가 모두 제한된 기록만 사용.
- 검증(오프라인): 10개 메시지 → 최근 6개(질문2~4)만 유지, human 경계 시작 확인.
- 참고: langchain 1.x 는 `RunnableWithMessageHistory` 를 deprecated(LangGraph 권장)로 안내하나,
  커리큘럼(06/17) 학습 항목이라 그대로 유지. 동작 정상.

## v3 — 멀티턴 대화 (2026-06-24)
- **`RunnableWithMessageHistory`** 로 session_id 별 대화 기록 유지 (`InMemoryChatMessageHistory`).
- **history-aware 질문 재작성**: 후속 질문("그건 얼마야?")을 직전 대화로 보강해 독립형 질문으로 변환 후 검색.
- **`RunnableBranch`** 로 첫 턴(기록 없음)에는 재작성 LLM 호출을 건너뜀(비용 절약).
- 답변 프롬프트에 `MessagesPlaceholder("chat_history")` 추가.
- API: `POST /chat`(session_id), `POST /chat/reset` 추가. `cli.py` 대화형 모드도 멀티턴화(reset 명령).
- 검증(오프라인, 가짜 LLM+진짜 retriever): 턴1 종단 동작 + 기록 2개 저장 + 후속질문 재작성("그건 얼마야?"→"어댑터즈 월 구독료는 얼마인가요?") + reset 확인.
  ⚠ 라이브 임베딩 검색은 당시 Gemini 임베딩 500 INTERNAL(서버측 장애)로 미완 → 복구 후 재확인 필요.

## v2 — Python 3.14 대응 (2026-06-24)
- langchain 0.3.x pin 이 tokenizers 빌드 실패로 3.14 미지원 → **langchain 1.x 스택으로 상향**
  (langchain 1.3.11, langchain-core 1.4.8, langchain-chroma 1.1.0, chromadb 1.5.9 등). 코드 무수정 동작.
- 3.14 실동작 확인: `ingest`(청크 5개 인덱싱), `cli.py` 단일 쿼리 정답+출처, FastAPI `GET /health`·`POST /query` 200 OK.
- ⚠ Gemini 무료티어 `gemini-2.5-flash-lite` 일일 한도가 **20건/일**로 확인됨(429 RESOURCE_EXHAUSTED). Dataset 평가는 코드 경로는 정상이나 quota 소진 시 중단됨.

## v1 — 베이스라인 (2026-06-24)
- 통합 시점 상태. LangChain LCEL RAG + FastAPI + LangSmith 평가 (Gemini 백엔드).
