"""에이전트 실행 루프.

모델 = 라우터(도구+인자 결정), 에이전트 = 파싱 -> 도구 실행 -> 응답.

흐름:
  질문 -> [모델] -> 출력
    ├─ 도구 호출이면 -> 파싱 -> 도구 실행 -> 관찰(observation) -> 응답
    └─ 아니면 -> 그 자체가 직접 답변

모델은 `generate_fn(prompt: str) -> str` 형태로 주입한다(otto_gpt, mock, 무엇이든).
이렇게 하면 모델 없이도 루프를 검증할 수 있다.
"""
from __future__ import annotations

from typing import Callable

from extract import extract_args
from parser import parse_tool_call
from tools import REGISTRY

# otto_gpt 멀티태스크 튜닝과 동일한 프롬프트 포맷
PROMPT = "### 지시:\n{q}\n\n### 응답:\n"


class Agent:
    def __init__(self, generate_fn: Callable[[str], str], tools: dict = REGISTRY):
        self.generate_fn = generate_fn
        self.tools = tools

    def run(self, question: str) -> dict:
        raw = self.generate_fn(PROMPT.format(q=question)).strip()
        parsed = parse_tool_call(raw)

        # 1) 도구 호출이 아니면 → 직접 답변
        if parsed is None:
            return {"type": "direct", "raw": raw, "answer": raw}

        name, model_args = parsed

        # 2) 모르는 도구
        if name not in self.tools:
            return {
                "type": "unknown_tool", "raw": raw, "tool": name, "args": model_args,
                "answer": f"알 수 없는 도구를 호출했습니다: {name}",
            }

        # 3) 인자 재추출: 모델의 라우팅은 신뢰, 정밀 인자는 원문에서 보정
        args = extract_args(name, question, model_args)

        # 4) 도구 실행 → 관찰
        observation = self.tools[name](**args)
        return {
            "type": "tool", "raw": raw, "tool": name,
            "model_args": model_args,   # 모델이 낸 (보정 전) 인자
            "args": args,               # 실제 실행에 쓴 (보정 후) 인자
            "observation": observation,
            "answer": self._synthesize(question, observation),
        }

    def _synthesize(self, question: str, observation: str) -> str:
        """도구 결과를 자연어 답변으로. (현재는 템플릿 — 모델이 관찰→답변을
        학습하지 않았으므로. 추후 'observation -> answer' 데이터로 학습하면
        여기서 self.generate_fn 으로 2차 합성하도록 교체)."""
        return observation
