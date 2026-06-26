"""모델 없이 에이전트 루프를 검증하는 데모.

otto_gpt 가 실제로 내뱉은 출력 문자열을 mock generate_fn 으로 주입해,
파싱 -> 도구 실행 -> 응답 흐름을 그대로 확인한다. (calculator 는 진짜 계산)

실제 모델로 돌리려면 demo_otto.py (otto_gpt_instruct.pt 필요) 참고.
"""
from agent import Agent

# otto_gpt v3 가 실제로 생성한 출력 (2026-06-24 Colab 결과)
MODEL_OUTPUTS = {
    "부산 날씨 어때?": 'weather(도시="부산")',
    "오늘 환율 검색해줘": 'search(검색어="오늘 환율")',
    "12*7 계산해줘": 'calculator(수식="12*7")',
    "인공지능이 뭐야?": "인공지능은 컴퓨터가 사람처럼 학습하고 추론하는 기술입니다.",
}


def mock_generate(prompt: str) -> str:
    # prompt 에서 질문만 추출해 대응 출력 반환
    q = prompt.split("### 지시:\n", 1)[-1].split("\n", 1)[0].strip()
    return MODEL_OUTPUTS.get(q, "(모름)")


if __name__ == "__main__":
    agent = Agent(generate_fn=mock_generate)
    for q in MODEL_OUTPUTS:
        r = agent.run(q)
        print(f"Q: {q}")
        print(f"   [type={r['type']}] 모델출력={r['raw']!r}")
        if r["type"] == "tool":
            print(f"   도구={r['tool']}{r['args']} → 관찰={r['observation']}")
        print(f"   ▶ 답변: {r['answer']}\n")
