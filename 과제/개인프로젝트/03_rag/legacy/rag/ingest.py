import os

os.environ.setdefault("USE_TF", "0")
os.environ.setdefault("TRANSFORMERS_NO_ADVISORY_WARNINGS", "1")

import glob
import pickle

import numpy as np
from sentence_transformers import SentenceTransformer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOCS_DIR = os.path.join(BASE_DIR, "data", "docs")
INDEX_PATH = os.path.join(BASE_DIR, "index", "doc_index.pkl")

EMBED_MODEL_NAME = "jhgan/ko-sroberta-multitask"

def read_text(path):
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
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks, buf = [], ""
    for p in paragraphs:
        if len(buf) + len(p) <= size:
            buf = (buf + "\n" + p).strip()
        else:
            if buf:
                chunks.append(buf)
            
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
    records = []  
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
