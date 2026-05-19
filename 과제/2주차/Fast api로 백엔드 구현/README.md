# FastAPI로 백엔드 구현

## 프로젝트 소개

FastAPI를 사용하여 간단한 커뮤니티 서비스의 백엔드 REST API를 구현한 과제입니다.

이번 과제에서는 실제 데이터베이스를 연결하지 않고, Python 리스트를 메모리 저장소처럼 사용했습니다.  
목표는 HTTP Method, REST API URL 설계, JSON 요청/응답 구조, 상태 코드의 기본 흐름을 이해하는 것입니다.

인증 기능과 파일 업로드 기능은 구현하지 않았습니다.  
사용자는 로그인 없이 username을 요청 Body에 입력하는 방식으로 처리했습니다.

## 구현 기능

- 글 작성
- 글 목록 조회
- 글 상세 조회
- 글 전체 수정
- 글 일부 수정
- 글 삭제
- 댓글 작성
- 댓글 목록 조회
- 댓글 수정
- 댓글 삭제

## 프로젝트 구조

| 구분 | 역할 |
|---|---|
| main.py | FastAPI 앱 생성 및 라우터 등록 |
| routers | URL과 HTTP Method 기준으로 요청을 받는 부분 |
| controllers | 요청에 대한 처리 로직을 담당하는 부분 |
| models | 메모리 데이터 저장 및 조회를 담당하는 부분 |

## 실행 방법

1. 패키지 설치

pip install -r requirements.txt

2. 서버 실행

uvicorn main:app --reload

3. 브라우저에서 확인

http://127.0.0.1:8000

4. API 문서 확인

http://127.0.0.1:8000/docs

## REST API 설계

### 글 API

| 기능 | Method | URL |
|---|---|---|
| 글 작성 | POST | /posts |
| 글 목록 조회 | GET | /posts |
| 글 상세 조회 | GET | /posts/{post_id} |
| 글 전체 수정 | PUT | /posts/{post_id} |
| 글 일부 수정 | PATCH | /posts/{post_id} |
| 글 삭제 | DELETE | /posts/{post_id} |

### 댓글 API

| 기능 | Method | URL |
|---|---|---|
| 댓글 작성 | POST | /posts/{post_id}/comments |
| 댓글 목록 조회 | GET | /posts/{post_id}/comments |
| 댓글 수정 | PATCH | /comments/{comment_id} |
| 댓글 삭제 | DELETE | /comments/{comment_id} |

## 요청 예시

글 작성 요청 Body 예시

{
  "title": "FastAPI 과제",
  "content": "HTTP REST API를 설계하고 구현했습니다.",
  "username": "minwoo"
}

댓글 작성 요청 Body 예시

{
  "content": "좋은 글입니다.",
  "username": "minwoo"
}

## 사용한 상태 코드

| 상태 코드 | 사용 상황 |
|---|---|
| 200 OK | 조회, 수정 성공 |
| 201 Created | 글 작성, 댓글 작성 성공 |
| 204 No Content | 글 삭제, 댓글 삭제 성공 |
| 400 Bad Request | 수정할 값이 없는 경우 |
| 404 Not Found | 글 또는 댓글을 찾을 수 없는 경우 |

## 한 줄 정리

HTTP는 클라이언트와 서버가 요청과 응답을 주고받기 위해 사용하는 웹 통신 규칙입니다.

JSON은 클라이언트와 서버가 데이터를 주고받을 때 사용하는 key-value 형태의 구조화된 데이터 형식입니다.

REST API는 URL로 자원을 표현하고, HTTP Method로 행위를 표현하는 API 설계 방식입니다.

## 느낀 점

이번 과제를 통해 HTTP Method와 URL을 함께 사용해 API의 의미를 표현하는 방식을 이해할 수 있었습니다.

처음에는 서버에 요청을 보내고 응답을 받는다는 개념만 알고 있었지만, 실제로 API를 설계해보니 GET, POST, PUT, PATCH, DELETE를 목적에 맞게 나누는 것이 중요하다는 것을 알게 되었습니다.

또한 URL에는 동작을 직접 적기보다 자원을 표현하고, 동작은 HTTP Method로 나타내는 것이 REST API 설계에서 중요하다는 점을 배웠습니다.

이번 구현에서는 실제 데이터베이스 대신 Python 리스트를 사용했기 때문에 서버를 재시작하면 데이터가 초기화됩니다. 하지만 메모리 기반 데이터 관리부터 시작해 이후 파일 저장이나 데이터베이스로 확장할 수 있다는 흐름을 이해할 수 있었습니다.

## LLM 연동 기능 추가

추가 과제로 로컬 LLM 연동 기능을 구현했습니다.

Ollama에 설치된 gemma4 모델을 사용하여 특정 글의 내용을 요약하는 API를 추가했습니다.

| 기능 | Method | URL |
|---|---|---|
| 글 요약 | POST | /posts/{post_id}/summary |

이 API는 글의 title, content, username을 가져와 로컬 Ollama 서버에 전달하고, gemma4 모델이 생성한 요약 결과를 JSON으로 반환합니다.

Ollama 서버가 실행 중이어야 정상 동작합니다.

실행 예시:

ollama run gemma4

그 후 FastAPI 서버를 실행하고 /docs에서 POST /posts/{post_id}/summary API를 테스트할 수 있습니다.
