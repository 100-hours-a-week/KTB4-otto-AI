from fastapi import FastAPI
from routers.user_router import router as user_router
from routers.post_router import router as post_router

app = FastAPI(title="Community Backend API")

app.include_router(user_router)
app.include_router(post_router)


@app.get("/")
def root():
    return {
        "message": "Community Backend API",
        "description": "FastAPI로 만든 간단한 커뮤니티 백엔드입니다.",
    }
