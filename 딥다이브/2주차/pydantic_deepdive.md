# FastAPI에서 Pydantic 모델을 활용한 입력 데이터 검증

## 1. 주제

**FastAPI에서 Pydantic 모델을 활용해 입력 데이터를 검증하는 방식과, 이를 통해 AI 모델 서빙 시 발생할 수 있는 잘못된 요청을 어떻게 방지할 수 있는지 설명하시오.**

---

## 2. 내가 이해한 핵심

FastAPI에서 Pydantic 모델은 **클라이언트가 보낸 요청 데이터가 서버에서 처리해도 되는 형태인지 미리 검사하는 역할**을 한다.

API 서버는 사용자가 보내는 데이터를 그대로 믿으면 안 된다.  
사용자가 필요한 값을 빼먹을 수도 있고, 숫자가 들어와야 할 곳에 문자열을 보낼 수도 있다. 특히 AI 모델 서빙 API에서는 잘못된 입력이 모델까지 전달되면 서버 에러, 의미 없는 결과, 불필요한 비용 증가로 이어질 수 있다.

그래서 FastAPI에서는 Pydantic 모델을 사용해서 요청 데이터의 구조를 먼저 정해둔다.

예를 들어 AI 요약 API라면 서버는 최소한 이런 값을 기대할 수 있다.

\`\`\`json
{
  "text": "오늘 배운 내용을 요약해줘.",
  "max_length": 100
}
\`\`\`

여기서 `text`는 요약할 원문이고, `max_length`는 요약 결과의 최대 길이다.

---

## 3. 입력 검증이 없는 경우의 문제

먼저 Pydantic 없이 `dict`로 요청을 받는 코드를 생각해보자.

\`\`\`python
from fastapi import FastAPI

app = FastAPI()

@app.post("/summary")
async def summarize(request: dict):
    text = request["text"]
    max_length = request["max_length"]

    summary = text[:max_length]

    return {"summary": summary}
\`\`\`

이 코드는 간단해 보이지만 문제가 있다.

예를 들어 사용자가 이렇게 요청하면 어떻게 될까?

\`\`\`json
{
  "max_length": 100
}
\`\`\`

`text`가 없기 때문에 아래 코드에서 문제가 생길 수 있다.

\`\`\`python
text = request["text"]
\`\`\`

또 사용자가 이렇게 보낼 수도 있다.

\`\`\`json
{
  "text": "오늘 수업 내용을 요약해줘.",
  "max_length": "길게"
}
\`\`\`

`max_length`는 숫자여야 하는데 문자열이 들어왔다.  
이 상태에서 `text[:max_length]`를 실행하면 정상적으로 동작하기 어렵다.

즉, 입력 검증이 없으면 잘못된 요청이 서버 내부 로직까지 그대로 들어오게 된다.

---

## 4. Pydantic 모델로 입력 구조 정하기

Pydantic을 사용하면 요청 데이터가 어떤 구조를 가져야 하는지 코드로 정할 수 있다.

\`\`\`python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class SummaryRequest(BaseModel):
    text: str
    max_length: int

@app.post("/summary")
async def summarize(request: SummaryRequest):
    summary = request.text[:request.max_length]

    return {"summary": summary}
\`\`\`

여기서 중요한 부분은 이 코드이다.

\`\`\`python
class SummaryRequest(BaseModel):
    text: str
    max_length: int
\`\`\`

이 코드는 다음과 같은 의미를 가진다.

| 필드 | 타입 | 의미 |
|---|---|---|
| `text` | `str` | 요약할 원문 |
| `max_length` | `int` | 요약 결과의 최대 길이 |

이제 FastAPI는 `/summary` 요청이 들어왔을 때, `text`가 문자열인지, `max_length`가 정수인지 먼저 확인한다.

검증에 성공하면 함수 내부 코드가 실행된다.  
검증에 실패하면 함수 내부로 들어가기 전에 오류 응답을 반환한다.

---

## 5. 검증 실패 시 실제 응답 예시

예를 들어 사용자가 `text`를 빼고 요청했다고 하자.

\`\`\`json
{
  "max_length": 100
}
\`\`\`

그러면 FastAPI는 보통 `422 Unprocessable Entity` 상태 코드와 함께 다음과 비슷한 응답을 반환한다.

\`\`\`json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "text"],
      "msg": "Field required",
      "input": {
        "max_length": 100
      }
    }
  ]
}
\`\`\`

여기서 중요한 부분은 `"loc": ["body", "text"]`이다.  
이 말은 request body 안에서 `text` 필드가 문제라는 뜻이다.

즉, FastAPI와 Pydantic은 단순히 “요청이 틀렸다”고만 말하는 것이 아니라, **어떤 위치의 어떤 값이 잘못됐는지 알려준다.**

이 점이 실무에서 중요하다고 생각했다.  
프론트엔드 개발자나 API 사용자 입장에서는 어떤 값을 고쳐야 하는지 알 수 있고, 백엔드 입장에서는 잘못된 요청이 AI 모델까지 들어가지 않았다는 것을 확인할 수 있기 때문이다.

---

## 6. AI 모델 서빙에서는 더 구체적인 검증이 필요하다

기본적으로 `text: str`, `max_length: int`만 적어도 타입 검증은 가능하다.

하지만 AI 모델 서빙에서는 이것만으로는 부족하다.

예를 들어 아래 요청은 `text`가 문자열이기 때문에 타입만 보면 맞다.

\`\`\`json
{
  "text": "      ",
  "max_length": 100
}
\`\`\`

하지만 실제로는 공백만 있는 문자열이다.  
AI 모델 입장에서는 요약할 내용이 없는 입력이다.

또 아래 요청도 문제가 있다.

\`\`\`json
{
  "text": "오늘 수업 내용을 요약해줘.",
  "max_length": 10000
}
\`\`\`

`max_length`는 정수이므로 타입은 맞다.  
하지만 요약 길이로 10000은 너무 크다. 이런 요청을 그대로 허용하면 응답 시간이 길어지거나 비용이 증가할 수 있다.

그래서 실제 AI API에서는 타입뿐 아니라 길이, 범위, 공백 여부 같은 조건도 함께 검사해야 한다.

---

## 7. 조금 더 실무적인 Pydantic 모델 예시

아래 코드는 AI 요약 API에서 사용할 수 있는 입력 검증 예시이다.

\`\`\`python
from typing import Literal, Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field, field_validator

app = FastAPI()


class SummaryRequest(BaseModel):
    text: str = Field(min_length=1, max_length=3000)
    max_length: int = Field(ge=20, le=300)
    language: Optional[Literal["ko", "en"]] = None

    @field_validator("text")
    @classmethod
    def text_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("text는 공백만 입력할 수 없습니다.")
        return value.strip()


@app.post("/summary")
async def summarize(request: SummaryRequest):
    language = request.language

    if language is None:
        language = "auto"

    result = fake_summary_model(
        text=request.text,
        max_length=request.max_length,
        language=language
    )

    return {
        "language": language,
        "result": result
    }


def fake_summary_model(text: str, max_length: int, language: str) -> str:
    return f"[{language}] " + text[:max_length] + "..."
\`\`\`

---

## 8. 코드 해석

### 8-1. `Field`로 길이와 범위 제한하기

\`\`\`python
text: str = Field(min_length=1, max_length=3000)
\`\`\`

이 코드는 `text`가 최소 1글자 이상, 최대 3000글자 이하이어야 한다는 뜻이다.

\`\`\`python
max_length: int = Field(ge=20, le=300)
\`\`\`

이 코드는 `max_length`가 20 이상 300 이하이어야 한다는 뜻이다.

- `ge=20`: 20 이상
- `le=300`: 300 이하

이렇게 하면 빈 문자열이나 너무 긴 텍스트, 너무 큰 숫자를 미리 막을 수 있다.

---

### 8-2. `Field`와 `field_validator`의 차이

처음에는 아래 두 코드가 비슷해 보였다.

\`\`\`python
text: str = Field(min_length=1, max_length=3000)

@field_validator("text")
@classmethod
def text_must_not_be_blank(cls, value: str) -> str:
    if not value.strip():
        raise ValueError("text는 공백만 입력할 수 없습니다.")
    return value.strip()
\`\`\`

하지만 역할이 다르다.

| 검증 방식 | 막는 입력 | 역할 |
|---|---|---|
| `Field(min_length=1)` | `""` | 빈 문자열 차단 |
| `Field(max_length=3000)` | 너무 긴 문자열 | 과도한 입력 차단 |
| `field_validator` | `"     "` | 공백만 있는 문자열 차단 |

`Field(min_length=1)`은 문자열 길이가 1 이상인지 확인한다.  
그래서 `""` 같은 빈 문자열은 막을 수 있다.

하지만 `"     "`처럼 공백만 있는 문자열은 길이가 1 이상이기 때문에 통과할 수 있다.  
그래서 `field_validator`에서 `strip()`을 사용해 공백을 제거한 뒤 실제 내용이 있는지 다시 확인한다.

이 부분에서 **타입 검증과 의미 검증은 다르다**는 것을 알 수 있었다.

---

### 8-3. Optional 필드 처리

\`\`\`python
language: Optional[Literal["ko", "en"]] = None
\`\`\`

이 코드는 `language`가 선택값이라는 뜻이다.

즉, 사용자는 언어를 직접 보낼 수도 있다.

\`\`\`json
{
  "text": "오늘 수업 내용을 요약해줘.",
  "max_length": 100,
  "language": "ko"
}
\`\`\`

또는 생략할 수도 있다.

\`\`\`json
{
  "text": "오늘 수업 내용을 요약해줘.",
  "max_length": 100
}
\`\`\`

`language`가 없으면 값은 `None`이 된다.  
그러면 서버에서 자동 감지하거나 기본값을 사용할 수 있다.

\`\`\`python
if language is None:
    language = "auto"
\`\`\`

이처럼 Pydantic 모델에서는 필수값과 선택값을 나눌 수 있다.

---

## 9. 잘못된 요청이 차단되는 예시

| 잘못된 요청 | 차단 이유 |
|---|---|
| `text` 없음 | 필수 입력값 누락 |
| `text: ""` | 빈 문자열 |
| `text: "   "` | 공백만 있는 문자열 |
| `text`가 너무 김 | 최대 길이 초과 |
| `max_length: "길게"` | 정수가 아님 |
| `max_length: 10000` | 허용 범위 초과 |
| `language: "fr"` | 허용된 값이 아님 |

이런 요청들은 AI 모델 함수까지 전달되기 전에 차단된다.

처리 흐름은 다음과 같다.

\`\`\`text
잘못된 요청
    ↓
Pydantic 검증 실패
    ↓
FastAPI가 422 오류 응답 반환
    ↓
AI 모델 호출 안 함
\`\`\`

정상 요청은 다음과 같이 처리된다.

\`\`\`text
정상 요청
    ↓
Pydantic 검증 통과
    ↓
엔드포인트 함수 실행
    ↓
AI 모델 호출
    ↓
결과 반환
\`\`\`

---

## 10. 간단한 테스트 코드

입력 검증이 실제로 동작하는지는 테스트 코드로 확인할 수 있다.

\`\`\`python
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_summary_success():
    response = client.post(
        "/summary",
        json={
            "text": "FastAPI와 Pydantic은 입력 검증에 사용된다.",
            "max_length": 100,
            "language": "ko"
        }
    )

    assert response.status_code == 200
    assert "result" in response.json()


def test_summary_rejects_missing_text():
    response = client.post(
        "/summary",
        json={
            "max_length": 100
        }
    )

    assert response.status_code == 422


def test_summary_rejects_wrong_max_length_type():
    response = client.post(
        "/summary",
        json={
            "text": "오늘 수업 내용을 요약해줘.",
            "max_length": "길게"
        }
    )

    assert response.status_code == 422


def test_summary_rejects_blank_text():
    response = client.post(
        "/summary",
        json={
            "text": "     ",
            "max_length": 100
        }
    )

    assert response.status_code == 422
\`\`\`

이 테스트의 핵심은 간단하다.

\`\`\`text
정상 요청 → 200
잘못된 요청 → 422
\`\`\`

즉, Pydantic 모델이 실제로 잘못된 요청을 막고 있는지 코드로 확인할 수 있다.

---

## 11. AI 모델 서빙에서 중요한 이유

AI 모델 서빙에서는 입력 검증이 더 중요하다고 생각한다.

일반적인 함수는 잘못된 입력이 들어와도 서버 내부에서 바로 수정하거나 예외 처리할 수 있을지도 모른다. 하지만 AI 모델은 입력이 잘못되면 다음과 같은 문제가 생길 수 있다.

| 잘못된 입력 | 발생 가능한 문제 |
|---|---|
| 빈 텍스트 | 의미 없는 결과 생성 |
| 너무 긴 텍스트 | 처리 시간 증가 |
| 너무 큰 max_length | 응답 지연 |
| 잘못된 타입 | 서버 에러 |
| 지원하지 않는 언어 | 모델 프롬프트 또는 후처리 오류 |

특히 외부 LLM API나 GPU 모델을 사용하는 경우, 잘못된 요청을 모델까지 보내는 것 자체가 비용과 자원 낭비가 될 수 있다.

따라서 AI 모델을 호출하기 전에 FastAPI와 Pydantic으로 입력값을 검사하는 것이 중요하다.

---

## 12. 최종 결론

FastAPI에서 Pydantic 모델은 클라이언트가 보낸 JSON 요청을 검증하는 입력 데이터 설계도이다.

`BaseModel`로 요청 구조를 만들고, `Field`를 사용해 문자열 길이나 숫자 범위를 제한할 수 있다. 또한 `field_validator`를 사용하면 공백만 있는 문자열처럼 타입은 맞지만 의미상 잘못된 입력도 막을 수 있다. `Optional`을 사용하면 언어 설정처럼 없어도 되는 선택값도 표현할 수 있다.

검증에 실패하면 FastAPI는 보통 `422 Unprocessable Entity` 응답을 반환하고, 어떤 필드에서 문제가 생겼는지 JSON 형태로 알려준다.

AI 모델 서빙에서는 잘못된 입력이 모델 추론 실패, 서버 에러, 비용 증가, 응답 지연으로 이어질 수 있다. 따라서 Pydantic 입력 검증은 AI 모델 앞에서 잘못된 요청을 걸러주는 1차 방어선이라고 볼 수 있다.

결국 개발자는 Pydantic 모델을 통해 API가 어떤 데이터를 받을 수 있는지 코드로 표현하고, 테스트를 통해 실제로 잘못된 요청이 차단되는지 확인할 수 있어야 한다.

---

## 13. 참고 자료

- FastAPI 공식 문서 - Request Body  
  https://fastapi.tiangolo.com/tutorial/body/

- FastAPI 공식 문서 - Handling Errors  
  https://fastapi.tiangolo.com/tutorial/handling-errors/

- FastAPI 공식 문서 - Testing  
  https://fastapi.tiangolo.com/tutorial/testing/

- Pydantic 공식 문서 - Fields  
  https://docs.pydantic.dev/latest/concepts/fields/

- Pydantic 공식 문서 - Validators  
  https://docs.pydantic.dev/latest/concepts/validators/
