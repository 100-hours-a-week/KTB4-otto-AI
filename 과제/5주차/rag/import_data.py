"""
내 데이터 가져오기 헬퍼
========================
폴더(예: 구글 드라이브 동기화 폴더, 다운로드 폴더)에서 파일을 골라
data/tables/ (표) 와 data/docs/ (문서) 로 복사한 뒤 문서 인덱스를 다시 만든다.

사용:
    python3 import_data.py "/Users/minwoo/Library/CloudStorage/GoogleDrive-.../실험데이터"
    python3 import_data.py ~/Downloads/my_experiment

확장자 기준 자동 분류:
    .csv .xlsx .xls          -> data/tables/   (pandas 로 계산)
    .md .txt .pdf            -> data/docs/     (임베딩 검색)
"""

import os
import sys
import glob
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TABLES_DIR = os.path.join(BASE_DIR, "data", "tables")
DOCS_DIR = os.path.join(BASE_DIR, "data", "docs")

TABLE_EXTS = {".csv", ".xlsx", ".xls"}
DOC_EXTS = {".md", ".txt", ".pdf"}


def main(src):
    src = os.path.expanduser(src)
    if not os.path.isdir(src):
        print(f"[!] 폴더를 찾을 수 없습니다: {src}")
        sys.exit(1)

    os.makedirs(TABLES_DIR, exist_ok=True)
    os.makedirs(DOCS_DIR, exist_ok=True)

    copied_tables, copied_docs = 0, 0
    # 하위 폴더까지 모두 탐색
    for path in glob.glob(os.path.join(src, "**", "*"), recursive=True):
        if not os.path.isfile(path):
            continue
        ext = os.path.splitext(path)[1].lower()
        if ext in TABLE_EXTS:
            shutil.copy2(path, TABLES_DIR)
            copied_tables += 1
            print(f"  [표]   {os.path.basename(path)}")
        elif ext in DOC_EXTS:
            shutil.copy2(path, DOCS_DIR)
            copied_docs += 1
            print(f"  [문서] {os.path.basename(path)}")

    print(f"\n표 {copied_tables}개, 문서 {copied_docs}개 복사 완료.")

    if copied_docs:
        print("문서 인덱스를 다시 만듭니다...")
        import ingest
        ingest.build_index()
    print("완료! 이제 서버를 실행하세요:  python3 -m uvicorn rag_app:app --reload")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법: python3 import_data.py <데이터가 있는 폴더 경로>")
        sys.exit(1)
    main(sys.argv[1])
