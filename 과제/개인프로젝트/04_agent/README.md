# 04_agent — 도구 쓰는 에이전트

`02_otto_gpt` 가 학습한 **도구 호출**을 실제로 실행하는 에이전트.
모델은 **라우터**(어떤 도구를 어떤 인자로 쓸지 결정), 에이전트는 **파싱 → 실행 → 응답**.

```
질문 ──▶ [otto_gpt] ──▶ 출력
                         ├─ 'weather(도시="부산")' ─▶ 파싱 ─▶ weather 실행 ─▶ 관찰 ─▶ 응답
                         └─ 일반 문장 ──────────────────────────────────▶ 직접 답변
```

## 구성
| 파일 | 역할 |
|---|---|
| `parser.py` | `tool(arg="값")` 문자열 → `(이름, kwargs)` 파싱 |
| `tools.py` | 도구 레지스트리. `calculator`(실제 계산) / `weather`·`search`(목업) |
| `agent.py` | 실행 루프 (`Agent.run(question)`) |
| `model.py` | otto-GPT 모델 정의 (추론용) |
| `otto_model.py` | 체크포인트 로드 + `generate_fn` 제공 |
| `demo.py` | 모델 없이 루프 검증 (실제 모델 출력 문자열 주입) |

## FastAPI 서버 (권장 — 어디서나 실행)
```bash
uvicorn api:app --port 8001
curl -X POST localhost:8001/agent -H 'Content-Type: application/json' \
     -d '{"question":"어댑터즈 구독료 얼마야?"}'
# → {"type":"tool","tool":"rag","answer":"월 구독료는 1만 9천 원이며..."}
```
otto 체크포인트 없으면 `local_router`(룰 기반)로, 있으면(`OTTO_PROJECT_DIR` 지정) 실제 모델로 라우팅.

## 실행 (스크립트)

완전 오프라인 데모 (맥에서 바로):
```bash
python demo_offline.py
```

모델 없이 루프만 확인:
```bash
python demo.py
```

실제 otto_gpt 로 (Colab 또는 ckpt 있는 로컬):
```python
from otto_model import OttoModel
from agent import Agent
gen = OttoModel("/content/drive/MyDrive/otto_gpt").generate_fn
agent = Agent(generate_fn=gen)
print(agent.run("부산 날씨 어때?"))   # weather 실행 → 결과
print(agent.run("12*7 계산해줘"))     # 84
```

## 설계 메모 / 다음
- **모델은 라우터**: 57M otto_gpt 는 지식은 약하나 도구 호출은 정확(2026-06-24 실측 3/3).
  지식이 필요한 질문은 도구(`search`)나 `03_rag` 로 외주하는 구조가 적합.
- 도구 결과를 자연어로 다시 풀어주는 **observation→answer 합성**은 아직 템플릿.
  추후 `02_otto_gpt` 에 '관찰→답변' 데이터를 추가 학습하면 `agent._synthesize` 를 2차 모델
  호출로 교체.
- 도구 **과트리거**(일반 질문을 도구로 오라우팅) 완화는 `02_otto_gpt` v4 에서 데이터 재균형으로.
- ✅ **`03_rag` 도구화 완료(v2)**: `rag_search` 가 RAG FastAPI 호출, `rag_registry()` 로 `search`→RAG 바인딩.
- 멀티스텝(도구 결과 보고 다음 도구 호출)은 이후 버전.

## RAG 도구 사용
```bash
# 1) 03_rag 서버 기동
cd ../03_rag/langchain_rag && uvicorn app.api:app --port 8000
# 2) 에이전트는 rag_registry() 로 search 를 RAG 에 바인딩
python demo_rag.py
```
