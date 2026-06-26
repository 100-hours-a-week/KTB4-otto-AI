"""터미널에서 RAG 를 빠르게 테스트하는 CLI.

사용법:
  python cli.py --build              # Chroma 인덱스 재구축
  python cli.py "환불 정책 알려줘"     # 단일 질문
  python cli.py                      # 대화형 모드
"""
from __future__ import annotations

import sys

from app.ingest import build_index
from app.rag_chain import get_chain


def _answer(question: str) -> None:
    result = get_chain().query(question)
    print(f"\nA: {result['answer']}")
    print(f"   (출처: {', '.join(result['sources'])})\n")


def main() -> None:
    args = sys.argv[1:]

    if args and args[0] == "--build":
        build_index()
        return

    if args:
        _answer(" ".join(args))
        return

    print("대화형 RAG — 멀티턴 (종료: exit / 맥락 초기화: reset)")
    chain = get_chain()
    session_id = "cli"
    while True:
        try:
            q = input("\nQ: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if q.lower() in {"exit", "quit", "q"}:
            break
        if q.lower() == "reset":
            chain.reset_session(session_id)
            print("(대화 맥락을 초기화했습니다)")
            continue
        if q:
            result = chain.chat(q, session_id=session_id)
            print(f"\nA: {result['answer']}")
            print(f"   (출처: {', '.join(result['sources'])})\n")


if __name__ == "__main__":
    main()
