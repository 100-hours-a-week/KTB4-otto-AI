"""RAGAS 기반 RAG 평가 — 표준 4대 지표로 baseline 점수를 잡는다.

지표 (06/17 커리큘럼)
  - Faithfulness        : 답변이 검색된 근거에 충실한가 (환각 여부)
  - Answer Relevancy    : 답변이 질문에 적절한가
  - Context Precision   : 검색된 컨텍스트 중 정답에 필요한 것의 비율 (정밀도)
  - Context Recall      : 정답에 필요한 정보가 검색에 포함됐는가 (재현율)

평가자(judge) LLM/임베딩은 우리 스택과 동일하게 Gemini 를 주입한다.

⚠️ 호환성: RAGAS 0.4.x 가 사라진 `langchain_community.chat_models.vertexai` 를 import 하는
   버그가 있다. 우리는 Gemini 를 직접 주입하므로 `ChatVertexAI` 는 실제로 쓰이지 않는다 →
   import 전에 빈 shim 으로 우회한다 (site-packages 수정 없음).

⚠️ 호출량: 지표 4종은 문항당 여러 번 LLM 을 호출하고, 거기에 RAG 답변 생성까지 더해진다.
   Gemini 무료티어(현재 flash-lite 20회/일)로는 2~3문항이 한계다. `--limit` 로 조절하고,
   전체 baseline 은 quota 여유(리셋/유료 키) 시 실행할 것.

사용법
  python -m evaluation.eval_ragas              # 앞 3문항 (무료티어 안전)
  python -m evaluation.eval_ragas --limit 11   # 전체 (quota 충분할 때)
"""
from __future__ import annotations

# --- ragas import 전에 사라진 모듈 경로를 shim 으로 대체 ---
import sys
import types as _types

_shim = _types.ModuleType("langchain_community.chat_models.vertexai")
_shim.ChatVertexAI = object  # 미사용 (Gemini 직접 주입)
sys.modules.setdefault("langchain_community.chat_models.vertexai", _shim)

import argparse
import json
import os
from typing import List

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from ragas import EvaluationDataset, SingleTurnSample, evaluate
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import (
    Faithfulness,
    LLMContextPrecisionWithReference,
    LLMContextRecall,
    ResponseRelevancy,
)

from app.config import get_rate_limiter, get_settings
from app.rag_chain import get_chain

DATASET_PATH = os.path.join(os.path.dirname(__file__), "dataset.jsonl")


def load_dataset() -> List[dict]:
    with open(DATASET_PATH, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def build_eval_dataset(limit: int | None) -> EvaluationDataset:
    """각 질문을 RAG 로 돌려 (질문/검색컨텍스트/답변/기준정답) 샘플을 만든다."""
    data = load_dataset()
    if limit:
        data = data[:limit]
    chain = get_chain()
    samples = []
    for i, row in enumerate(data, 1):
        result = chain.query(row["question"])
        samples.append(
            SingleTurnSample(
                user_input=row["question"],
                retrieved_contexts=result["contexts"],
                response=result["answer"],
                reference=row["answer"],
            )
        )
        print(f"  [{i}/{len(data)}] RAG 응답 생성 완료: {row['question']}")
    return EvaluationDataset(samples=samples)


def make_judge():
    """RAGAS 가 쓸 평가자 LLM/임베딩 (Gemini)."""
    s = get_settings()
    judge_llm = LangchainLLMWrapper(
        ChatGoogleGenerativeAI(
            model=s.gemini_chat_model,
            google_api_key=s.google_api_key,
            temperature=0.0,
            rate_limiter=get_rate_limiter(),
        )
    )
    judge_emb = LangchainEmbeddingsWrapper(
        GoogleGenerativeAIEmbeddings(
            model=s.gemini_embed_model,
            google_api_key=s.google_api_key,
        )
    )
    return judge_llm, judge_emb


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--limit", type=int, default=3,
        help="앞에서 N개 문항만 평가 (기본 3 — 무료티어 quota 안전)",
    )
    args = parser.parse_args()

    print(f"\n=== RAGAS 평가 시작 (문항 {args.limit}개) ===")
    print("1) RAG 파이프라인으로 답변+컨텍스트 수집...")
    dataset = build_eval_dataset(args.limit)

    print("2) RAGAS 지표 채점 (Gemini judge)...")
    judge_llm, judge_emb = make_judge()
    metrics = [
        Faithfulness(),
        ResponseRelevancy(),
        LLMContextPrecisionWithReference(),
        LLMContextRecall(),
    ]

    # 동시성 1 로 낮춰 분당 호출 제한(RPM) 부담을 줄인다.
    run_config = None
    try:
        from ragas import RunConfig
        run_config = RunConfig(max_workers=1)
    except Exception:
        pass

    result = evaluate(
        dataset,
        metrics=metrics,
        llm=judge_llm,
        embeddings=judge_emb,
        **({"run_config": run_config} if run_config else {}),
    )

    print("\n=== RAGAS baseline 점수 ===")
    print(result)
    try:
        df = result.to_pandas()
        print("\n[문항별]")
        print(df.to_string())
    except Exception:
        pass


if __name__ == "__main__":
    main()
