posts = [
    {
        "id": 1,
        "title": "첫 번째 글",
        "content": "FastAPI로 만든 글 CRUD 예시입니다.",
        "username": "minwoo",
    }
]

next_post_id = 2


def get_posts():
    return posts


def get_post_by_id(post_id: int):
    for post in posts:
        if post["id"] == post_id:
            return post
    return None


def add_post(title: str, content: str, username: str):
    global next_post_id

    new_post = {
        "id": next_post_id,
        "title": title,
        "content": content,
        "username": username,
    }

    posts.append(new_post)
    next_post_id += 1

    return new_post


def update_post(post_id: int, title: str, content: str, username: str):
    post = get_post_by_id(post_id)

    post["title"] = title
    post["content"] = content
    post["username"] = username

    return post


def patch_post(post_id: int, title=None, content=None, username=None):
    post = get_post_by_id(post_id)

    if title is not None:
        post["title"] = title

    if content is not None:
        post["content"] = content

    if username is not None:
        post["username"] = username

    return post


def delete_post(post_id: int):
    post = get_post_by_id(post_id)

    if post:
        posts.remove(post)
