users = [
    {
        "id": 1,
        "email": "test@example.com",
        "password": "1234",
        "nickname": "테스트유저",
    }
]

next_user_id = 2


def get_users():
    return users


def get_user_by_id(user_id: int):
    for user in users:
        if user["id"] == user_id:
            return user
    return None


def get_user_by_email(email: str):
    for user in users:
        if user["email"] == email:
            return user
    return None


def add_user(email: str, password: str, nickname: str):
    global next_user_id

    new_user = {
        "id": next_user_id,
        "email": email,
        "password": password,
        "nickname": nickname,
    }

    users.append(new_user)
    next_user_id += 1

    return new_user
