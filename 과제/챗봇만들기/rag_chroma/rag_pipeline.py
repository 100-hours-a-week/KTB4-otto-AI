"""
RAG 파이프라인 (2026-06-15 수업 내용 그대로 구현)
====================================================
수업에서 배운 흐름:
  문서 로딩 → 전처리 → 청킹(chunk_size/overlap) → 임베딩(sentence-transformers)
  → ChromaDB 저장 → 질문 임베딩 → 유사도 검색(코사인/HNSW) → 검색 결과 반환

핵심 도구 (수업과 동일):
  - 임베딩: sentence-transformers
  - Vector DB: ChromaDB (collection, hnsw:space=cosine)
"""

import os
import re
import glob

os.environ.setdefault("USE_TF", "0")  # transformers 가 TF/Keras3 불러오지 않게
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")  # ChromaDB 텔레메트리 끄기

import chromadb
from chromadb.utils import embedding_functions

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOCS_DIR = os.path.join(BASE_DIR, "docs")
DB_DIR = os.path.join(BASE_DIR, "chroma_db")          # ChromaDB 영구 저장 위치
COLLECTION_NAME = "rag_demo"

# 임베딩 모델 (sentence-transformers). 수업 예시는 all-MiniLM-L6-v2 였지만,
# 한국어 검색 정확도를 위해 한국어 전용 모델(ko-sroberta)을 사용한다.
EMBED_MODEL_NAME = "jhgan/ko-sroberta-multitask"


# ---------------------------------------------------------------------------
# 1. 문서 로딩 + 전처리
# ---------------------------------------------------------------------------
def load_documents():
    """docs/ 안의 .md/.txt 파일을 읽어 (텍스트, 출처) 리스트로 반환."""
    docs = []
    for path in glob.glob(os.path.join(DOCS_DIR, "*.md")) + \
                glob.glob(os.path.join(DOCS_DIR, "*.txt")):
        with open(path, encoding="utf-8") as f:
            text = f.read()
        docs.append((preprocess(text), os.path.basename(path)))
    return docs


def preprocess(text):
    """간단한 전처리: 과도한 공백/빈 줄 정리."""
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# ---------------------------------------------------------------------------
# 2. 청킹
# ---------------------------------------------------------------------------
def fixed_size_chunk(text, chunk_size=400, chunk_overlap=80):
    """
    [Fixed-size 청킹] chunk_size 글자 단위로 자르되 chunk_overlap 만큼 겹치게 한다.
    겹침(overlap)은 청크 경계에서 문맥이 끊기는 것을 막아준다.
    """
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
    """
    [Delimiter 청킹] 마크다운 '## 제목' 을 기준으로 섹션 단위로 나눈다.
    주제별로 청크가 나뉘어 검색 정확도가 좋아진다(수업 13장: Regex & Delimiter Chunking).
    섹션이 너무 길면 Fixed-size 로 한 번 더 쪼갠다.
    """
    # '## ' 헤더 기준 분할 (헤더 텍스트는 각 섹션에 포함시켜 문맥 유지)
    parts = re.split(r"\n(?=##\s)", text)
    chunks = []
    for part in parts:
        part = part.strip()
        # 제목만 있는 짧은 조각(예: 문서 맨 위 '# 제목')은 검색에 방해 → 제외
        if len(part) < 25:
            continue
        if len(part) <= chunk_size * 1.5:
            chunks.append(part)
        else:
            chunks.extend(fixed_size_chunk(part, chunk_size, chunk_overlap))
    return chunks


# ---------------------------------------------------------------------------
# 3. 인덱싱 (임베딩 → ChromaDB 저장)
# ---------------------------------------------------------------------------
def get_client():
    return chromadb.PersistentClient(path=DB_DIR)


def get_embedding_function():
    # ChromaDB 가 add/query 시 자동으로 임베딩하도록 임베딩 함수를 등록
    return embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBED_MODEL_NAME
    )


def build_index(chunk_size=400, chunk_overlap=80):
    """문서를 청킹·임베딩하여 ChromaDB 컬렉션에 저장한다."""
    client = get_client()
    # 기존 컬렉션이 있으면 새로 만들기 위해 삭제
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        embedding_function=get_embedding_function(),
        metadata={"hnsw:space": "cosine"},   # 코사인 유사도 + HNSW 인덱스 (수업 내용)
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

    # add() 호출 시 embedding_function 이 자동으로 임베딩을 계산해 저장
    collection.add(documents=documents, metadatas=metadatas, ids=ids)
    print(f"인덱싱 완료: 청크 {len(documents)}개 → ChromaDB('{COLLECTION_NAME}')")
    return len(documents)


# ---------------------------------------------------------------------------
# 4. 검색 (질문 임베딩 → 유사도 검색)
# ---------------------------------------------------------------------------
def get_collection():
    client = get_client()
    return client.get_collection(
        name=COLLECTION_NAME,
        embedding_function=get_embedding_function(),
    )


def search(query, n_results=3):
    """
    질문과 가장 유사한 청크 top-k 를 ChromaDB 에서 검색한다.
    ChromaDB 의 distance 는 '거리'(작을수록 유사) → 유사도로 변환해 함께 반환.
    """
    collection = get_collection()
    res = collection.query(query_texts=[query], n_results=n_results)

    hits = []
    for doc, meta, dist in zip(res["documents"][0],
                               res["metadatas"][0],
                               res["distances"][0]):
        hits.append({
            "text": doc,
            "source": meta.get("source", "?"),
            "similarity": round(1 - dist, 3),   # cosine distance → similarity
        })
    return hits


if __name__ == "__main__":
    # CLI 테스트: 인덱스 만들고 검색해보기
    build_index()
    for q in ["어댑터즈 구독료 얼마야?", "환불 정책 알려줘", "부트캠프 몇 주 과정이야?"]:
        print(f"\nQ: {q}")
        for h in search(q, n_results=2):
            print(f"  [{h['source']} sim={h['similarity']}] {h['text'][:50]}...")
