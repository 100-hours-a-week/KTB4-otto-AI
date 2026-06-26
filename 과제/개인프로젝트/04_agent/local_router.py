"""오프라인 룰 기반 라우터 (otto 없이도 에이전트가 돌도록).

otto_gpt 가 학습한 라우팅을 규칙으로 흉내낸다 — 어떤 도구를 쓸지만 결정하고,
정확한 인자는 agent 의 extract_args 가 원문에서 채운다(그래서 더미 인자 OK).
실제 모델을 쓰려면 OttoModel().generate_fn 을 Agent 에 주입.
"""
from __future__ import annotations

import re

from extract import _MATH

_PROMPT_SPLIT = "### 지시:\n"


def local_router(prompt: str) -> str:
    q = prompt.split(_PROMPT_SPLIT, 1)[-1].split("\n", 1)[0].strip() if _PROMPT_SPLIT in prompt else prompt.strip()

    # 1) 산술 → calculator (extract 가 원문에서 수식 재추출)
    if _MATH.search(q.replace("×", "*").replace("÷", "/")):
        return 'calculator(수식="0")'

    # 2) 날씨 → weather (도시 추출)
    if any(w in q for w in ("날씨", "기온", "비 와")):
        m = re.search(r"([가-힣]+?)\s*(?:의)?\s*(?:날씨|기온)", q)
        return f'weather(도시="{m.group(1) if m else ""}")'

    # 3) 검색성 질의 → search (extract 가 꼬리말 제거해 채움)
    if any(w in q for w in ("검색", "찾아", "시세", "환율", "예매", "조회")):
        return 'search(검색어="")'

    # 4) 그 외(지식/사실 질문) → rag (extract 가 원문 질문으로 채움)
    return 'rag(질문="")'
