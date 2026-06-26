"""RAG 재파인튜닝 v2 — 교사모델(Gemini) distillation + 평가 기반 학습.

v1 대비: 데이터를 Gemini 로 수백개 자동 생성(다양한 표현/구어체/거부) + train/eval 분리 +
베스트 체크포인트 저장으로 과적합 방지.
"""
import json
import os

ROOT = "/Users/minwoo/7주차/langchain_rag"
OUT = os.path.join(ROOT, "colab", "otto_rag_finetune_v2_colab.ipynb")
REFUSE = "제공된 문서에서 답을 찾을 수 없습니다."

# 문맥 스니펫 (docs 실제 단락)
C = {
    "adapterz": "[출처: startupcode_faq.md] 어댑터즈는 현업 개발자가 직접 집필한 실무 중심 개발 교재를 구독형으로 제공하는 서비스입니다. 월 구독료는 1만 9천 원이며, 모든 교재를 무제한으로 볼 수 있습니다. 교재는 매주 새로 업데이트되고, 코드 예제는 깃허브 저장소로 함께 제공됩니다.",
    "company": "[출처: startupcode_faq.md] 스타트업코드는 개발자를 위한 교육과 교재를 제공하는 회사입니다. 주력 서비스로는 개발 교재 플랫폼 어댑터즈와 온라인 코딩 부트캠프가 있습니다. 2021년에 설립되었으며, 현재 누적 수강생은 1만 2천 명을 넘었습니다.",
    "bootcamp": "[출처: startupcode_faq.md] 온라인 코딩 부트캠프는 16주 과정으로 운영됩니다. 백엔드 트랙과 AI 트랙 두 가지가 있으며, 백엔드 트랙은 파이썬과 FastAPI를, AI 트랙은 딥러닝과 LLM 애플리케이션 개발을 다룹니다. 수료하려면 최종 프로젝트를 제출하고 코드 리뷰를 통과해야 합니다.",
    "refund": "[출처: startupcode_faq.md] 부트캠프 수강료는 350만 원이며, 분할 납부가 가능합니다. 환불은 수강 시작 후 14일 이내에 신청하면 전액 환불됩니다. 14일이 지난 뒤에는 진행한 주차를 제외한 잔여 금액의 일부만 환불됩니다.",
    "cert": "[출처: startupcode_faq.md] 모든 과정을 수료하면 수료증이 발급됩니다. 또한 취업 지원 프로그램을 통해 이력서 첨삭과 모의 면접을 제공하며, 협력 기업에 추천서를 보내드립니다.",
    "contact": "[출처: startupcode_faq.md] 서비스 관련 문의는 평일 오전 10시부터 오후 6시까지 이메일(support@startupcode.kr) 또는 카카오톡 채널로 받습니다. 주말과 공휴일에는 답변이 다음 영업일로 넘어갑니다.",
    "aigoal": "[출처: ai_bootcamp_notes.md] AI 트랙은 딥러닝의 기초부터 LLM 애플리케이션 개발까지 다룹니다. 수료 후에는 이미지 분류 모델과 RAG 기반 챗봇을 직접 만들 수 있는 수준을 목표로 합니다.",
    "weeks": "[출처: ai_bootcamp_notes.md] 1주차에는 파이썬 복습과 넘파이를 다룹니다. 2주차부터 4주차까지는 신경망과 CNN을 배우고, ResNet과 VGG16 같은 사전학습 모델로 전이학습을 실습합니다. 5주차에는 자연어 처리와 챗봇을 만들고, RAG 아키텍처를 적용합니다.",
    "ragprac": "[출처: ai_bootcamp_notes.md] RAG 실습에서는 문서를 청킹하고 sentence-transformers로 임베딩한 뒤 ChromaDB에 저장합니다. 사용자 질문이 들어오면 코사인 유사도로 관련 문서를 검색해 프롬프트에 넣고 LLM이 답변을 생성합니다.",
    "eval": "[출처: ai_bootcamp_notes.md] 최종 프로젝트는 동작 여부, 코드 구조, 그리고 발표로 평가됩니다. 단순히 개념을 아는 것보다 실제로 동작하는 애플리케이션을 만드는 것이 더 높게 평가됩니다.",
}

# 손으로 만든 시드(핵심 사실 보장용) — 교사 생성이 일부 실패해도 베이스 확보
seed = [
    ("adapterz", "어댑터즈 월 구독료는 얼마인가요?", "월 구독료는 1만 9천 원입니다."),
    ("adapterz", "어댑터즈 구독료 얼마야?", "월 1만 9천 원입니다."),
    ("company", "스타트업코드는 언제 설립됐어?", "2021년에 설립되었습니다."),
    ("company", "누적 수강생은 몇 명이야?", "1만 2천 명을 넘었습니다."),
    ("bootcamp", "부트캠프는 몇 주 과정이야?", "16주 과정입니다."),
    ("bootcamp", "AI 트랙은 뭘 다뤄?", "딥러닝과 LLM 애플리케이션 개발을 다룹니다."),
    ("refund", "부트캠프 수강료는 얼마야?", "350만 원이며 분할 납부가 가능합니다."),
    ("refund", "환불은 언제까지 신청하면 전액 환불돼?", "수강 시작 후 14일 이내에 신청하면 전액 환불됩니다."),
    ("refund", "환불하고 싶어", "수강 시작 후 14일 이내에 신청하면 전액 환불됩니다."),
    ("contact", "문의는 어디로 해?", "이메일(support@startupcode.kr) 또는 카카오톡 채널로 문의할 수 있습니다."),
    ("weeks", "5주차엔 뭘 해?", "자연어 처리와 챗봇을 만들고 RAG 아키텍처를 적용합니다."),
    ("eval", "최종 프로젝트는 뭘로 평가해?", "동작 여부, 코드 구조, 발표로 평가됩니다."),
]
seed_rows = [{"context": C[k], "question": q, "answer": a} for k, q, a in seed]


def md(*lines):
    return {"cell_type": "markdown", "metadata": {}, "source": list(lines)}


def code(src):
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
            "source": src if isinstance(src, str) else "\n".join(src)}


PROMPT_HEAD = (
    "### 질문: 아래 [문서] 내용만 근거로 질문에 한국어 한 문장으로만 답해줘. "
    "문서에 답이 없으면 다른 말 없이 정확히 '제공된 문서에서 답을 찾을 수 없습니다'라고만 답해. 추측·부연 금지.\\n\\n"
    "[문서]\\n{context}\\n\\n[질문] {question}\\n\\n### 답변:"
)

cells = []

cells.append(md(
    "# 내 모델 RAG 재파인튜닝 v2 — 교사모델 distillation + 평가 기반 학습\n",
    "\n",
    "1. **Gemini(교사)** 로 내 docs 기반 고품질 QA·구어체·거부 예시를 **대량 생성** (distillation)\n",
    "2. **train/eval 분리 + 베스트 체크포인트** 저장 → 오래 학습해도 과적합 방지\n",
    "3. 내 5.8B 모델에 LoRA 학습 → 테스트 → HF Hub 업로드\n",
    "\n",
    "> 런타임 = **GPU (A100/L4 권장)**. 준비물: HF Write 토큰, Google API 키.",
))

cells.append(md("## 1. 설치"))
cells.append(code(
    "!pip -q uninstall -y torchao\n"
    "!pip -q install -U transformers peft accelerate bitsandbytes datasets google-generativeai"
))

cells.append(md("## 2. GPU 확인"))
cells.append(code(
    "import torch\n"
    "print('CUDA', torch.cuda.is_available(), '|', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')"
))

cells.append(md("## 3. 키 입력 (HF Write + Google)"))
cells.append(code(
    "import os, getpass\n"
    "from huggingface_hub import login\n"
    "login(getpass.getpass('HF Write Token (hf_...): '))\n"
    "os.environ['GOOGLE_API_KEY'] = getpass.getpass('Google API Key (교사모델용): ')"
))

cells.append(md("## 4. 문맥 + 시드 데이터"))
cells.append(code(
    "REFUSE = '제공된 문서에서 답을 찾을 수 없습니다.'\n"
    "C = " + json.dumps(C, ensure_ascii=False, indent=1) + "\n"
    "seed_rows = " + json.dumps(seed_rows, ensure_ascii=False, indent=1) + "\n"
    "print('문맥', len(C), '| 시드', len(seed_rows))"
))

cells.append(md(
    "## 5. 교사모델(Gemini)로 학습 데이터 대량 생성\n",
    "각 문서마다 다양한 질문/답변 + 거부 예시를 생성한다. (무료 티어 속도제한 대비 sleep 포함)",
))
cells.append(code(
    "import google.generativeai as genai\n"
    "import os, json, time\n"
    "\n"
    "genai.configure(api_key=os.environ['GOOGLE_API_KEY'])\n"
    "teacher = genai.GenerativeModel('gemini-2.5-flash-lite',\n"
    "    generation_config={'response_mime_type': 'application/json', 'temperature': 0.9})\n"
    "\n"
    "def gen_qa(context, n=12):\n"
    "    prompt = (f'다음 [문서]만 근거로, 사용자가 실제로 물어볼 법한 한국어 질문 {n}개와 정확한 답변을 만들어줘.\\n'\n"
    "        '규칙: 답변은 [문서]에 명시된 사실만. 질문 표현을 최대한 다양하게(존댓말/반말/짧게/길게/구어체/'\n"
    "        '명령형/불완전한 문장/오타 포함). 답변은 한 문장.\\n'\n"
    "        '반드시 JSON 배열로만 출력: [{\"question\":\"...\",\"answer\":\"...\"}]\\n\\n[문서]\\n' + context)\n"
    "    try:\n"
    "        return json.loads(teacher.generate_content(prompt).text)\n"
    "    except Exception as e:\n"
    "        print('  qa 실패:', str(e)[:50]); return []\n"
    "\n"
    "def gen_refusal(context, n=6):\n"
    "    prompt = (f'다음 [문서]로는 답할 수 없지만 같은 분야(교육/부트캠프/서비스)에서 나올 법한 한국어 질문 {n}개를 만들어줘.\\n'\n"
    "        '반드시 JSON 배열로만 출력: [{\"question\":\"...\"}]\\n\\n[문서]\\n' + context)\n"
    "    try:\n"
    "        qs = json.loads(teacher.generate_content(prompt).text)\n"
    "        return [{'context': context, 'question': q['question'], 'answer': REFUSE} for q in qs if 'question' in q]\n"
    "    except Exception as e:\n"
    "        print('  refusal 실패:', str(e)[:50]); return []\n"
    "\n"
    "all_rows = list(seed_rows)\n"
    "for i, (k, ctx) in enumerate(C.items(), 1):\n"
    "    for qa in gen_qa(ctx, 12):\n"
    "        if isinstance(qa, dict) and qa.get('question') and qa.get('answer'):\n"
    "            all_rows.append({'context': ctx, 'question': qa['question'], 'answer': qa['answer']})\n"
    "    time.sleep(4)\n"
    "    all_rows += gen_refusal(ctx, 6)\n"
    "    time.sleep(4)\n"
    "    print(f'[{i}/{len(C)}] {k}: 누적 {len(all_rows)}개')\n"
    "\n"
    "# 중복 제거 (질문 기준)\n"
    "seen, dedup = set(), []\n"
    "for r in all_rows:\n"
    "    key = r['question'].strip().lower()\n"
    "    if key not in seen:\n"
    "        seen.add(key); dedup.append(r)\n"
    "all_rows = dedup\n"
    "n_ref = sum(1 for r in all_rows if r['answer'] == REFUSE)\n"
    "print(f'\\n총 {len(all_rows)}개 (근거 {len(all_rows)-n_ref} + 거부 {n_ref})')\n"
    "print('예시:', all_rows[len(seed_rows)])"
))

cells.append(md("## 6. train / eval 분리"))
cells.append(code(
    "import random\n"
    "random.seed(42)\n"
    "random.shuffle(all_rows)\n"
    "n_eval = max(12, int(len(all_rows) * 0.12))\n"
    "eval_rows, train_rows = all_rows[:n_eval], all_rows[n_eval:]\n"
    "print(f'train {len(train_rows)} | eval {len(eval_rows)}')"
))

cells.append(md("## 7. 베이스 모델 로드 (4-bit) + LoRA"))
cells.append(code(
    "import torch\n"
    "from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig\n"
    "from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training\n"
    "\n"
    "BASE_MODEL = 'jjminu/polyglot58-chatbot'\n"
    "BASE_TOK   = 'EleutherAI/polyglot-ko-5.8b'\n"
    "try:\n"
    "    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)\n"
    "except Exception:\n"
    "    tokenizer = AutoTokenizer.from_pretrained(BASE_TOK)\n"
    "if tokenizer.pad_token_id is None:\n"
    "    tokenizer.pad_token = tokenizer.eos_token\n"
    "\n"
    "bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type='nf4',\n"
    "    bnb_4bit_compute_dtype=torch.float16, bnb_4bit_use_double_quant=True)\n"
    "model = AutoModelForCausalLM.from_pretrained(BASE_MODEL, quantization_config=bnb, device_map='auto')\n"
    "model = prepare_model_for_kbit_training(model)\n"
    "model = get_peft_model(model, LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05,\n"
    "    bias='none', task_type='CAUSAL_LM', target_modules=['query_key_value']))\n"
    "model.print_trainable_parameters()"
))

cells.append(md("## 8. 토크나이즈 (답변만 학습)"))
cells.append(code(
    "from datasets import Dataset\n"
    "PROMPT_HEAD = (\"" + PROMPT_HEAD + "\")\n"
    "\n"
    "def encode(row):\n"
    "    prompt = PROMPT_HEAD.format(context=row['context'], question=row['question'])\n"
    "    full = prompt + ' ' + row['answer'] + tokenizer.eos_token\n"
    "    p_ids = tokenizer(prompt, add_special_tokens=False)['input_ids']\n"
    "    f_ids = tokenizer(full, add_special_tokens=False, truncation=True, max_length=768)['input_ids']\n"
    "    labels = ([-100] * len(p_ids) + f_ids[len(p_ids):])[:len(f_ids)]\n"
    "    return {'input_ids': f_ids, 'labels': labels, 'attention_mask': [1] * len(f_ids)}\n"
    "\n"
    "train_ds = Dataset.from_list([encode(r) for r in train_rows])\n"
    "eval_ds  = Dataset.from_list([encode(r) for r in eval_rows])\n"
    "print(train_ds, eval_ds)"
))

cells.append(md(
    "## 9. 학습 (평가 기반 — 베스트 체크포인트 자동 선택)\n",
    "매 에폭 eval loss 를 보고, **가장 좋은 시점의 모델**을 최종 채택한다(과적합 방지). "
    "에폭을 넉넉히 줘도 best 만 남으므로 안전하다.",
))
cells.append(code(
    "import torch\n"
    "from dataclasses import dataclass\n"
    "from transformers import Trainer, TrainingArguments\n"
    "\n"
    "@dataclass\n"
    "class Collator:\n"
    "    pad_id: int\n"
    "    def __call__(self, feats):\n"
    "        m = max(len(f['input_ids']) for f in feats)\n"
    "        ii, ll, am = [], [], []\n"
    "        for f in feats:\n"
    "            pad = m - len(f['input_ids'])\n"
    "            ii.append(f['input_ids'] + [self.pad_id] * pad)\n"
    "            ll.append(f['labels'] + [-100] * pad)\n"
    "            am.append(f['attention_mask'] + [0] * pad)\n"
    "        return {'input_ids': torch.tensor(ii), 'labels': torch.tensor(ll),\n"
    "                'attention_mask': torch.tensor(am)}\n"
    "\n"
    "args = TrainingArguments(output_dir='out', per_device_train_batch_size=2,\n"
    "    gradient_accumulation_steps=4, num_train_epochs=10, learning_rate=2e-4,\n"
    "    warmup_ratio=0.05, lr_scheduler_type='cosine', fp16=True, logging_steps=10,\n"
    "    eval_strategy='epoch', save_strategy='epoch', save_total_limit=2,\n"
    "    load_best_model_at_end=True, metric_for_best_model='eval_loss',\n"
    "    greater_is_better=False, report_to='none', remove_unused_columns=False)\n"
    "\n"
    "trainer = Trainer(model=model, args=args, train_dataset=train_ds, eval_dataset=eval_ds,\n"
    "    data_collator=Collator(tokenizer.pad_token_id))\n"
    "trainer.train()\n"
    "print('\\n베스트 eval_loss:', trainer.state.best_metric)"
))

cells.append(md("## 10. 동작 테스트 (근거 + 거부 + 구어체)"))
cells.append(code(
    "import torch\n"
    "model.eval()\n"
    "\n"
    "def gen(context, question, n=64):\n"
    "    ids = tokenizer(PROMPT_HEAD.format(context=context, question=question), return_tensors='pt').to(model.device)\n"
    "    with torch.no_grad():\n"
    "        out = model.generate(**ids, max_new_tokens=n, do_sample=False,\n"
    "            repetition_penalty=1.2, no_repeat_ngram_size=3,\n"
    "            pad_token_id=tokenizer.pad_token_id, eos_token_id=tokenizer.eos_token_id)\n"
    "    t = tokenizer.decode(out[0][ids['input_ids'].shape[1]:], skip_special_tokens=True)\n"
    "    for s in ['###', '\\n']:\n"
    "        i = t.find(s)\n"
    "        if i != -1: t = t[:i]\n"
    "    return t.strip()\n"
    "\n"
    "print('근거 :', gen(C['adapterz'], '어댑터즈 구독료 얼마야?'))\n"
    "print('구어체:', gen(C['refund'], '환불하고싶어'))\n"
    "print('근거 :', gen(C['weeks'], '5주차에 뭐 배워?'))\n"
    "print('거부 :', gen(C['adapterz'], '부트캠프 수강료 얼마야?'))\n"
    "print('거부 :', gen(C['weeks'], '비트코인 사도 돼?'))"
))

cells.append(md("## 11. 병합 + HF Hub 업로드 (재실행 안전)"))
cells.append(code(
    "import torch, gc, os\n"
    "from peft import PeftModel\n"
    "from transformers import AutoModelForCausalLM, AutoTokenizer\n"
    "\n"
    "NEW_REPO = 'jjminu/polyglot58-rag-v2'\n"
    "\n"
    "if 'trainer' in globals() and not os.path.exists('lora_adapter/adapter_config.json'):\n"
    "    trainer.model.save_pretrained('lora_adapter')\n"
    "    (tokenizer if 'tokenizer' in globals() else AutoTokenizer.from_pretrained(BASE_TOK)).save_pretrained('lora_adapter')\n"
    "assert os.path.exists('lora_adapter/adapter_config.json'), 'lora_adapter 없음 -> 학습부터 다시'\n"
    "\n"
    "for _v in ['model', 'trainer', 'base', 'merged']:\n"
    "    globals().pop(_v, None)\n"
    "gc.collect(); torch.cuda.empty_cache()\n"
    "\n"
    "base = AutoModelForCausalLM.from_pretrained(BASE_MODEL, torch_dtype=torch.float16, device_map='auto')\n"
    "merged = PeftModel.from_pretrained(base, 'lora_adapter').merge_and_unload()\n"
    "merged.push_to_hub(NEW_REPO)\n"
    "try:\n"
    "    AutoTokenizer.from_pretrained('lora_adapter').push_to_hub(NEW_REPO)\n"
    "except Exception:\n"
    "    AutoTokenizer.from_pretrained(BASE_TOK).push_to_hub(NEW_REPO)\n"
    "print('업로드 완료 ->', NEW_REPO)"
))

cells.append(md(
    "---\n",
    "## 12. RAG 노트북에 연결\n",
    "`otto_rag_my_model_colab.ipynb` 셀 5: `MODEL_ID = 'jjminu/polyglot58-rag-v2'` 로 바꾸고 셀 6~11 재실행.\n",
    "\n",
    "**더 키우려면:** 셀 5의 `gen_qa(ctx, 12)` 숫자를 늘리거나 docs 를 추가하면 데이터가 커집니다. "
    "데이터가 클수록(수백~수천) 모델이 똑똑해집니다 — 학습 시간보다 **데이터가 핵심 지렛대**.",
))

nb = {
    "cells": cells,
    "metadata": {
        "accelerator": "GPU",
        "colab": {"provenance": []},
        "kernelspec": {"display_name": "Python 3", "name": "python3"},
        "language_info": {"name": "python"},
    },
    "nbformat": 4,
    "nbformat_minor": 0,
}

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)
print("생성:", OUT, "| 셀", len(cells), "| 시드", len(seed_rows))
