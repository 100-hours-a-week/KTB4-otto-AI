"""오프라인 로컬 RAG 검색 (의존성 0, stdlib 만).

2단계: ① 질문에 맞는 **단락**을 TF-IDF 로 찾고 ② 그 단락 안에서 질문에 가장
맞는 **문장**만 골라 간결히 답한다. (단락 통째 반환 X)
Gemini/서버 없이도 in-domain 지식 질문에 근거 기반으로 답하기 위한 폴백.
"""
from __future__ import annotations

import glob
import math
import os
import re
from collections import Counter

try:
    _BASE = os.path.dirname(os.path.abspath(__file__))
except NameError:  # 노트북 셀에 인라인된 경우 __file__ 없음
    _BASE = os.getcwd()
_DEFAULT_DOCS = os.path.join(_BASE, "..", "03_rag", "langchain_rag", "docs")
DOCS_DIR = os.environ.get("RAG_DOCS_DIR", _DEFAULT_DOCS)


def _ngrams(text: str, n: int = 2) -> list[str]:
    """문자 n-gram. 한국어 조사(은/는/이/가...)를 흡수해 부분일치를 견고하게.
    예) '구독료'와 '구독료는' 이 'ㄱ구독','독료' n-gram 을 공유."""
    s = "".join(re.findall(r"[가-힣a-z0-9]", text.lower()))
    return [s[i : i + n] for i in range(len(s) - n + 1)]


def _sentences(paragraph: str) -> list[str]:
    """단락을 문장 단위로 분리. 헤딩(#) 줄 제외, 줄바꿈 이어붙인 뒤 마침표 기준 분리."""
    text = " ".join(
        ln.strip() for ln in paragraph.split("\n") if not ln.strip().startswith("#")
    )
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if len(s.strip()) >= 8]


class LocalRetriever:
    def __init__(self, docs_dir: str = DOCS_DIR):
        self.paras: list[tuple[str, str]] = []  # (source, paragraph)
        for path in sorted(glob.glob(os.path.join(docs_dir, "*.md"))):
            src = os.path.basename(path)
            with open(path, encoding="utf-8") as f:
                text = f.read()
            for para in re.split(r"\n\s*\n", text):
                if len(para.strip()) >= 20:
                    self.paras.append((src, para.strip()))
        # 문자 n-gram idf (코퍼스 전체 기준 — 희귀 표현일수록 변별력↑)
        n = max(len(self.paras), 1)
        df: Counter = Counter()
        for _, text in self.paras:
            for g in set(_ngrams(text)):
                df[g] += 1
        self.idf = {g: math.log((n + 1) / (df_g + 1)) + 1 for g, df_g in df.items()}

    def _score(self, query: str, text: str) -> float:
        qg = set(_ngrams(query))
        tg = set(_ngrams(text))
        return sum(self.idf.get(g, 1.0) for g in qg & tg)

    def best_paragraph(self, query: str) -> tuple[str, str] | None:
        best = max(self.paras, key=lambda p: self._score(query, p[1]), default=None)
        # 흔한 n-gram(어미 등)만 걸린 경우 배제: 의미 있는 매칭 점수 요구
        if best is None or self._score(query, best[1]) < 2.0:
            return None
        return best

    def answer(self, query: str) -> tuple[str, str] | None:
        """① 최적 단락 → ② 그 안에서 질문을 가장 잘 담은 문장 1~2개."""
        hit = self.best_paragraph(query)
        if hit is None:
            return None
        src, para = hit
        sents = _sentences(para) or [para]
        # 단락 제목에 든 단어 = 주제어 → 문장 선택 시 약화(질문의 '의도'어가 이기게)
        head_grams = set(
            _ngrams(" ".join(l for l in para.split("\n") if l.strip().startswith("#")))
        )
        qg = set(_ngrams(query))

        def sscore(s: str) -> float:
            sg = set(_ngrams(s))
            return sum(
                self.idf.get(g, 1.0) * (0.3 if g in head_grams else 1.0)
                for g in qg & sg
            )

        ranked = sorted(sents, key=sscore, reverse=True)
        top_score = sscore(ranked[0])
        # 기본 1문장. 2번째는 점수가 '거의 동률'(>=0.9)일 때만 — 한 세트로 묶인 답
        picked = [s for s in ranked if sscore(s) >= top_score * 0.9][:2]
        return src, " ".join(picked)


_retriever: LocalRetriever | None = None


def local_rag(질문: str = "", 검색어: str = "", **_) -> str:
    """로컬 문서에서 질문에 맞는 문장을 찾아 간결히 반환. (offline, no quota)"""
    global _retriever
    q = (질문 or 검색어).strip()
    if not q:
        return "질문이 비었습니다."
    if _retriever is None:
        _retriever = LocalRetriever()
    res = _retriever.answer(q)
    if res is None:
        return "제공된 문서에서 답을 찾을 수 없습니다."
    src, text = res
    return f"{text} (출처: {src}, 로컬검색)"
