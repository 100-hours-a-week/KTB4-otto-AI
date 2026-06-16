"""
웹 검색 (논파라메트릭 검색 — 소스가 '실시간 웹')
=================================================
RAG 의 '검색(Retrieve)' 단계를 로컬 벡터DB 대신 실시간 웹 검색으로 수행한다.
DuckDuckGo(무료, API 키 불필요)로 검색하고, 상위 결과 페이지 본문을 일부 가져와
컨텍스트로 만든다.

retriever.search() 와 같은 형태의 hits 를 돌려준다:
  [{"text": ..., "source": <url>, "similarity": <순위기반 점수>}, ...]
"""

import re
import urllib.request

from ddgs import DDGS


def _fetch_page_text(url, max_chars=1500, timeout=6):
    """웹페이지 본문 텍스트를 간단히 추출(태그 제거)."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        html = urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8", "ignore")
    except Exception:
        return ""
    # script/style 제거 후 태그 제거
    html = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", html)
    text = re.sub(r"(?s)<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_chars]


def search(query, n_results=4, fetch_pages=True):
    """웹에서 검색해 상위 결과를 hits 형태로 반환."""
    results = []
    with DDGS() as ddgs:
        raw = list(ddgs.text(query, region="kr-kr", max_results=n_results))

    for rank, r in enumerate(raw):
        url = r.get("href") or r.get("url", "")
        snippet = r.get("body", "")
        title = r.get("title", "")
        # 본문 일부를 가져와 더 풍부한 컨텍스트 구성 (실패하면 스니펫만)
        body = _fetch_page_text(url) if fetch_pages else ""
        text = f"{title}\n{body or snippet}".strip()
        results.append({
            "text": text,
            "source": url,
            "similarity": round(1.0 - rank * 0.1, 3),  # 순위 기반 점수
        })
    return results


if __name__ == "__main__":
    for h in search("2024년 노벨 물리학상 수상자", n_results=3):
        print(f"[{h['source']}]\n{h['text'][:120]}...\n")
