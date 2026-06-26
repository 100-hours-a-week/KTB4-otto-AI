"""완전 오프라인 에이전트 데모 (맥에서 지금 바로 실행 — Gemini/Colab/서버 불필요).

otto 라우팅은 mock 으로 흉내내고, 도구는 실제 동작:
  - calculator : 실제 계산
  - rag        : 서버 없으니 로컬 문서 검색(local_rag)으로 폴백 → 근거 기반 답변
  - weather/search : 목업

실제 otto_gpt 로 라우팅하려면 demo_otto / colab_agent_demo 참고.
"""
from agent import Agent

# otto 가 각 질문을 어떻게 라우팅하는지(실측 기반) 흉내
ROUTES = {
    "어댑터즈 구독료 얼마야?": 'rag(질문="어댑터즈")',
    "부트캠프 환불 정책 알려줘": 'rag(질문="환불")',
    "345+678 얼마야?": 'calculator(수식="346+679")',   # 모델 인자 틀려도 보정됨
    "부산 날씨 어때?": 'weather(도시="부산")',
    "인공지능이 뭐야?": 'rag(질문="인공지능")',          # 문서에 없음 → 정직하게 답
}


def mock_otto(prompt: str) -> str:
    q = prompt.split("### 지시:\n", 1)[-1].split("\n", 1)[0].strip()
    return ROUTES.get(q, "잘 모르겠어요.")


if __name__ == "__main__":
    agent = Agent(generate_fn=mock_otto)
    for q in ROUTES:
        r = agent.run(q)
        print(f"Q: {q}")
        if r["type"] == "tool":
            if r.get("model_args") != r.get("args"):
                print(f"   인자보정: {r['model_args']} → {r['args']}")
            print(f"   [{r['tool']}] {r['answer']}")
        else:
            print(f"   {r['answer']}")
        print()
