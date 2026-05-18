from fastapi import HTTPException

from models import post_model, comment_model


def get_posts():
    posts = post_model.get_posts()

    return {
        "message": "글 목록 조회 성공",
        "data": posts,
    }


def get_post(post_id: int):
    post = post_model.get_post_by_id(post_id)

    if not post:
        raise HTTPException(status_code=404, detail="글을 찾을 수 없습니다.")

    return {
        "message": "글 상세 조회 성공",
        "data": post,
    }


def create_post(post_data):
    new_post = post_model.add_post(
        title=post_data.title,
        content=post_data.content,
        username=post_data.username,
    )

    return {
        "message": "글 작성 성공",
        "data": new_post,
    }


def update_post(post_id: int, post_data):
    post = post_model.get_post_by_id(post_id)

    if not post:
        raise HTTPException(status_code=404, detail="글을 찾을 수 없습니다.")

    updated_post = post_model.update_post(
        post_id=post_id,
        title=post_data.title,
        content=post_data.content,
        username=post_data.username,
    )

    return {
        "message": "글 전체 수정 성공",
        "data": updated_post,
    }


def patch_post(post_id: int, post_data):
    post = post_model.get_post_by_id(post_id)

    if not post:
        raise HTTPException(status_code=404, detail="글을 찾을 수 없습니다.")

    if post_data.title is None and post_data.content is None and post_data.username is None:
        raise HTTPException(status_code=400, detail="수정할 값이 없습니다.")

    updated_post = post_model.patch_post(
        post_id=post_id,
        title=post_data.title,
        content=post_data.content,
        username=post_data.username,
    )

    return {
        "message": "글 일부 수정 성공",
        "data": updated_post,
    }


def delete_post(post_id: int):
    post = post_model.get_post_by_id(post_id)

    if not post:
        raise HTTPException(status_code=404, detail="글을 찾을 수 없습니다.")

    post_model.delete_post(post_id)
    comment_model.delete_comments_by_post_id(post_id)
