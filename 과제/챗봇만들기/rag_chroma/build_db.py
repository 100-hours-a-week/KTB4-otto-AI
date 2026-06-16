import rag_pipeline as rag

if __name__ == "__main__":
    n = rag.build_index()
    print(f"\n총 {n}개 청크를 ChromaDB 에 저장했습니다.")
    print("이제 서버를 실행하세요:  python3 -m uvicorn app:app --reload")
