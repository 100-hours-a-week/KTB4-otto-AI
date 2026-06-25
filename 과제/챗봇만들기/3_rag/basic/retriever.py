import os

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

AGG_KEYWORDS = {
    "평균": "mean", "최대": "max", "최댓값": "max", "가장 높": "max",
    "최소": "min", "최솟값": "min", "가장 낮": "min",
    "합계": "sum", "총합": "sum", "표준편차": "std",
    "개수": "count", "몇 개": "count", "갯수": "count",
}

class Retriever:
    def __init__(self):
        
        self.records, self.embeddings, self.embed_model = [], None, None
        if os.path.exists(INDEX_PATH):
            with open(INDEX_PATH, "rb") as f:
                idx = pickle.load(f)
            self.records = idx["records"]
            self.embeddings = idx["embeddings"]
            self.embed_model = SentenceTransformer(idx["model_name"])

        self.tables = {}   
        for path in glob.glob(os.path.join(TABLES_DIR, "*.csv")):
            self.tables[os.path.basename(path)] = pd.read_csv(path)
        for path in glob.glob(os.path.join(TABLES_DIR, "*.xlsx")):
            self.tables[os.path.basename(path)] = pd.read_excel(path)

    
    def search_docs(self, query, top_k=3):
        if self.embed_model is None or self.embeddings is None or len(self.records) == 0:
            return []
        q = self.embed_model.encode([query], normalize_embeddings=True)
        q = np.asarray(q, dtype="float32")[0]
        scores = self.embeddings @ q            
        top_idx = np.argsort(-scores)[:top_k]
        return [{"text": self.records[i]["text"],
                 "source": self.records[i]["source"],
                 "score": float(scores[i])} for i in top_idx]

    
    def query_tables(self, query):
        results = []
        
        agg = next((op for kw, op in AGG_KEYWORDS.items() if kw in query), None)

        for fname, df in self.tables.items():
            num_cols = df.select_dtypes(include="number").columns.tolist()
            
            target_cols = [c for c in num_cols
                           if c.lower() in query.lower()
                           or c.split("_")[0].lower() in query.lower()]

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

    def table_overview(self):
        lines = []
        for fname, df in self.tables.items():
            cols = ", ".join(df.columns)
            lines.append(f"[{fname}] 행 {len(df)}개, 컬럼: {cols}")
        return "\n".join(lines)

def _agg_kor(agg):
    return {"mean": "평균", "max": "최댓값", "min": "최솟값", "sum": "합계",
            "std": "표준편차", "count": "개수"}.get(agg, agg)
