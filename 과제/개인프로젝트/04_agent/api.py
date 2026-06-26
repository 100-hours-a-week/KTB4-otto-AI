"""에이전트 FastAPI 서버.

질문 → otto(또는 로컬 룰 라우터) → 도구 실행 → 답변 을 REST 로 노출.
otto 체크포인트가 있으면 실제 모델, 없으면 오프라인 룰 라우터로 동작(어디서나 실행).

실행:
    uvicorn api:app --reload --port 8001
    curl -X POST localhost:8001/agent -H 'Content-Type: application/json' \
         -d '{"question":"12*7 계산해줘"}'
"""
from __future__ import annotations

import os

from fastapi import FastAPI
from pydantic import BaseModel, Field

from agent import Agent
from local_router import local_router


def _build_agent() -> Agent:
    proj = os.environ.get("OTTO_PROJECT_DIR")
    if proj and os.path.exists(f"{proj}/ckpt/otto_gpt_instruct.pt"):
        from otto_model import OttoModel  # torch/spm 필요 — 체크포인트 있을 때만
        from hybrid import make_safe_router
        print(f"[agent] otto_gpt 라우터 + 환각 안전망 사용: {proj}")
        # otto 가 환각하면 규칙 라우터로 폴백 → 사용자에게 환각이 도달하지 않음
        return Agent(generate_fn=make_safe_router(OttoModel(proj).generate_fn))
    print("[agent] 로컬 룰 라우터 사용 (otto 체크포인트 없음)")
    return Agent(generate_fn=local_router)


app = FastAPI(title="otto Agent API", description="otto 라우터 + 도구 실행 에이전트", version="1.0.0")
_agent: Agent | None = None


def get_agent() -> Agent:
    global _agent
    if _agent is None:
        _agent = _build_agent()
    return _agent


class AgentRequest(BaseModel):
    question: str = Field(..., min_length=1)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/agent")
def run_agent(req: AgentRequest):
    """질문을 라우팅 → 도구 실행 → 답변. (도구/인자보정/관찰도 함께 반환)"""
    return get_agent().run(req.question)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api:app", host="0.0.0.0", port=8001, reload=True)
