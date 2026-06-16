"""
한국어 챗봇 - KoGPT2 버전 (진짜 AI 모델 활용)
=================================================
SKT 가 공개한 사전학습 한국어 GPT 모델(skt/kogpt2-base-v2)을 불러와
'다음 토큰을 반복 생성'하여 문장을 만든다.

- 과제 5-1: predict_next_token()  → 다음 토큰(단어 조각) 1개 예측
- 과제 5-2: generate_reply()      → 다음 토큰 생성을 반복하여 완전한 문장 생성

작은 LSTM(chatbot_model.py) 과 달리, 대용량 코퍼스로 사전학습된 모델이라
코퍼스에 없는 문장도 자연스러운 한국어로 생성한다.
"""

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

MODEL_NAME = "skt/kogpt2-base-v2"

# 모듈 전역에 1회만 로딩 (서버가 요청마다 다시 읽지 않도록)
_tokenizer = None
_model = None
_device = "cuda" if torch.cuda.is_available() else "cpu"


def load():
    """모델/토크나이저를 1회 로딩한다 (최초 호출 시 다운로드)."""
    global _tokenizer, _model
    if _model is None:
        print(f"KoGPT2 로딩 중... ({MODEL_NAME}, device={_device})")
        _tokenizer = AutoTokenizer.from_pretrained(
            MODEL_NAME,
            bos_token="</s>", eos_token="</s>", unk_token="<unk>",
            pad_token="<pad>", mask_token="<mask>",
        )
        _model = AutoModelForCausalLM.from_pretrained(MODEL_NAME).to(_device)
        _model.eval()
        print("KoGPT2 로딩 완료.")
    return _tokenizer, _model


# ---------------------------------------------------------------------------
# 과제 5-1: 다음 토큰 1개 예측
# ---------------------------------------------------------------------------
@torch.no_grad()
def predict_next_token(text, temperature=0.8):
    """입력 문장 다음에 올 토큰(단어 조각) 하나를 예측해 반환한다."""
    tokenizer, model = load()
    input_ids = tokenizer.encode(text, return_tensors="pt").to(_device)
    logits = model(input_ids).logits[0, -1, :] / max(temperature, 1e-3)
    probs = torch.softmax(logits, dim=-1)
    next_id = torch.multinomial(probs, num_samples=1).item()
    return tokenizer.decode([next_id])


# ---------------------------------------------------------------------------
# 과제 5-2: 다음 토큰 생성을 반복하여 완전한 문장 생성
# ---------------------------------------------------------------------------
# 모델이 '답변'을 생성하도록 유도하는 대화 템플릿.
# 순수 언어모델이라 질문-답변 형식을 보여주면 훨씬 챗봇처럼 답한다.
_PROMPT_TEMPLATE = (
    "다음은 사용자와 친절한 한국어 상담원의 대화입니다.\n"
    "사용자: {q}\n"
    "상담원:"
)


@torch.no_grad()
def generate_reply(prompt, max_new_tokens=60, temperature=0.8,
                   top_k=50, top_p=0.92, repetition_penalty=1.3):
    """
    prompt 를 시작으로 다음 토큰을 반복 생성하여 한국어 답변을 만든다.
    내부적으로 model.generate 가 '다음 토큰 예측'을 max_new_tokens 번 반복한다.
    """
    tokenizer, model = load()
    framed = _PROMPT_TEMPLATE.format(q=prompt.strip())
    input_ids = tokenizer.encode(framed, return_tensors="pt").to(_device)

    output = model.generate(
        input_ids,
        max_new_tokens=max_new_tokens,
        do_sample=True,
        temperature=temperature,
        top_k=top_k,
        top_p=top_p,
        repetition_penalty=repetition_penalty,
        no_repeat_ngram_size=3,
        pad_token_id=tokenizer.pad_token_id,
        eos_token_id=tokenizer.eos_token_id,
    )

    text = tokenizer.decode(output[0], skip_special_tokens=True)
    # 프롬프트(템플릿) 이후 '상담원:' 다음에 생성된 답변만 추출
    reply = text[len(framed):].strip()
    # 다음 '사용자:' 턴이 시작되면 그 앞까지만 사용
    for stop in ("사용자:", "상담원:", "\n"):
        idx = reply.find(stop)
        if idx != -1:
            reply = reply[:idx].strip()
    # 첫 문장만 깔끔하게 잘라서 반환 (마침표/물음표/느낌표 기준)
    reply = _trim_to_sentence(reply)
    return reply if reply else "죄송해요, 잘 이해하지 못했어요. 다시 말씀해 주시겠어요?"


def _trim_to_sentence(text):
    """첫 종결 부호까지만 남겨 답변을 깔끔하게 만든다."""
    text = text.replace("\n", " ").strip()
    for i, ch in enumerate(text):
        if ch in ".?!":
            return text[: i + 1]
    return text


if __name__ == "__main__":
    # 간단한 CLI 테스트
    for q in ["안녕하세요", "오늘 날씨가 좋아서", "인공지능이란", "주말에 뭐 하면 좋을까요?"]:
        print(f"입력: {q}")
        print(f"답변: {generate_reply(q)}\n")
