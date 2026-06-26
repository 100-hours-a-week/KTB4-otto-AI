"""환각 차단 안전 라우터.

otto(57M)는 학습 분포 밖 입력에서 도구 호출 대신 자유 텍스트(환각)를 내뱉을 수 있다.
이 래퍼는 otto 출력이 **유효한 도구 호출일 때만** 사용하고, 아니면 규칙 라우터로 폴백한다.
→ 모델의 자유 생성 텍스트가 사용자 답변으로 절대 도달하지 않는다.
  (모든 답 = 도구 결과 / 문서 근거 / 정직한 '못 찾음')
"""
from __future__ import annotations

from typing import Callable

from local_router import local_router
from parser import parse_tool_call


def make_safe_router(model_fn: Callable[[str], str]) -> Callable[[str], str]:
    """모델 라우터를 환각 안전 버전으로 감싼다."""

    def _route(prompt: str) -> str:
        out = (model_fn(prompt) or "").strip()
        if parse_tool_call(out):
            return out  # otto 가 제대로 라우팅 → 그대로 사용
        return local_router(prompt)  # 환각/실패 → 규칙으로 안전하게 도구 선택

    return _route
