# 1. HTTP 내용 정리

## HTTP란?

HTTP는 **HyperText Transfer Protocol**의 줄임말로, 웹에서 클라이언트와 서버가 데이터를 주고받기 위해 사용하는 통신 규칙이다.

처음에는 HTTP를 단순히 “웹사이트를 열 때 쓰는 것” 정도로만 생각했다. 하지만 이번에 학습하면서 HTTP는 브라우저와 서버가 서로 요청하고 응답하기 위해 정해둔 약속이라는 것을 알게 되었다.

예를 들어 사용자가 브라우저에서 게시글 목록 페이지에 들어가면, 브라우저는 서버에게 “게시글 목록을 보내줘”라고 요청한다. 그러면 서버는 요청을 처리한 뒤 게시글 데이터를 응답으로 보내준다. 이때 클라이언트와 서버가 사용하는 기본 규칙이 HTTP이다.

즉, HTTP는 웹에서 데이터를 주고받기 위한 기본 언어라고 볼 수 있다.

---

## 클라이언트와 서버

HTTP를 이해하기 위해서는 먼저 클라이언트와 서버 구조를 알아야 한다.

클라이언트는 요청을 보내는 쪽이다. 웹에서는 보통 브라우저가 클라이언트 역할을 한다. 사용자가 버튼을 클릭하거나 주소창에 URL을 입력하면, 브라우저가 서버에게 요청을 보낸다.

서버는 요청을 받아 처리하고 결과를 응답하는 쪽이다. 예를 들어 로그인 요청이 들어오면 서버는 아이디와 비밀번호를 확인하고, 성공 또는 실패 결과를 클라이언트에게 돌려준다.

정리하면 다음과 같다.

| 구분 | 역할 |
|---|---|
| 클라이언트 | 서버에게 필요한 데이터나 기능을 요청하는 쪽 |
| 서버 | 클라이언트의 요청을 처리하고 결과를 응답하는 쪽 |

HTTP는 이 클라이언트와 서버 사이에서 요청과 응답이 오갈 수 있도록 도와주는 규칙이다.

---

## URL이란?

URL은 웹에서 특정 리소스의 위치를 나타내는 주소이다.

예를 들어 아래와 같은 주소가 있다고 하면,

```text
https://example.com/posts/1?category=notice
```

이 URL은 여러 부분으로 나눌 수 있다.

| 구성 요소 | 예시 | 의미 |
|---|---|---|
| 프로토콜 | `https` | 어떤 통신 규칙을 사용할지 |
| 도메인 | `example.com` | 접속하려는 서버 주소 |
| 경로 | `/posts/1` | 서버 안에서 접근하려는 리소스 위치 |
| 쿼리 문자열 | `?category=notice` | 서버에 추가로 전달하는 조건 |

URL은 단순한 주소가 아니라, 클라이언트가 서버의 어떤 자원에 접근하고 싶은지를 나타내는 정보이다.

---

## HTTP Message

HTTP 통신에서 클라이언트와 서버가 주고받는 메시지를 HTTP Message라고 한다.

HTTP Message는 크게 요청 메시지와 응답 메시지로 나뉜다.

클라이언트가 서버에게 보내는 것은 **HTTP Request**, 서버가 클라이언트에게 돌려주는 것은 **HTTP Response**이다.

HTTP Message는 보통 다음과 같은 구조를 가진다.

| 구성 요소 | 설명 |
|---|---|
| Start Line | 요청 또는 응답의 첫 줄 |
| Headers | 요청이나 응답에 대한 추가 정보 |
| Empty Line | 헤더와 본문을 구분하는 빈 줄 |
| Body | 실제 전달되는 데이터 |

예를 들어 클라이언트가 게시글을 작성할 때는 다음과 같은 HTTP 요청을 보낼 수 있다.

```http
POST /posts HTTP/1.1
Host: example.com
Content-Type: application/json

{
  "title": "첫 번째 게시글",
  "content": "HTTP를 학습했습니다."
}
```

여기서 `POST /posts`는 서버에게 게시글을 생성하라는 요청이고, Body에는 실제 게시글 데이터가 JSON 형태로 담겨 있다.

---

## HTTP Request Method

HTTP Request Method는 클라이언트가 서버에게 어떤 작업을 원하는지 알려주는 방법이다.

대표적인 HTTP Method는 다음과 같다.

| Method | 의미 | 사용 예시 |
|---|---|---|
| GET | 데이터 조회 | 게시글 목록 조회 |
| POST | 데이터 생성 | 새 게시글 작성 |
| PUT | 데이터 전체 수정 | 회원 정보 전체 수정 |
| PATCH | 데이터 일부 수정 | 비밀번호만 변경 |
| DELETE | 데이터 삭제 | 게시글 삭제 |

예를 들어 게시글 목록을 가져오고 싶다면 `GET /posts`를 사용할 수 있다.

```http
GET /posts
```

새 게시글을 작성하고 싶다면 `POST /posts`를 사용할 수 있다.

```http
POST /posts
```

특정 게시글을 삭제하고 싶다면 `DELETE /posts/1`처럼 작성할 수 있다.

```http
DELETE /posts/1
```

이번 학습을 통해 URL은 “어떤 자원인지”를 나타내고, Method는 “그 자원에 대해 어떤 행동을 할 것인지”를 나타낸다는 것을 이해했다.

---

## Query String과 Path Variable

HTTP 요청에서 서버에 값을 전달하는 방식에는 Query String과 Path Variable이 있다.

### Path Variable

Path Variable은 특정 리소스를 식별할 때 사용한다.

예를 들어 1번 게시글을 조회하려면 다음과 같이 작성할 수 있다.

```http
GET /posts/1
```

여기서 `1`은 게시글의 ID이다. 즉, `/posts/1`은 “1번 게시글을 조회하겠다”는 의미이다.

### Query String

Query String은 검색, 필터링, 정렬, 페이지네이션처럼 추가 조건을 전달할 때 사용한다.

```http
GET /posts?category=notice&page=1
```

여기서 `category=notice`와 `page=1`은 서버에게 전달하는 추가 조건이다.

정리하면 다음과 같다.

| 구분 | 사용 목적 | 예시 |
|---|---|---|
| Path Variable | 특정 리소스 식별 | `/posts/1` |
| Query String | 검색, 필터, 정렬, 페이지 조건 전달 | `/posts?category=notice&page=1` |

---

## HTTP Status Code

HTTP Status Code는 서버가 클라이언트의 요청을 처리한 결과를 숫자로 알려주는 코드이다.

예를 들어 요청이 성공했는지, 클라이언트가 잘못 요청했는지, 서버에서 문제가 발생했는지를 상태 코드로 구분할 수 있다.

| 번호대 | 의미 |
|---|---|
| 2xx | 요청 성공 |
| 3xx | 리다이렉션 |
| 4xx | 클라이언트 오류 |
| 5xx | 서버 오류 |

자주 사용하는 상태 코드는 다음과 같다.

| 상태 코드 | 의미 | 예시 |
|---|---|---|
| 200 OK | 요청 성공 | 게시글 조회 성공 |
| 201 Created | 리소스 생성 성공 | 게시글 작성 성공 |
| 204 No Content | 성공했지만 응답할 내용 없음 | 삭제 성공 |
| 400 Bad Request | 잘못된 요청 | 필수 값 누락 |
| 401 Unauthorized | 인증 필요 | 로그인하지 않음 |
| 403 Forbidden | 권한 없음 | 관리자 페이지 접근 실패 |
| 404 Not Found | 리소스를 찾을 수 없음 | 없는 게시글 조회 |
| 422 Unprocessable Entity | 요청 데이터 검증 실패 | 타입 오류, 필드 누락 |
| 500 Internal Server Error | 서버 내부 오류 | 서버 코드 문제 |

상태 코드를 사용하면 클라이언트는 서버의 응답 결과를 명확하게 이해할 수 있다. 예를 들어 로그인하지 않은 사용자가 글 작성 요청을 보내면 서버는 `401 Unauthorized`를 응답할 수 있다.

---

## JSON과 HTTP

HTTP 통신에서 데이터를 주고받을 때는 JSON 형식을 많이 사용한다.

JSON은 key-value 형태로 데이터를 표현하는 형식이다.

예를 들어 게시글 데이터는 다음과 같이 표현할 수 있다.

```json
{
  "id": 1,
  "title": "HTTP 학습",
  "content": "HTTP 요청과 응답 구조를 배웠습니다."
}
```

JSON은 사람이 읽기 쉽고, JavaScript, Python 등 여러 언어에서 쉽게 사용할 수 있기 때문에 웹 API에서 많이 사용된다.

FastAPI에서도 딕셔너리나 리스트를 반환하면 자동으로 JSON 형태로 응답된다.

```python
@app.get("/posts")
def get_posts():
    return {
        "message": "게시글 조회 성공",
        "data": [
            {
                "id": 1,
                "title": "HTTP 학습"
            }
        ]
    }
```

이처럼 HTTP는 요청과 응답의 규칙을 제공하고, JSON은 그 안에서 실제 데이터를 표현하는 형식으로 사용된다.

---

## REST API와 HTTP

REST API는 HTTP를 더 일관성 있게 사용하기 위한 API 설계 방식이다.

REST API에서는 URL은 자원을 나타내고, HTTP Method는 행위를 나타낸다.

예를 들어 게시글 기능을 REST API로 설계하면 다음과 같이 만들 수 있다.

| 기능 | HTTP Method | URL |
|---|---|---|
| 게시글 목록 조회 | GET | `/posts` |
| 게시글 상세 조회 | GET | `/posts/{post_id}` |
| 게시글 작성 | POST | `/posts` |
| 게시글 전체 수정 | PUT | `/posts/{post_id}` |
| 게시글 일부 수정 | PATCH | `/posts/{post_id}` |
| 게시글 삭제 | DELETE | `/posts/{post_id}` |

좋지 않은 예시는 다음과 같다.

```http
GET /getPosts
POST /deletePost
GET /createPost
```

이런 방식은 URL 안에 행위가 들어가 있어서 일관성이 떨어진다.

REST API에서는 다음처럼 생각하는 것이 좋다.

```text
URL = 자원
HTTP Method = 행위
```

즉, `/posts`는 게시글이라는 자원을 의미하고, `GET`, `POST`, `DELETE` 같은 Method가 그 자원에 대한 행동을 의미한다.

---

## 내가 이해한 HTTP 흐름

이번에 HTTP를 학습하면서 웹 요청이 단순히 “주소를 입력하면 페이지가 열린다”가 아니라는 것을 알게 되었다.

사용자가 브라우저에서 URL을 입력하거나 버튼을 클릭하면, 클라이언트는 HTTP Request Message를 만든다. 이 요청에는 Method, URL, Header, Body 등이 포함될 수 있다.

서버는 이 요청을 받아서 어떤 자원에 대한 어떤 작업인지 확인한다. 그 후 필요한 로직을 처리하고, 결과를 HTTP Response Message로 반환한다. 응답에는 상태 코드와 JSON 데이터가 포함될 수 있다.

전체 흐름을 정리하면 다음과 같다.

```text
1. 사용자가 브라우저에서 요청을 보낸다.
2. 클라이언트는 HTTP Request를 생성한다.
3. 요청에는 Method, URL, Header, Body 등이 포함된다.
4. 서버는 요청을 해석하고 필요한 작업을 처리한다.
5. 서버는 HTTP Status Code와 함께 응답을 반환한다.
6. 클라이언트는 응답 데이터를 화면에 보여주거나 다음 동작을 수행한다.
```

HTTP는 웹 개발에서 가장 기본이 되는 개념이다. 특히 FastAPI로 백엔드를 구현할 때도 결국 클라이언트가 HTTP Method와 URL로 요청을 보내고, 서버가 JSON과 상태 코드로 응답하는 구조를 사용한다. 따라서 HTTP를 이해하는 것은 REST API 설계와 백엔드 구현의 출발점이라고 생각한다.
