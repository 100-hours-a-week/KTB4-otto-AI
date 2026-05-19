import requests
from fastapi import HTTPException

from models import post_model


OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "gemma4"


def summarize_post(post_id: int):
    post = post_model.get_post_by_id(post_id)

    if not post:
        raise HTTPException(status_code=404, detail="글을 찾을 수 없습니다.")

    prompt = f"""
너는 게시글 요약 API입니다.

아래 게시글을 요약하세요.

규칙:
- 반드시 한국어로 답변하세요.
- 반드시 3문장 이내로 답변하세요.
- 제목, 마크다운, 목록, 이모지, 코드블록은 절대 사용하지 마세요.
- 설명을 덧붙이지 말고 요약 결과만 작성하세요.

게시글 제목: {post["title"]}
작성자: {post["username"]}
게시글 내용: {post["content"]}
"""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
            },
            timeout=60,
        )
    except requests.exceptions.ConnectionError:
        raise HTTPException(
            status_code=503,
            detail="Ollama 서버에 연결할 수 없습니다. ollama run gemma4 실행 여부를 확인해주세요.",
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=500,
            detail="LLM 요약 요청 중 오류가 발생했습니다.",
        )

    result = response.json()
    summary = result.get("response", "").strip()

    return {
        "message": "LLM 글 요약 성공",
        "data": {
            "post_id": post_id,
            "model": OLLAMA_MODEL,
            "summary": summary,
        },
    }
