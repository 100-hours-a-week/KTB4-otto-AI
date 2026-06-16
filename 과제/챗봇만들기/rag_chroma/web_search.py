import re
import urllib.request

from ddgs import DDGS

def _fetch_page_text(url, max_chars=1500, timeout=6):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        html = urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8", "ignore")
    except Exception:
        return ""
    
    html = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", html)
    text = re.sub(r"(?s)<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_chars]

def search(query, n_results=4, fetch_pages=True):
    results = []
    with DDGS() as ddgs:
        raw = list(ddgs.text(query, region="kr-kr", max_results=n_results))

    for rank, r in enumerate(raw):
        url = r.get("href") or r.get("url", "")
        snippet = r.get("body", "")
        title = r.get("title", "")
        
        body = _fetch_page_text(url) if fetch_pages else ""
        text = f"{title}\n{body or snippet}".strip()
        results.append({
            "text": text,
            "source": url,
            "similarity": round(1.0 - rank * 0.1, 3),  
        })
    return results

if __name__ == "__main__":
    for h in search("2024년 노벨 물리학상 수상자", n_results=3):
        print(f"[{h['source']}]\n{h['text'][:120]}...\n")
