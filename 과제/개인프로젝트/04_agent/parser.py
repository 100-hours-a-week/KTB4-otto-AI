"""모델이 내뱉는 도구 호출 문자열을 파싱한다.

예) 'weather(도시="부산")' -> ('weather', {'도시': '부산'})
    'calculator(수식="12*7")' -> ('calculator', {'수식': '12*7'})

도구 호출이 아니면(일반 답변이면) None 을 반환한다.
"""
from __future__ import annotations

import re

# 도구명은 ASCII, 인자명은 한글 가능(\w 는 유니코드 매칭)
_CALL = re.compile(r'^\s*([A-Za-z_]\w*)\s*\((.*)\)\s*$', re.DOTALL)
_ARG = re.compile(r'(\w+)\s*=\s*"([^"]*)"')


def parse_tool_call(text: str) -> tuple[str, dict[str, str]] | None:
    """도구 호출이면 (이름, kwargs), 아니면 None."""
    if not text:
        return None
    m = _CALL.match(text.strip())
    if not m:
        return None
    name = m.group(1)
    kwargs = dict(_ARG.findall(m.group(2)))
    if not kwargs:  # 괄호는 있는데 key="val" 형식이 없으면 도구 호출로 보지 않음
        return None
    return name, kwargs
