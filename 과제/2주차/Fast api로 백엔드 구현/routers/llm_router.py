from fastapi import APIRouter

from controllers import llm_controller


router = APIRouter(tags=["llm"])


@router.get("/posts/{post_id}/summary")
def summarize_post(post_id: int):
    return llm_controller.summarize_post(post_id)


@router.get("/comments/{comment_id}/summary")
def summarize_comment(comment_id: int):
    return llm_controller.summarize_comment(comment_id)


@router.get("/posts/{post_id}/comments/{comment_id}/summary")
def summarize_comment_in_post(post_id: int, comment_id: int):
    return llm_controller.summarize_comment_in_post(post_id, comment_id)
