"""
ChromaDB 인덱스 빌드 (Indexing 단계)
=====================================
docs/ 의 문서를 청킹·임베딩하여 ChromaDB 에 저장한다.
실행:  python3 build_db.py
"""

import rag_pipeline as rag

if __name__ == "__main__":
    n = rag.build_index()
    print(f"\n총 {n}개 청크를 ChromaDB 에 저장했습니다.")
    print("이제 서버를 실행하세요:  python3 -m uvicorn app:app --reload")
