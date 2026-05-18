from fastapi import HTTPException

from models import comment_model, post_model


def get_comments(post_id: int):
    post = post_model.get_post_by_id(post_id)

    if not post:
        raise HTTPException(status_code=404, detail="글을 찾을 수 없습니다.")

    comments = comment_model.get_comments_by_post_id(post_id)

    return {
        "message": "댓글 목록 조회 성공",
        "data": comments,
    }


def create_comment(post_id: int, comment_data):
    post = post_model.get_post_by_id(post_id)

    if not post:
        raise HTTPException(status_code=404, detail="글을 찾을 수 없습니다.")

    new_comment = comment_model.add_comment(
        post_id=post_id,
        content=comment_data.content,
        username=comment_data.username,
    )

    return {
        "message": "댓글 작성 성공",
        "data": new_comment,
    }


def patch_comment(comment_id: int, comment_data):
    comment = comment_model.get_comment_by_id(comment_id)

    if not comment:
        raise HTTPException(status_code=404, detail="댓글을 찾을 수 없습니다.")

    if comment_data.content is None and comment_data.username is None:
        raise HTTPException(status_code=400, detail="수정할 값이 없습니다.")

    updated_comment = comment_model.patch_comment(
        comment_id=comment_id,
        content=comment_data.content,
        username=comment_data.username,
    )

    return {
        "message": "댓글 수정 성공",
        "data": updated_comment,
    }


def delete_comment(comment_id: int):
    comment = comment_model.get_comment_by_id(comment_id)

    if not comment:
        raise HTTPException(status_code=404, detail="댓글을 찾을 수 없습니다.")

    comment_model.delete_comment(comment_id)
