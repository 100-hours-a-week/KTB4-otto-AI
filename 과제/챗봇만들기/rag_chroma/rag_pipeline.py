import os
import re
import glob

os.environ.setdefault("USE_TF", "0")  
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")  

import chromadb
from chromadb.utils import embedding_functions

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOCS_DIR = os.path.join(BASE_DIR, "docs")
DB_DIR = os.path.join(BASE_DIR, "chroma_db")          
COLLECTION_NAME = "rag_demo"

EMBED_MODEL_NAME = "jhgan/ko-sroberta-multitask"

def load_documents():
    docs = []
    for path in glob.glob(os.path.join(DOCS_DIR, "*.md")) +                glob.glob(os.path.join(DOCS_DIR, "*.txt")):
        with open(path, encoding="utf-8") as f:
            text = f.read()
        docs.append((preprocess(text), os.path.basename(path)))
    return docs

def preprocess(text):
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def fixed_size_chunk(text, chunk_size=400, chunk_overlap=80):
    chunks = []
    start = 0
    step = chunk_size - chunk_overlap
    while start < len(text):
        chunk = text[start:start + chunk_size].strip()
        if chunk:
            chunks.append(chunk)
        start += step
    return chunks

def chunk_text(text, chunk_size=400, chunk_overlap=80):
    
    parts = re.split(r"\n(?=##\s)", text)
    chunks = []
    for part in parts:
        part = part.strip()
        
        if len(part) < 25:
            continue
        if len(part) <= chunk_size * 1.5:
            chunks.append(part)
        else:
            chunks.extend(fixed_size_chunk(part, chunk_size, chunk_overlap))
    return chunks

def get_client():
    return chromadb.PersistentClient(path=DB_DIR)

def get_embedding_function():
    
    return embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBED_MODEL_NAME
    )

def build_index(chunk_size=400, chunk_overlap=80):
    client = get_client()
    
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        embedding_function=get_embedding_function(),
        metadata={"hnsw:space": "cosine"},   
    )

    documents, metadatas, ids = [], [], []
    for text, source in load_documents():
        for i, chunk in enumerate(chunk_text(text, chunk_size, chunk_overlap)):
            documents.append(chunk)
            metadatas.append({"source": source, "chunk": i})
            ids.append(f"{source}-{i}")

    if not documents:
        print("[!] docs/ 에 문서가 없습니다.")
        return 0

    collection.add(documents=documents, metadatas=metadatas, ids=ids)
    print(f"인덱싱 완료: 청크 {len(documents)}개 → ChromaDB('{COLLECTION_NAME}')")
    return len(documents)

def get_collection():
    client = get_client()
    return client.get_collection(
        name=COLLECTION_NAME,
        embedding_function=get_embedding_function(),
    )

def search(query, n_results=3):
    collection = get_collection()
    res = collection.query(query_texts=[query], n_results=n_results)

    hits = []
    for doc, meta, dist in zip(res["documents"][0],
                               res["metadatas"][0],
                               res["distances"][0]):
        hits.append({
            "text": doc,
            "source": meta.get("source", "?"),
            "similarity": round(1 - dist, 3),   
        })
    return hits

if __name__ == "__main__":
    
    build_index()
    for q in ["어댑터즈 구독료 얼마야?", "환불 정책 알려줘", "부트캠프 몇 주 과정이야?"]:
        print(f"\nQ: {q}")
        for h in search(q, n_results=2):
            print(f"  [{h['source']} sim={h['similarity']}] {h['text'][:50]}...")
