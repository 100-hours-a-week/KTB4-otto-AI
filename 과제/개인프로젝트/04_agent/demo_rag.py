"""otto_gpt(라우터) + 03_rag(지식) 결합 데모.

지식이 필요한 질문 → otto 가 search 로 라우팅 → RAG 가 근거 기반 답변.
계산/날씨 → 해당 도구. 그 외 → 직접 답변.

선행: 03_rag 의 FastAPI 를 띄워둘 것.
    cd ../03_rag/langchain_rag && uvicorn app.api:app --port 8000
실제 otto 대신 mock 을 쓰려면 demo.py 의 MODEL_OUTPUTS 처럼 generate_fn 을 주입.
"""
import os

from agent import Agent
from tools import rag_registry

# 실제 otto_gpt 로 돌리려면:
#   from otto_model import OttoModel
#   gen = OttoModel("/content/drive/MyDrive/otto_gpt").generate_fn
# 여기서는 라우팅을 흉내내는 mock 으로 구조만 보여준다.
ROUTES = {
    "어댑터즈 구독료 얼마야?": 'search(검색어="어댑터즈 구독료")',
    "부산 날씨 어때?": 'weather(도시="부산")',
    "12*7 계산해줘": 'calculator(수식="12*7")',
}


def mock_otto(prompt: str) -> str:
    q = prompt.split("### 지시:\n", 1)[-1].split("\n", 1)[0].strip()
    return ROUTES.get(q, "잘 모르겠어요.")


if __name__ == "__main__":
    os.environ.setdefault("RAG_API", "http://127.0.0.1:8000/query")
    agent = Agent(generate_fn=mock_otto, tools=rag_registry())
    for q in ROUTES:
        r = agent.run(q)
        print(f"Q: {q}\n   [{r['type']}/{r.get('tool')}] {r['answer']}\n")
