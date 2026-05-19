# FastAPI로 백엔드 구현해보기

## 프로젝트 소개

FastAPI로 간단한 커뮤니티 백엔드를 만들어보는 과제입니다.

데이터베이스는 아직 몰라서 Python 리스트로 대신했습니다. 서버 끄면 데이터 다 날아갑니다.  
로그인 기능도 없고, username을 그냥 Body에 직접 적는 방식으로 했습니다.  
부족한 부분이 많지만 일단 동작은 합니다.

## 구현한 기능

- 글 작성 / 조회 / 수정 / 삭제
- 댓글 작성 / 조회 / 수정 / 삭제
- Ollama(gemma4) 연동해서 글 요약하는 기능 (추가 과제)

## 프로젝트 구조

```
main.py           # FastAPI 앱이랑 라우터 등록
routers/          # 엔드포인트 정의
controllers/      # 실제 처리 로직
models/           # 메모리(리스트)에 데이터 저장하는 부분
```

## 실행 방법

```bash
# 패키지 설치
pip install -r requirements.txt

# 서버 실행
uvicorn main:app --reload
```

실행 후 http://127.0.0.1:8000/docs 에서 API 테스트할 수 있습니다.

LLM 기능 쓰려면 Ollama도 따로 실행해야 합니다.

```bash
ollama run gemma4
```

## API 목록

### 글

| 기능 | Method | URL |
|---|---|---|
| 글 작성 | POST | /posts |
| 글 목록 조회 | GET | /posts |
| 글 상세 조회 | GET | /posts/{post_id} |
| 글 전체 수정 | PUT | /posts/{post_id} |
| 글 일부 수정 | PATCH | /posts/{post_id} |
| 글 삭제 | DELETE | /posts/{post_id} |

### 댓글

| 기능 | Method | URL |
|---|---|---|
| 댓글 작성 | POST | /posts/{post_id}/comments |
| 댓글 목록 조회 | GET | /posts/{post_id}/comments |
| 댓글 수정 | PATCH | /comments/{comment_id} |
| 댓글 삭제 | DELETE | /comments/{comment_id} |

### LLM 요약

| 기능 | Method | URL |
|---|---|---|
| 글 요약 | GET | /posts/{post_id}/summary |
| 댓글 요약 | GET | /comments/{comment_id}/summary |
| 글의 댓글 요약 | GET | /posts/{post_id}/comments/{comment_id}/summary |

## 요청 예시

글 작성할 때 Body

```json
{
  "title": "제목입니다",
  "content": "내용입니다",
  "username": "minwoo"
}
```

댓글 작성할 때 Body

```json
{
  "content": "댓글입니다",
  "username": "minwoo"
}
```

## 사용한 상태 코드

| 코드 | 상황 |
|---|---|
| 200 | 조회, 수정 성공 |
| 201 | 작성 성공 |
| 204 | 삭제 성공 |
| 400 | 수정할 값이 없을 때 |
| 404 | 글/댓글 없을 때 |
| 503 | Ollama 서버 안 켜져 있을 때 |

## 느낀 점

솔직히 처음엔 GET이랑 POST 차이도 대충만 알고 있었는데, 직접 짜보니까 왜 구분하는지 감이 왔습니다.

URL에 `/getPost` 이런 식으로 동사 쓰면 안 된다는 것도 이번에 알았습니다. 자원은 URL로, 행위는 Method로 표현하는 게 REST라는 걸 이제야 좀 이해한 것 같습니다.

Ollama 연동은 생각보다 간단했는데 처음에 stream 옵션 빠뜨려서 응답이 이상하게 와서 한참 헤맸습니다.

데이터베이스 없이 리스트로만 하다 보니 서버 재시작하면 데이터가 날아가는 게 좀 불편했습니다. 다음엔 DB도 써보고 싶습니다.
