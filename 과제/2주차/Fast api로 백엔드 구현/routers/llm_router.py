from fastapi import APIRouter

from controllers import llm_controller


router = APIRouter(tags=["llm"])


@router.post("/posts/{post_id}/summary")
def summarize_post(post_id: int):
    return llm_controller.summarize_post(post_id)
