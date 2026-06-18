import torch
import gradio as gr
from transformers import AutoTokenizer, AutoModelForCausalLM

MODEL = "jjminu/koalpaca-chatbot"
BASE = "EleutherAI/polyglot-ko-1.3b"

try:
    tokenizer = AutoTokenizer.from_pretrained(MODEL)
except Exception:
    tokenizer = AutoTokenizer.from_pretrained(BASE)
if tokenizer.pad_token_id is None:
    tokenizer.pad_token = tokenizer.eos_token
model = AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.float32)
model.eval()


@torch.no_grad()
def chat(message, history):
    prompt = f"### 질문: {message}\n\n### 답변:"
    ids = tokenizer.encode(prompt, return_tensors="pt")
    out = model.generate(
        ids,
        max_new_tokens=150,
        do_sample=True,
        top_p=0.92,
        temperature=0.7,
        repetition_penalty=1.1,
        pad_token_id=tokenizer.pad_token_id,
        eos_token_id=tokenizer.eos_token_id,
    )
    text = tokenizer.decode(out[0][ids.shape[1]:], skip_special_tokens=True)
    return text.split("###")[0].strip()


demo = gr.ChatInterface(
    fn=chat,
    title="otto의 챗봇",
    description="직접 파인튜닝한 한국어 모델(polyglot-ko-1.3b)로 답합니다.",
    examples=["파이썬이 뭐야?", "건강하게 사는 방법 알려줘", "좋은 개발자가 되려면?"],
)

if __name__ == "__main__":
    demo.launch()
