from database import get_connection


def _row_to_dict(row):
    if row is None:
        return None

    return dict(row)


def get_comments_by_post_id(post_id: int):
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, post_id, content, username, created_at
            FROM comments
            WHERE post_id = ?
            ORDER BY id ASC
            """,
            (post_id,),
        ).fetchall()

    return [dict(row) for row in rows]


def get_comment_by_id(comment_id: int):
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id, post_id, content, username, created_at
            FROM comments
            WHERE id = ?
            """,
            (comment_id,),
        ).fetchone()

    return _row_to_dict(row)


def add_comment(post_id: int, content: str, username: str):
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO comments (post_id, content, username)
            VALUES (?, ?, ?)
            """,
            (post_id, content, username),
        )

        comment_id = cursor.lastrowid

    return get_comment_by_id(comment_id)


def patch_comment(comment_id: int, content=None, username=None):
    comment = get_comment_by_id(comment_id)

    new_content = content if content is not None else comment["content"]
    new_username = username if username is not None else comment["username"]

    with get_connection() as conn:
        conn.execute(
            """
            UPDATE comments
            SET content = ?, username = ?
            WHERE id = ?
            """,
            (new_content, new_username, comment_id),
        )

    return get_comment_by_id(comment_id)


def delete_comment(comment_id: int):
    with get_connection() as conn:
        conn.execute(
            """
            DELETE FROM comments
            WHERE id = ?
            """,
            (comment_id,),
        )


def delete_comments_by_post_id(post_id: int):
    with get_connection() as conn:
        conn.execute(
            """
            DELETE FROM comments
            WHERE post_id = ?
            """,
            (post_id,),
        )
