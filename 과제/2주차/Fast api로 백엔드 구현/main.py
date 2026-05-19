from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from routers.post_router import router as post_router
from routers.comment_router import router as comment_router
from routers.llm_router import router as llm_router

app = FastAPI(
    title="FastAPI로 백엔드 구현",
    description="메모리 변수를 사용해 글 CRUD와 댓글 CRUD를 구현한 과제입니다.",
    version="1.0.0",
)

app.include_router(post_router)
app.include_router(comment_router)
app.include_router(llm_router)


@app.get("/", response_class=HTMLResponse)
def root():
    return """
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <title>FastAPI로 백엔드 구현</title>
        <style>
            body {
                margin: 0;
                padding: 40px;
                font-family: Arial, sans-serif;
                background-color: #f5f6fa;
                color: #222;
            }
            .container {
                max-width: 850px;
                margin: 0 auto;
                background-color: white;
                padding: 36px;
                border-radius: 16px;
                box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
            }
            h1 {
                margin-bottom: 12px;
            }
            p {
                line-height: 1.7;
                color: #555;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 16px;
            }
            th, td {
                border: 1px solid #ddd;
                padding: 10px;
                text-align: left;
            }
            th {
                background-color: #f1f3f5;
            }
            code {
                background-color: #f1f3f5;
                padding: 3px 6px;
                border-radius: 5px;
            }
            .button {
                display: inline-block;
                margin-top: 18px;
                padding: 11px 16px;
                background-color: #222;
                color: white;
                text-decoration: none;
                border-radius: 8px;
            }
            .note {
                background-color: #fff8e1;
                padding: 14px;
                border-radius: 10px;
                margin-top: 20px;
            }
        </style>
    </head>
    <body>
        <main class="container">
            <h1>FastAPI로 백엔드 구현</h1>
            <p>
                이 프로젝트는 FastAPI를 사용해 커뮤니티 서비스의 기본 백엔드 API를 구현한 과제입니다.
                인증 기능 없이 username을 입력받고, 데이터는 Python 리스트를 임시 저장소로 사용했습니다.
            </p>

            <a class="button" href="/docs">API 테스트 문서 열기</a>

            <h2>구현한 API</h2>
            <table>
                <tr>
                    <th>기능</th>
                    <th>Method</th>
                    <th>URL</th>
                </tr>
                <tr>
                    <td>글 작성</td>
                    <td>POST</td>
                    <td><code>/posts</code></td>
                </tr>
                <tr>
                    <td>글 목록 조회</td>
                    <td>GET</td>
                    <td><code>/posts</code></td>
                </tr>
                <tr>
                    <td>글 상세 조회</td>
                    <td>GET</td>
                    <td><code>/posts/{post_id}</code></td>
                </tr>
                <tr>
                    <td>글 전체 수정</td>
                    <td>PUT</td>
                    <td><code>/posts/{post_id}</code></td>
                </tr>
                <tr>
                    <td>글 일부 수정</td>
                    <td>PATCH</td>
                    <td><code>/posts/{post_id}</code></td>
                </tr>
                <tr>
                    <td>글 삭제</td>
                    <td>DELETE</td>
                    <td><code>/posts/{post_id}</code></td>
                </tr>
                <tr>
                    <td>댓글 작성</td>
                    <td>POST</td>
                    <td><code>/posts/{post_id}/comments</code></td>
                </tr>
                <tr>
                    <td>댓글 목록 조회</td>
                    <td>GET</td>
                    <td><code>/posts/{post_id}/comments</code></td>
                </tr>
                <tr>
                    <td>댓글 수정</td>
                    <td>PATCH</td>
                    <td><code>/comments/{comment_id}</code></td>
                </tr>
                <tr>
                    <td>댓글 삭제</td>
                    <td>DELETE</td>
                    <td><code>/comments/{comment_id}</code></td>
                </tr>
            </table>

            <div class="note">
                <strong>학습 포인트:</strong>
                HTTP Method, REST API URL 설계, JSON 요청/응답, 상태 코드, 메모리 기반 데이터 관리를 연습했습니다.
            </div>
        </main>
    </body>
    </html>
    """
