from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from controllers import comment_controller


router = APIRouter(tags=["comments"])


class CommentCreate(BaseModel):
    content: str
    username: str


class CommentPatch(BaseModel):
    content: Optional[str] = None
    username: Optional[str] = None


@router.get("/posts/{post_id}/comments")
def get_comments(post_id: int):
    return comment_controller.get_comments(post_id)


@router.post("/posts/{post_id}/comments", status_code=201)
def create_comment(post_id: int, comment_data: CommentCreate):
    return comment_controller.create_comment(post_id, comment_data)


@router.patch("/comments/{comment_id}")
def patch_comment(comment_id: int, comment_data: CommentPatch):
    return comment_controller.patch_comment(comment_id, comment_data)


@router.delete("/comments/{comment_id}", status_code=204)
def delete_comment(comment_id: int):
    comment_controller.delete_comment(comment_id)
    return None
