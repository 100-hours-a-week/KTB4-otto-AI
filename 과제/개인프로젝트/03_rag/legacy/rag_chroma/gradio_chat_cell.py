# ── Colab 셀: 대화 기억 + 간결한 답변 (학습/병합 셀 다음에 실행) ──
!pip -q install gradio
import gradio as gr, torch

SYSTEM = "너는 한국어로 간결하고 정확하게 답하는 친절한 비서다. 한두 문단으로 핵심만 답하고, 같은 말을 반복하지 마라."

def build_prompt(message, history):
    # history: [[user, bot], ...] — 이전 대화를 프롬프트에 넣어 기억하게 함
    s = SYSTEM + "\n\n"
    for turn in history[-5:]:          # 최근 5턴만 (너무 길어지지 않게)
        u = turn[0] if isinstance(turn, (list, tuple)) else turn.get("content", "")
        b = turn[1] if isinstance(turn, (list, tuple)) else ""
        if u:
            s += f"### 질문: {u}\n\n### 답변: {b}\n\n"
    s += f"### 질문: {message}\n\n### 답변:"
    return s

@torch.no_grad()
def chat(message, history):
    prompt = build_prompt(message, history or [])
    ids = tok.encode(prompt, return_tensors="pt").to(merged.device)
    out = merged.generate(
        ids, max_new_tokens=180, do_sample=True, top_p=0.9, temperature=0.6,
        repetition_penalty=1.2, no_repeat_ngram_size=3,
        pad_token_id=tok.pad_token_id, eos_token_id=tok.eos_token_id,
    )
    text = tok.decode(out[0][ids.shape[1]:], skip_special_tokens=True)
    return text.split("###")[0].strip()

gr.ChatInterface(chat, title="otto의 챗봇 (5.8B)",
                 description="대화를 기억합니다.").launch(share=True)
