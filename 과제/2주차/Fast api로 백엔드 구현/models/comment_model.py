comments = [
    {
        "id": 1,
        "post_id": 1,
        "content": "첫 번째 댓글입니다.",
        "username": "minwoo",
    }
]

next_comment_id = 2


def get_comments_by_post_id(post_id: int):
    result = []

    for comment in comments:
        if comment["post_id"] == post_id:
            result.append(comment)

    return result


def get_comment_by_id(comment_id: int):
    for comment in comments:
        if comment["id"] == comment_id:
            return comment
    return None


def add_comment(post_id: int, content: str, username: str):
    global next_comment_id

    new_comment = {
        "id": next_comment_id,
        "post_id": post_id,
        "content": content,
        "username": username,
    }

    comments.append(new_comment)
    next_comment_id += 1

    return new_comment


def patch_comment(comment_id: int, content=None, username=None):
    comment = get_comment_by_id(comment_id)

    if content is not None:
        comment["content"] = content

    if username is not None:
        comment["username"] = username

    return comment


def delete_comment(comment_id: int):
    comment = get_comment_by_id(comment_id)

    if comment:
        comments.remove(comment)


def delete_comments_by_post_id(post_id: int):
    target_comments = get_comments_by_post_id(post_id)

    for comment in target_comments:
        comments.remove(comment)
