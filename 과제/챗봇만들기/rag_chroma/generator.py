import os

def build_prompt(question, hits):
    context = "\n\n".join(
        f"[문서 {i+1}] (출처: {h['source']})\n{h['text']}"
        for i, h in enumerate(hits)
    )
    return (
        "다음 문서를 바탕으로 질문에 답하세요. 문서에 없는 내용은 모른다고 하세요.\n\n"
        f"=== 참고 문서 ===\n{context}\n\n"
        f"=== 질문 ===\n{question}\n\n=== 답변 ==="
    )

def _clean(text):
    import re
    text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)   
    text = re.sub(r"\n{2,}", "\n", text).strip()
    return text

def answer_local(question, hits):
    if not hits:
        return "관련 문서에서 답을 찾지 못했어요. 다른 표현으로 물어봐 주세요."
    top = hits[0]
    
    if top["similarity"] < 0.2:
        return "관련 문서에서 답을 찾지 못했어요. 다른 표현으로 물어봐 주세요."
    body = _clean(top["text"])
    return f"{body}\n\n— 출처: {top['source']} (유사도 {top['similarity']})"

def answer_kogpt2(question, hits):
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    import kogpt2_chatbot as bot  
    prompt = build_prompt(question, hits)
    return bot.generate_reply(prompt, max_new_tokens=80, temperature=0.7)

_ft_model = None
_ft_tokenizer = None

def _load_finetuned():
    global _ft_model, _ft_tokenizer
    if _ft_model is None:
        import torch
        from transformers import AutoTokenizer, AutoModelForCausalLM
        path = os.environ.get("FINETUNED_MODEL_PATH", "kogpt2-finetuned")
        _ft_tokenizer = AutoTokenizer.from_pretrained(path)
        _ft_model = AutoModelForCausalLM.from_pretrained(path)
        _ft_model.eval()
    return _ft_model, _ft_tokenizer

def answer_finetuned(question, hits):
    import torch
    model, tokenizer = _load_finetuned()

    context = "\n".join(f"- {h['text']}" for h in hits)
    prompt = f"### 질문: {question}\n참고:\n{context}\n### 답변:"

    ids = tokenizer.encode(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        out = model.generate(
            ids, max_new_tokens=100, do_sample=True, top_p=0.92,
            temperature=0.7, repetition_penalty=1.3, no_repeat_ngram_size=3,
            pad_token_id=tokenizer.pad_token_id, eos_token_id=tokenizer.eos_token_id,
        )
    text = tokenizer.decode(out[0], skip_special_tokens=True)
    return text[len(prompt):].split("### 질문")[0].strip() or answer_local(question, hits)

def answer_claude(question, hits):
    from anthropic import Anthropic
    client = Anthropic()
    model = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-6")
    system = (
        "너는 문서 기반으로 답하는 한국어 비서다. "
        "반드시 주어진 참고 문서 내용만 사용해 답하고, 없으면 모른다고 말하라."
    )
    resp = client.messages.create(
        model=model, max_tokens=600, system=system,
        messages=[{"role": "user", "content": build_prompt(question, hits)}],
    )
    return "".join(b.text for b in resp.content if b.type == "text").strip()

def answer_gemini_web(question):
    if not os.environ.get("GEMINI_API_KEY"):
        return ("GEMINI_API_KEY 가 설정되지 않았어요. .env 에 키를 넣어주세요. "
                "(https://aistudio.google.com/app/apikey 에서 발급)", [])

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

    cfg = types.GenerateContentConfig(
        tools=[types.Tool(google_search=types.GoogleSearch())],
        system_instruction=(
            "너는 한국어로 답하는 친절한 비서다. "
            "Google 검색 결과를 근거로 정확하고 간결하게 한국어로 답하라. "
            "모르면 모른다고 말하라."
        ),
    )

    import time
    resp, last_err = None, None
    for attempt in range(4):
        try:
            resp = client.models.generate_content(model=model, contents=question, config=cfg)
            break
        except Exception as e:
            last_err = e
            msg = str(e)
            if "503" in msg or "UNAVAILABLE" in msg or "429" in msg or "overloaded" in msg.lower():
                time.sleep(1.5 * (attempt + 1))   
                continue
            return (f"Gemini 호출 중 오류가 발생했어요: {e}", [])
    if resp is None:
        return ("Gemini 서버가 잠시 혼잡해요(503). 잠시 후 다시 시도해 주세요. "
                f"(자동 재시도 4회 모두 실패: {last_err})", [])

    text = (resp.text or "").strip()
    sources = []
    try:
        gm = resp.candidates[0].grounding_metadata
        for ch in (gm.grounding_chunks or []):
            if getattr(ch, "web", None):
                sources.append({"source": ch.web.title or ch.web.uri, "url": ch.web.uri})
    except Exception:
        pass
    return text or "답변을 생성하지 못했어요.", sources

def get_backend_name():
    b = os.environ.get("LLM_BACKEND", "").lower()
    if b in ("local", "kogpt2", "finetuned", "claude"):
        return b
    return "claude" if os.environ.get("ANTHROPIC_API_KEY") else "local"

def generate(question, hits):
    backend = get_backend_name()
    try:
        if backend == "claude":
            return answer_claude(question, hits)
        if backend == "finetuned":
            return answer_finetuned(question, hits)
        if backend == "kogpt2":
            return answer_kogpt2(question, hits)
    except Exception as e:
        return f"({backend} 호출 실패 → 로컬 답변으로 대체: {e})\n\n{answer_local(question, hits)}"
    return answer_local(question, hits)
