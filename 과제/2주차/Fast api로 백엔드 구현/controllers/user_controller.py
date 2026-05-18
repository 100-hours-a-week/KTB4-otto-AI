from fastapi import HTTPException

from models import user_model, post_model


def _hide_password(user: dict):
    return {
        "id": user["id"],
        "email": user["email"],
        "nickname": user["nickname"],
    }


def signup(user_data):
    existing_user = user_model.get_user_by_email(user_data.email)

    if existing_user:
        raise HTTPException(status_code=409, detail="이미 가입된 이메일입니다.")

    new_user = user_model.add_user(
        email=user_data.email,
        password=user_data.password,
        nickname=user_data.nickname,
    )

    return {
        "message": "회원가입 성공",
        "data": _hide_password(new_user),
    }


def login(login_data):
    user = user_model.get_user_by_email(login_data.email)

    if not user or user["password"] != login_data.password:
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다.")

    return {
        "message": "로그인 성공",
        "data": {
            "user_id": user["id"],
            "nickname": user["nickname"],
        },
    }


def get_user(user_id: int):
    user = user_model.get_user_by_id(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    return {
        "message": "회원 조회 성공",
        "data": _hide_password(user),
    }


def get_user_posts(user_id: int):
    user = user_model.get_user_by_id(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    posts = post_model.get_posts_by_author(user_id)

    return {
        "message": "내가 쓴 글 조회 성공",
        "data": posts,
    }
