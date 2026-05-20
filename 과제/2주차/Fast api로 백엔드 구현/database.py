import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).resolve().parent / "community.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                username TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                username TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (post_id) REFERENCES posts (id) ON DELETE CASCADE
            )
            """
        )

        post_count = conn.execute("SELECT COUNT(*) AS count FROM posts").fetchone()["count"]

        if post_count == 0:
            cursor = conn.execute(
                """
                INSERT INTO posts (title, content, username)
                VALUES (?, ?, ?)
                """,
                (
                    "첫 번째 글",
                    "FastAPI로 만든 글 CRUD 예시입니다.",
                    "minwoo",
                ),
            )

            first_post_id = cursor.lastrowid

            conn.execute(
                """
                INSERT INTO comments (post_id, content, username)
                VALUES (?, ?, ?)
                """,
                (
                    first_post_id,
                    "첫 번째 댓글입니다.",
                    "minwoo",
                ),
            )
