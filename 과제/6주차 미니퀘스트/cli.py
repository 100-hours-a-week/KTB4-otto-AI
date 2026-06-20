"""터미널에서 RAG를 빠르게 테스트하는 CLI.

사용법:
  python cli.py --build                 # 인덱스 재구축
  python cli.py "RAG가 뭐야?"            # 단일 질문
  python cli.py                         # 대화형 모드
"""
from __future__ import annotations

import sys

from app.rag_pipeline import get_pipeline
from app.vector_store import build_index


def _answer(question: str) -> None:
    result = get_pipeline().query(question)
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

    print("대화형 RAG (종료: exit)")
    while True:
        try:
            q = input("\nQ: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if q.lower() in {"exit", "quit", "q"}:
            break
        if q:
            _answer(q)


if __name__ == "__main__":
    main()
