"""
검색 · 계산 층 (RAG 2단계) — 전부 로컬, 정확, 환각 없음
=========================================================
- 문서: 임베딩 벡터 검색으로 질문과 관련된 청크 top-k 를 찾는다.
- 표(CSV/Excel): pandas 로 실제 값을 계산한다 (평균/최대/최소/합계/표준편차/개수).

이 층은 '정확한 근거(evidence)'만 만들고, 자연어로 풀어 쓰는 일은 llm_backend 가 한다.
"""

import os
# transformers 가 TensorFlow/Keras3 를 불러오지 않도록 torch 백엔드만 사용
os.environ.setdefault("USE_TF", "0")
os.environ.setdefault("TRANSFORMERS_NO_ADVISORY_WARNINGS", "1")

import glob
import pickle

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_PATH = os.path.join(BASE_DIR, "index", "doc_index.pkl")
TABLES_DIR = os.path.join(BASE_DIR, "data", "tables")

# 집계 키워드 → pandas 연산
AGG_KEYWORDS = {
    "평균": "mean", "최대": "max", "최댓값": "max", "가장 높": "max",
    "최소": "min", "최솟값": "min", "가장 낮": "min",
    "합계": "sum", "총합": "sum", "표준편차": "std",
    "개수": "count", "몇 개": "count", "갯수": "count",
}


class Retriever:
    def __init__(self):
        # --- 문서 인덱스 로딩 ---
        self.records, self.embeddings, self.embed_model = [], None, None
        if os.path.exists(INDEX_PATH):
            with open(INDEX_PATH, "rb") as f:
                idx = pickle.load(f)
            self.records = idx["records"]
            self.embeddings = idx["embeddings"]
            self.embed_model = SentenceTransformer(idx["model_name"])

        # --- 표(CSV/Excel) 로딩 ---
        self.tables = {}   # 파일명 -> DataFrame
        for path in glob.glob(os.path.join(TABLES_DIR, "*.csv")):
            self.tables[os.path.basename(path)] = pd.read_csv(path)
        for path in glob.glob(os.path.join(TABLES_DIR, "*.xlsx")):
            self.tables[os.path.basename(path)] = pd.read_excel(path)

    # ------------------------------------------------------------------
    # 문서 벡터 검색
    # ------------------------------------------------------------------
    def search_docs(self, query, top_k=3):
        if self.embed_model is None or self.embeddings is None or len(self.records) == 0:
            return []
        q = self.embed_model.encode([query], normalize_embeddings=True)
        q = np.asarray(q, dtype="float32")[0]
        scores = self.embeddings @ q            # 코사인 유사도 (정규화됨)
        top_idx = np.argsort(-scores)[:top_k]
        return [{"text": self.records[i]["text"],
                 "source": self.records[i]["source"],
                 "score": float(scores[i])} for i in top_idx]

    # ------------------------------------------------------------------
    # 표 계산 (질문에서 컬럼명 + 집계 키워드 + 그룹 필터를 추출)
    # ------------------------------------------------------------------
    def query_tables(self, query):
        results = []
        # 어떤 집계인지 파악
        agg = next((op for kw, op in AGG_KEYWORDS.items() if kw in query), None)

        for fname, df in self.tables.items():
            num_cols = df.select_dtypes(include="number").columns.tolist()
            # 질문에 등장한 숫자형 컬럼 찾기 (컬럼명 일부만 포함돼도 인식)
            target_cols = [c for c in num_cols
                           if c.lower() in query.lower()
                           or c.split("_")[0].lower() in query.lower()]

            # 그룹 필터: 문자열 컬럼 값 중 질문에 등장하는 것
            filt = df
            filter_desc = ""
            for c in df.select_dtypes(include="object").columns:
                for val in df[c].unique():
                    if str(val).lower() in query.lower():
                        filt = filt[filt[c] == val]
                        filter_desc = f"{c}={val} 조건에서 "
                        break

            if agg and target_cols:
                for col in target_cols:
                    series = filt[col].dropna()
                    if len(series) == 0:
                        continue
                    value = getattr(series, agg)()
                    results.append({
                        "file": fname,
                        "description": f"{filter_desc}{col}의 {_agg_kor(agg)}",
                        "value": round(float(value), 4) if agg != "count" else int(value),
                        "n_rows": int(len(series)),
                    })
        return results

    # 표 전체 개요 (LLM 에게 항상 제공하는 컨텍스트)
    def table_overview(self):
        lines = []
        for fname, df in self.tables.items():
            cols = ", ".join(df.columns)
            lines.append(f"[{fname}] 행 {len(df)}개, 컬럼: {cols}")
        return "\n".join(lines)


def _agg_kor(agg):
    return {"mean": "평균", "max": "최댓값", "min": "최솟값", "sum": "합계",
            "std": "표준편차", "count": "개수"}.get(agg, agg)
