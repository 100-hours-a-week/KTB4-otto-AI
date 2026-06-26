"""LangSmith Dataset 기반 RAG 평가.

두 가지 모드를 지원한다.

  python -m evaluation.eval_langsmith            # 로컬 오프라인 평가 (LangSmith 키 불필요)
  python -m evaluation.eval_langsmith --langsmith  # LangSmith 에 Dataset 업로드 + 클라우드 평가

평가 지표
  - correctness : Gemini 를 LLM-judge 로 써서 정답(reference)과 의미가 일치하는지 (CORRECT/INCORRECT)
  - source_match: 기대 출처 문서가 검색된 sources 에 포함됐는지 (groundedness 의 근사)

correctness 판정에는 정답 생성과 분리하기 위해 별도의 judge LLM(temperature=0)을 사용한다.
"""
from __future__ import annotations

import argparse
import json
import os
from typing import Dict, List

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from app.config import get_rate_limiter, get_settings
from app.rag_chain import get_chain

DATASET_PATH = os.path.join(os.path.dirname(__file__), "dataset.jsonl")
LANGSMITH_DATASET_NAME = "otto-rag-qa"


# ---------- 데이터셋 ----------
def load_dataset() -> List[Dict]:
    with open(DATASET_PATH, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


# ---------- LLM Judge (correctness) ----------
_JUDGE_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "너는 RAG 챗봇 답변을 채점하는 평가자다. "
            "기준 정답(reference)과 챗봇 답변(prediction)이 핵심 사실에서 일치하면 CORRECT, "
            "사실이 틀리거나 핵심 정보가 누락되면 INCORRECT 라고만 답하라. "
            "표현/말투 차이는 무시하고 사실 일치만 본다. "
            "정답이 '문서에서 찾을 수 없다'는 취지인데 챗봇도 그렇게 답하면 CORRECT 다.",
        ),
        (
            "human",
            "[질문]\n{question}\n\n[기준 정답]\n{reference}\n\n[챗봇 답변]\n{prediction}\n\n"
            "판정(CORRECT 또는 INCORRECT):",
        ),
    ]
)


def _judge_llm() -> ChatGoogleGenerativeAI:
    settings = get_settings()
    return ChatGoogleGenerativeAI(
        model=settings.gemini_chat_model,
        google_api_key=settings.google_api_key,
        temperature=0.0,
        rate_limiter=get_rate_limiter(),  # RAG LLM 과 호출 예산 공유
    )


def grade_correctness(question: str, reference: str, prediction: str) -> bool:
    chain = _JUDGE_PROMPT | _judge_llm() | StrOutputParser()
    verdict = chain.invoke(
        {"question": question, "reference": reference, "prediction": prediction}
    )
    return "CORRECT" in verdict.upper() and "INCORRECT" not in verdict.upper()


# ---------- 로컬 오프라인 평가 ----------
def run_local(limit: int | None = None) -> None:
    data = load_dataset()
    if limit:
        data = data[:limit]
    chain = get_chain()
    n = len(data)
    correct = 0
    source_hit = 0
    source_total = 0

    print(f"\n=== 로컬 평가 시작 (총 {n}문항) ===\n")
    for i, row in enumerate(data, 1):
        result = chain.query(row["question"])
        pred = result["answer"]
        is_correct = grade_correctness(row["question"], row["answer"], pred)
        correct += int(is_correct)

        # source_match: 기대 출처가 있는 문항만 채점 (없는 정보 케이스는 제외)
        src_ok = None
        if row.get("source"):
            source_total += 1
            src_ok = row["source"] in result["sources"]
            source_hit += int(src_ok)

        mark = "O" if is_correct else "X"
        src_str = "-" if src_ok is None else ("O" if src_ok else "X")
        print(f"[{i:02d}] 정답={mark} 출처={src_str} | Q: {row['question']}")
        print(f"     기대: {row['answer']}")
        print(f"     응답: {pred}")
        print(f"     검색출처: {result['sources']}\n")

    print("=== 요약 ===")
    print(f"correctness : {correct}/{n} = {correct / n:.1%}")
    if source_total:
        print(f"source_match: {source_hit}/{source_total} = {source_hit / source_total:.1%}")


# ---------- LangSmith 클라우드 평가 ----------
def run_langsmith() -> None:
    from langsmith import Client

    settings = get_settings()
    if not settings.langsmith_api_key:
        raise SystemExit(
            "LANGSMITH_API_KEY 가 비어 있습니다. .env 에 키를 넣고 "
            "LANGSMITH_TRACING=true 로 설정하세요."
        )
    # tracing 환경변수 보장
    os.environ.setdefault("LANGCHAIN_API_KEY", settings.langsmith_api_key)
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_PROJECT"] = settings.langsmith_project

    client = Client()
    data = load_dataset()

    # 1) Dataset 생성 (이미 있으면 재사용)
    if client.has_dataset(dataset_name=LANGSMITH_DATASET_NAME):
        dataset = client.read_dataset(dataset_name=LANGSMITH_DATASET_NAME)
    else:
        dataset = client.create_dataset(
            dataset_name=LANGSMITH_DATASET_NAME,
            description="otto RAG QA 평가셋 (스타트업코드/부트캠프 문서)",
        )
        client.create_examples(
            inputs=[{"question": r["question"]} for r in data],
            outputs=[{"answer": r["answer"], "source": r["source"]} for r in data],
            dataset_id=dataset.id,
        )
        print(f"[langsmith] Dataset '{LANGSMITH_DATASET_NAME}' 생성, 예시 {len(data)}개 업로드")

    # 2) 평가 대상 함수 (LangSmith 가 각 example 마다 호출)
    def target(inputs: dict) -> dict:
        return get_chain().query(inputs["question"])

    # 3) 평가자 (LangSmith evaluator 시그니처: run, example)
    def correctness_evaluator(run, example) -> dict:
        pred = (run.outputs or {}).get("answer", "")
        ref = (example.outputs or {}).get("answer", "")
        ok = grade_correctness(example.inputs["question"], ref, pred)
        return {"key": "correctness", "score": int(ok)}

    def source_evaluator(run, example) -> dict:
        expected = (example.outputs or {}).get("source", "")
        sources = (run.outputs or {}).get("sources", [])
        if not expected:  # '문서에 없음' 케이스는 채점 제외 -> None
            return {"key": "source_match", "score": None}
        return {"key": "source_match", "score": int(expected in sources)}

    from langsmith import evaluate

    results = evaluate(
        target,
        data=LANGSMITH_DATASET_NAME,
        evaluators=[correctness_evaluator, source_evaluator],
        experiment_prefix="otto-rag",
        max_concurrency=2,
    )
    print("\n[langsmith] 평가 완료. https://smith.langchain.com 에서 결과를 확인하세요.")
    print(results)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--langsmith",
        action="store_true",
        help="LangSmith 에 Dataset 업로드 후 클라우드 평가 (키 필요)",
    )
    parser.add_argument(
        "--limit", type=int, default=None, help="앞에서 N개 문항만 평가 (빠른 점검용)"
    )
    args = parser.parse_args()
    if args.langsmith:
        run_langsmith()
    else:
        run_local(limit=args.limit)


if __name__ == "__main__":
    main()
