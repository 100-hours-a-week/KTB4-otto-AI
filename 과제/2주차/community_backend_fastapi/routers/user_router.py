from fastapi import APIRouter
from pydantic import BaseModel

from controllers import user_controller


router = APIRouter(prefix="/users", tags=["users"])


class UserCreate(BaseModel):
    email: str
    password: str
    nickname: str


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("", status_code=201)
def signup(user_data: UserCreate):
    return user_controller.signup(user_data)


@router.post("/login")
def login(login_data: LoginRequest):
    return user_controller.login(login_data)


@router.get("/{user_id}")
def get_user(user_id: int):
    return user_controller.get_user(user_id)


@router.get("/{user_id}/posts")
def get_my_posts(user_id: int):
    return user_controller.get_user_posts(user_id)
