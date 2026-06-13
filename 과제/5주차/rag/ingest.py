"""
문서 인덱싱 (RAG 1단계)
========================
data/docs/ 안의 문서(.md/.txt/.pdf)를 읽어 일정 크기로 쪼갠 뒤(chunk),
한국어 임베딩 모델로 벡터화하여 index/ 에 저장한다.

실행:
    python3 ingest.py
"""

import os
# transformers 가 TensorFlow/Keras3 를 불러오지 않도록 torch 백엔드만 사용
os.environ.setdefault("USE_TF", "0")
os.environ.setdefault("TRANSFORMERS_NO_ADVISORY_WARNINGS", "1")

import glob
import pickle

import numpy as np
from sentence_transformers import SentenceTransformer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOCS_DIR = os.path.join(BASE_DIR, "data", "docs")
INDEX_PATH = os.path.join(BASE_DIR, "index", "doc_index.pkl")

# 한국어에 강한 무료 임베딩 모델 (로컬 실행)
EMBED_MODEL_NAME = "jhgan/ko-sroberta-multitask"


def read_text(path):
    """문서 파일을 읽어 평문 텍스트로 반환 (.pdf 포함)."""
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError:
            raise ImportError("PDF 를 읽으려면 `pip3 install pypdf` 가 필요합니다.")
        reader = PdfReader(path)
        return "\n".join((page.extract_text() or "") for page in reader.pages)
    with open(path, encoding="utf-8") as f:
        return f.read()


def chunk_text(text, size=350, overlap=70):
    """긴 텍스트를 문단 경계를 고려해 일정 길이의 청크로 나눈다."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks, buf = [], ""
    for p in paragraphs:
        if len(buf) + len(p) <= size:
            buf = (buf + "\n" + p).strip()
        else:
            if buf:
                chunks.append(buf)
            # 문단이 너무 길면 슬라이딩 윈도우로 분할
            if len(p) > size:
                for i in range(0, len(p), size - overlap):
                    chunks.append(p[i:i + size])
                buf = ""
            else:
                buf = p
    if buf:
        chunks.append(buf)
    return chunks


def build_index():
    files = []
    for ext in ("*.md", "*.txt", "*.pdf"):
        files.extend(glob.glob(os.path.join(DOCS_DIR, ext)))

    if not files:
        print(f"[!] {DOCS_DIR} 에 문서가 없습니다. 문서를 넣고 다시 실행하세요.")
        return

    print(f"[1/3] 문서 {len(files)}개 로딩 및 청크 분할...")
    records = []  # {text, source}
    for path in files:
        text = read_text(path)
        for ch in chunk_text(text):
            records.append({"text": ch, "source": os.path.basename(path)})
    print(f"      총 청크 수: {len(records)}")

    print(f"[2/3] 임베딩 생성... ({EMBED_MODEL_NAME})")
    model = SentenceTransformer(EMBED_MODEL_NAME)
    embeddings = model.encode([r["text"] for r in records],
                              normalize_embeddings=True,
                              show_progress_bar=False)
    embeddings = np.asarray(embeddings, dtype="float32")

    print("[3/3] 인덱스 저장...")
    os.makedirs(os.path.dirname(INDEX_PATH), exist_ok=True)
    with open(INDEX_PATH, "wb") as f:
        pickle.dump({"records": records, "embeddings": embeddings,
                     "model_name": EMBED_MODEL_NAME}, f)
    print(f"      저장 완료 -> {INDEX_PATH}")


if __name__ == "__main__":
    build_index()
