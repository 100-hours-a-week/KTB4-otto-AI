from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from controllers import post_controller


router = APIRouter(prefix="/posts", tags=["posts"])


class PostCreate(BaseModel):
    title: str
    content: str
    username: str


class PostUpdate(BaseModel):
    title: str
    content: str
    username: str


class PostPatch(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    username: Optional[str] = None


@router.get("")
def get_posts():
    return post_controller.get_posts()


@router.get("/{post_id}")
def get_post(post_id: int):
    return post_controller.get_post(post_id)


@router.post("", status_code=201)
def create_post(post_data: PostCreate):
    return post_controller.create_post(post_data)


@router.put("/{post_id}")
def update_post(post_id: int, post_data: PostUpdate):
    return post_controller.update_post(post_id, post_data)


@router.patch("/{post_id}")
def patch_post(post_id: int, post_data: PostPatch):
    return post_controller.patch_post(post_id, post_data)


@router.delete("/{post_id}", status_code=204)
def delete_post(post_id: int):
    post_controller.delete_post(post_id)
    return None
