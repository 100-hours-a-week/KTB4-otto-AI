"""도구 레지스트리 + 실행.

calculator 는 실제로 계산하고(안전한 산술 eval), weather/search 는 외부 키가 없으므로
목업(mock) 결과를 돌려준다. 실제 API 키가 있으면 해당 함수만 교체하면 된다.
"""
from __future__ import annotations

import ast
import json
import operator
import os
import urllib.error
import urllib.request

# ── calculator: 안전한 산술 평가 (eval 미사용) ──
_OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub,
    ast.Mult: operator.mul, ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod,
    ast.Pow: operator.pow, ast.USub: operator.neg, ast.UAdd: operator.pos,
}


def _safe_eval(node):
    if isinstance(node, ast.Expression):
        return _safe_eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_safe_eval(node.operand))
    raise ValueError("허용되지 않은 수식")


def calculator(수식: str = "", **_) -> str:
    try:
        result = _safe_eval(ast.parse(수식, mode="eval"))
        return f"{수식} = {result}"
    except Exception:
        return f"계산할 수 없는 수식: {수식!r}"


def weather(도시: str = "", **_) -> str:
    # 목업: 실제로는 기상 API 호출. 도시명으로 결정적 가짜 데이터 생성.
    temp = 18 + (len(도시) * 3) % 12
    return f"{도시}의 현재 날씨: 맑음, 기온 {temp}도 (mock)"


def search(검색어: str = "", **_) -> str:
    # 목업: 실제로는 검색 API 호출.
    return f"'{검색어}' 검색 결과 상위 항목 (mock): 관련 문서 3건"


# ── RAG 도구: 03_rag 의 FastAPI /query 를 HTTP 로 호출 (venv 분리 유지) ──
# 지식이 필요한 질문은 작은 라우터(otto_gpt) 대신 RAG 가 근거 기반으로 답한다.
RAG_API = os.environ.get("RAG_API", "http://127.0.0.1:8000/query")


def rag_search(검색어: str = "", 질문: str = "", **_) -> str:
    """03_rag 파이프라인에 질문을 던져 근거 기반 답변 + 출처를 받는다.
    otto_gpt 는 search(검색어=...) 로 호출하므로 검색어/질문 둘 다 받는다."""
    q = (질문 or 검색어).strip()
    if not q:
        return "검색어가 비었습니다."
    try:
        req = urllib.request.Request(
            RAG_API,
            data=json.dumps({"question": q}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            d = json.loads(resp.read().decode("utf-8"))
        srcs = ", ".join(d.get("sources", []))
        return f"{d.get('answer', '')}" + (f" (출처: {srcs})" if srcs else "")
    except urllib.error.URLError:
        # 서버/Gemini 없을 때 → 오프라인 로컬 문서 검색으로 폴백
        try:
            from local_rag import local_rag
            return local_rag(질문=q)
        except Exception:
            return "[RAG 서버 연결 실패 + 로컬 문서 없음]"
    except Exception as e:
        return f"[RAG 오류: {e}]"


# 기본 레지스트리 (search = 목업, rag = 실제 03_rag 호출)
REGISTRY = {
    "calculator": calculator,
    "weather": weather,
    "search": search,
    "rag": rag_search,
}


def rag_registry() -> dict:
    """search 를 실제 RAG 로 바인딩한 레지스트리.
    otto_gpt 가 이미 search 로 라우팅하므로 재학습 없이 지식 질문을 RAG 로 보낸다."""
    return {**REGISTRY, "search": rag_search, "rag": rag_search}
