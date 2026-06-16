import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

MODEL_NAME = "skt/kogpt2-base-v2"

_tokenizer = None
_model = None
_device = "cuda" if torch.cuda.is_available() else "cpu"

def load():
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

@torch.no_grad()
def predict_next_token(text, temperature=0.8):
    tokenizer, model = load()
    input_ids = tokenizer.encode(text, return_tensors="pt").to(_device)
    logits = model(input_ids).logits[0, -1, :] / max(temperature, 1e-3)
    probs = torch.softmax(logits, dim=-1)
    next_id = torch.multinomial(probs, num_samples=1).item()
    return tokenizer.decode([next_id])

_PROMPT_TEMPLATE = (
    "다음은 사용자와 친절한 한국어 상담원의 대화입니다.\n"
    "사용자: {q}\n"
    "상담원:"
)

@torch.no_grad()
def generate_reply(prompt, max_new_tokens=60, temperature=0.8,
                   top_k=50, top_p=0.92, repetition_penalty=1.3):
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
    
    reply = text[len(framed):].strip()
    
    for stop in ("사용자:", "상담원:", "\n"):
        idx = reply.find(stop)
        if idx != -1:
            reply = reply[:idx].strip()
    
    reply = _trim_to_sentence(reply)
    return reply if reply else "죄송해요, 잘 이해하지 못했어요. 다시 말씀해 주시겠어요?"

def _trim_to_sentence(text):
    text = text.replace("\n", " ").strip()
    for i, ch in enumerate(text):
        if ch in ".?!":
            return text[: i + 1]
    return text

if __name__ == "__main__":
    
    for q in ["안녕하세요", "오늘 날씨가 좋아서", "인공지능이란", "주말에 뭐 하면 좋을까요?"]:
        print(f"입력: {q}")
        print(f"답변: {generate_reply(q)}\n")
