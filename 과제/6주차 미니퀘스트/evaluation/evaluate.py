"""RAGAS로 RAG 파이프라인 평가.

RAGAS는 LLM-as-judge 방식으로 다음 지표를 계산한다:
- faithfulness        : 답변이 검색된 문맥에 충실한가 (환각 여부)
- answer_relevancy    : 답변이 질문과 관련 있는가
- context_precision   : 검색된 문맥 중 정답에 유용한 것의 비율
- context_recall      : 정답을 뒷받침하는 문맥이 충분히 검색됐는가

심판(LLM)과 임베딩 모두 Gemini를 사용한다.
"""
from __future__ import annotations

import json
import os
import time

from datasets import Dataset
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from ragas import evaluate
from ragas.run_config import RunConfig
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.metrics import (
    answer_relevancy,
    context_precision,
    context_recall,
    faithfulness,
)

from app.config import get_settings
from app.rag_pipeline import get_pipeline

HERE = os.path.dirname(__file__)
TESTSET_PATH = os.path.join(HERE, "eval_dataset.json")


def build_eval_dataset() -> Dataset:
    """테스트 질문을 파이프라인에 흘려 RAGAS 입력 형식을 만든다."""
    with open(TESTSET_PATH, encoding="utf-8") as f:
        testset = json.load(f)

    # 무료 할당량(분당 요청 제한) 안에서 돌리도록 문항 수를 제한할 수 있다.
    limit = int(os.environ.get("EVAL_LIMIT", "0"))
    if limit > 0:
        testset = testset[:limit]
    # 호출 간 간격(초) — 분당 요청 제한 회피용.
    delay = float(os.environ.get("EVAL_DELAY", "0"))

    pipeline = get_pipeline()
    rows = {"question": [], "answer": [], "contexts": [], "ground_truth": []}

    for item in testset:
        result = pipeline.query(item["question"])
        rows["question"].append(item["question"])
        rows["answer"].append(result["answer"])
        rows["contexts"].append(result["contexts"])
        rows["ground_truth"].append(item["ground_truth"])
        print(f"  ✓ {item['question'][:40]}...")
        if delay:
            time.sleep(delay)

    return Dataset.from_dict(rows)


def main() -> None:
    settings = get_settings()

    print("[1/2] 평가 데이터셋 생성 중 (파이프라인 실행)...")
    dataset = build_eval_dataset()

    # RAGAS가 내부적으로 사용할 심판 LLM/임베딩을 Gemini로 설정.
    # 심판 모델은 무료 할당량이 더 큰 모델을 따로 지정할 수 있다(기본: 채팅 모델).
    judge_model = os.environ.get("RAGAS_JUDGE_MODEL", settings.gemini_chat_model)
    judge_llm = LangchainLLMWrapper(
        ChatGoogleGenerativeAI(
            model=judge_model,
            google_api_key=settings.google_api_key,
            temperature=0,
        )
    )
    judge_emb = LangchainEmbeddingsWrapper(
        GoogleGenerativeAIEmbeddings(
            model=settings.gemini_embed_model,
            google_api_key=settings.google_api_key,
        )
    )

    # 분당 요청 제한(rate limit)에 견디도록: 동시성 최소화 + 재시도/대기 확대.
    run_config = RunConfig(
        max_workers=int(os.environ.get("RAGAS_MAX_WORKERS", "1")),
        max_retries=15,
        max_wait=90,
        timeout=300,
    )

    print(f"[2/2] RAGAS 평가 실행 중 (심판 모델: {judge_model})...")
    result = evaluate(
        dataset=dataset,
        metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
        llm=judge_llm,
        embeddings=judge_emb,
        run_config=run_config,
    )

    print("\n===== RAGAS 평가 결과 =====")
    print(result)

    df = result.to_pandas()
    out_csv = os.path.join(HERE, "ragas_result.csv")
    df.to_csv(out_csv, index=False)
    print(f"\n상세 결과 저장: {out_csv}")


if __name__ == "__main__":
    main()
