"""
답변 생성 층 (RAG 3단계) — 교체 가능(pluggable)
=================================================
retriever 가 찾아준 '근거(표 계산값 + 문서 청크)'를 바탕으로 답변을 만든다.

두 가지 백엔드를 환경변수로 선택:
  - LLM_BACKEND=local  (기본) : API 키 불필요. 근거를 그대로 정리해 정확히 답함(환각 없음).
  - LLM_BACKEND=claude         : ANTHROPIC_API_KEY 가 있으면 Claude 가 자연스럽게 답함.

ANTHROPIC_API_KEY 가 설정돼 있으면 자동으로 claude 백엔드를 사용한다.
"""

import os


def _build_context(table_results, doc_results, overview):
    """LLM 에게 줄 컨텍스트(근거) 문자열을 만든다."""
    parts = ["[보유 데이터 개요]", overview, ""]
    if table_results:
        parts.append("[표 데이터 계산 결과]")
        for r in table_results:
            parts.append(f"- {r['description']} = {r['value']} (파일 {r['file']}, n={r['n_rows']})")
        parts.append("")
    if doc_results:
        parts.append("[관련 문서 발췌]")
        for d in doc_results:
            parts.append(f"- ({d['source']}, 유사도 {d['score']:.2f}) {d['text']}")
        parts.append("")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# 로컬 백엔드 : 근거를 규칙 기반으로 정리 (정확·환각 없음, API 불필요)
# ---------------------------------------------------------------------------
def answer_local(question, table_results, doc_results, overview):
    lines = []
    if table_results:
        lines.append("📊 데이터 계산 결과:")
        for r in table_results:
            lines.append(f"  • {r['description']}: {r['value']}  (표본 {r['n_rows']}개, {r['file']})")
    if doc_results:
        top = doc_results[0]
        lines.append("")
        lines.append(f"📄 관련 문서 내용 ({top['source']}):")
        lines.append(f"  {top['text']}")
    if not lines:
        return ("관련 데이터를 찾지 못했어요. 컬럼명(예: yield_percent)이나 "
                "집계어(평균/최대/최소/합계)를 넣어 다시 물어봐 주세요.")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Claude 백엔드 : 근거를 바탕으로 자연스러운 한국어 답변 (API 키 필요)
# ---------------------------------------------------------------------------
def answer_claude(question, table_results, doc_results, overview):
    from anthropic import Anthropic

    client = Anthropic()  # ANTHROPIC_API_KEY 환경변수 자동 사용
    context = _build_context(table_results, doc_results, overview)

    system = (
        "너는 연구자의 실험 데이터를 분석해 주는 한국어 비서다. "
        "반드시 아래에 주어진 '근거'에 있는 값과 문서 내용만 사용해 답하라. "
        "근거에 없는 수치를 지어내지 말고, 없으면 모른다고 말하라. "
        "표 계산 결과가 있으면 그 수치를 인용해 간결하고 명확하게 설명하라."
    )
    user = f"질문: {question}\n\n근거:\n{context}"

    # 모델은 환경변수로 바꿀 수 있게 (기본: 비용 효율적인 Sonnet 4.6)
    model = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-6")
    resp = client.messages.create(
        model=model,
        max_tokens=800,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return "".join(b.text for b in resp.content if b.type == "text").strip()


# ---------------------------------------------------------------------------
# 진입점 : 환경에 따라 백엔드 자동 선택
# ---------------------------------------------------------------------------
def get_backend_name():
    explicit = os.environ.get("LLM_BACKEND", "").lower()
    if explicit in ("local", "claude"):
        return explicit
    # 명시 안 했으면, 키가 있으면 claude, 없으면 local
    return "claude" if os.environ.get("ANTHROPIC_API_KEY") else "local"


def answer(question, table_results, doc_results, overview):
    backend = get_backend_name()
    if backend == "claude":
        try:
            return answer_claude(question, table_results, doc_results, overview)
        except Exception as e:
            # 키 오류 등으로 실패하면 로컬로 안전하게 폴백
            local = answer_local(question, table_results, doc_results, overview)
            return f"(Claude 호출 실패 → 로컬 답변으로 대체: {e})\n\n{local}"
    return answer_local(question, table_results, doc_results, overview)
