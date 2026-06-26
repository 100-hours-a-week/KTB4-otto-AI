"""에이전트 레이어 인자 재추출.

otto_gpt(57M)는 '어떤 도구를 쓸지'(라우팅)는 잘하나 '정확한 인자 복사'가 약하다
(예: 345+678 → 346+679, 오늘 환율 → 오늘 환율이, rag 인자 깨짐).
→ 모델의 라우팅 결정은 신뢰하되, 정밀한 인자는 사용자 원문에서 직접 추출한다.
"""
from __future__ import annotations

import re

# 단일 이항 산술식: 12*7, 345 + 678, 100/4 ...
_MATH = re.compile(r"(-?\d+(?:\.\d+)?)\s*([-+*/])\s*(-?\d+(?:\.\d+)?)")
# search 질의에서 떼어낼 꼬리말
_SEARCH_TAIL = re.compile(r"\s*(검색해줘|검색해|좀\s*찾아줘|찾아줘|검색|알려줘)\s*$")


def extract_args(tool: str, question: str, model_args: dict) -> dict:
    """도구별로 신뢰 가능한 인자를 만든다. 못 뽑으면 모델 인자로 폴백."""
    q = question.strip()

    if tool == "calculator":
        norm = q.replace("×", "*").replace("÷", "/")
        m = _MATH.search(norm)
        if m:
            return {"수식": f"{m.group(1)}{m.group(2)}{m.group(3)}"}
        return model_args

    if tool == "rag":
        # 모델 인자가 자주 깨짐 → 원문 질문을 그대로 (RAG는 자연어 질문 처리 OK)
        return {"질문": q}

    if tool == "search":
        cleaned = _SEARCH_TAIL.sub("", q).strip()
        return {"검색어": cleaned or model_args.get("검색어", "")}

    # weather 등은 모델 인자가 대체로 정확 → 그대로 사용
    return model_args
