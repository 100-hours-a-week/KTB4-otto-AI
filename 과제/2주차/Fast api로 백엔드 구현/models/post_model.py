from database import get_connection


def _row_to_dict(row):
    if row is None:
        return None

    return dict(row)


def get_posts():
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, title, content, username, created_at
            FROM posts
            ORDER BY id DESC
            """
        ).fetchall()

    return [dict(row) for row in rows]


def get_post_by_id(post_id: int):
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id, title, content, username, created_at
            FROM posts
            WHERE id = ?
            """,
            (post_id,),
        ).fetchone()

    return _row_to_dict(row)


def add_post(title: str, content: str, username: str):
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO posts (title, content, username)
            VALUES (?, ?, ?)
            """,
            (title, content, username),
        )

        post_id = cursor.lastrowid

    return get_post_by_id(post_id)


def update_post(post_id: int, title: str, content: str, username: str):
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE posts
            SET title = ?, content = ?, username = ?
            WHERE id = ?
            """,
            (title, content, username, post_id),
        )

    return get_post_by_id(post_id)


def patch_post(post_id: int, title=None, content=None, username=None):
    post = get_post_by_id(post_id)

    new_title = title if title is not None else post["title"]
    new_content = content if content is not None else post["content"]
    new_username = username if username is not None else post["username"]

    with get_connection() as conn:
        conn.execute(
            """
            UPDATE posts
            SET title = ?, content = ?, username = ?
            WHERE id = ?
            """,
            (new_title, new_content, new_username, post_id),
        )

    return get_post_by_id(post_id)


def delete_post(post_id: int):
    with get_connection() as conn:
        conn.execute(
            """
            DELETE FROM posts
            WHERE id = ?
            """,
            (post_id,),
        )
