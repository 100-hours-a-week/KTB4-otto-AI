# FastAPI 커뮤니티 백엔드 과제

## 1. 프로젝트 소개

이 프로젝트는 FastAPI를 사용해서 간단한 커뮤니티 서비스의 백엔드를 구현한 과제입니다.

이번 과제에서는 실제 데이터베이스를 연결하지 않고, Python 리스트를 임시 저장소처럼 사용했습니다.  
목표는 데이터베이스 연동보다 HTTP REST API의 구조와 FastAPI의 기본 사용 흐름을 이해하는 것입니다.

구현한 기능은 다음과 같습니다.

- 회원가입
- 로그인
- 회원 정보 조회
- 게시글 목록 조회
- 게시글 상세 조회
- 게시글 작성
- 게시글 전체 수정
- 게시글 일부 수정
- 게시글 삭제
- 특정 사용자가 작성한 글 조회

---

## 2. 프로젝트 구조

```text
community_backend_fastapi/
├── main.py
├── routers/
│   ├── user_router.py
│   └── post_router.py
├── controllers/
│   ├── user_controller.py
│   └── post_controller.py
├── models/
│   ├── user_model.py
│   └── post_model.py
├── requirements.txt
└── README.md
```

역할은 다음과 같이 나누었습니다.

| 구분 | 역할 |
|---|---|
| main.py | FastAPI 앱 생성 및 라우터 등록 |
| routers | URL과 HTTP Method를 기준으로 요청을 받는 부분 |
| controllers | 요청에 대한 실제 처리 로직을 담당하는 부분 |
| models | 임시 데이터 저장 및 조회를 담당하는 부분 |

---

## 3. 실행 방법

### 1) 패키지 설치

```bash
pip install -r requirements.txt
```

### 2) 서버 실행

```bash
uvicorn main:app --reload
```

### 3) 접속 확인

브라우저에서 아래 주소로 접속합니다.

```text
http://localhost:8000
```

FastAPI 자동 문서는 아래 주소에서 확인할 수 있습니다.

```text
http://localhost:8000/docs
```

---

## 4. REST API 설계

### User API

| 기능 | Method | URL |
|---|---|---|
| 회원가입 | POST | `/users` |
| 로그인 | POST | `/users/login` |
| 회원 정보 조회 | GET | `/users/{user_id}` |
| 특정 사용자가 작성한 글 조회 | GET | `/users/{user_id}/posts` |

### Post API

| 기능 | Method | URL |
|---|---|---|
| 게시글 목록 조회 | GET | `/posts` |
| 게시글 상세 조회 | GET | `/posts/{post_id}` |
| 게시글 작성 | POST | `/posts` |
| 게시글 전체 수정 | PUT | `/posts/{post_id}` |
| 게시글 일부 수정 | PATCH | `/posts/{post_id}` |
| 게시글 삭제 | DELETE | `/posts/{post_id}` |

---

## 5. 요청 예시

### 회원가입

```http
POST /users
```

```json
{
  "email": "minwoo@example.com",
  "password": "1234",
  "nickname": "민우"
}
```

### 로그인

```http
POST /users/login
```

```json
{
  "email": "minwoo@example.com",
  "password": "1234"
}
```

### 게시글 작성

```http
POST /posts
```

```json
{
  "title": "첫 게시글",
  "content": "FastAPI로 게시글을 작성했습니다.",
  "author_id": 1
}
```

### 게시글 전체 수정

```http
PUT /posts/1
```

```json
{
  "title": "수정된 제목",
  "content": "수정된 내용입니다."
}
```

### 게시글 일부 수정

```http
PATCH /posts/1
```

```json
{
  "title": "제목만 수정"
}
```

---

## 6. HTTP Status Code 사용

이번 과제에서는 요청 결과에 따라 다음 상태 코드를 사용했습니다.

| 상태 코드 | 사용 상황 |
|---|---|
| 200 OK | 조회, 로그인, 수정 성공 |
| 201 Created | 회원가입, 게시글 작성 성공 |
| 204 No Content | 게시글 삭제 성공 |
| 400 Bad Request | 수정할 값이 없는 경우 |
| 401 Unauthorized | 로그인 실패 |
| 404 Not Found | 사용자 또는 게시글을 찾을 수 없는 경우 |
| 409 Conflict | 이미 가입된 이메일인 경우 |

---

## 7. 느낀 점

이번 과제를 진행하면서 HTTP Method와 URL을 함께 사용해서 API의 의미를 표현하는 방식을 이해할 수 있었습니다.

처음에는 단순히 서버에 요청을 보내고 응답을 받는다고만 생각했지만, 실제로는 `GET`, `POST`, `PUT`, `PATCH`, `DELETE` 같은 Method를 목적에 맞게 사용해야 한다는 것을 알게 되었습니다.

또한 URL은 행위를 적는 곳이 아니라 자원을 표현하는 곳이라는 점이 중요했습니다.  
예를 들어 `/getPosts`처럼 작성하는 것보다 `GET /posts`처럼 작성하는 것이 REST API 설계 방식에 더 적절하다는 것을 배웠습니다.

아직 실제 데이터베이스를 연결하지는 않았지만, 리스트를 임시 저장소로 사용하면서 백엔드 API의 기본 흐름을 먼저 익힐 수 있었습니다.
