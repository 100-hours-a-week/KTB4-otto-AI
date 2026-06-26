"""otto RAG (내 모델) Colab 노트북 생성기.

프로젝트의 docs/ 와 dataset.jsonl 을 내장해 자체 완결형 .ipynb 를 만든다.
"""
import json
import os

ROOT = "/Users/minwoo/7주차/langchain_rag"
OUT = os.path.join(ROOT, "colab", "otto_rag_my_model_colab.ipynb")

# --- 프로젝트 자료 읽어서 내장 ---
docs = {}
for name in sorted(os.listdir(os.path.join(ROOT, "docs"))):
    if name.endswith(".md"):
        with open(os.path.join(ROOT, "docs", name), encoding="utf-8") as f:
            docs[name] = f.read()

with open(os.path.join(ROOT, "evaluation", "dataset.jsonl"), encoding="utf-8") as f:
    dataset_text = f.read()


def md(*lines):
    return {"cell_type": "markdown", "metadata": {}, "source": list(lines)}


def code(src):
    return {
        "cell_type": "code",
        "metadata": {},
        "execution_count": None,
        "outputs": [],
        "source": src if isinstance(src, str) else "\n".join(src),
    }


cells = []

cells.append(md(
    "# otto RAG — **내 파인튜닝 모델**로 돌리는 LangChain RAG + FastAPI + LangSmith\n",
    "\n",
    "내가 학습시킨 모델(`jjminu/polyglot58-chatbot`, polyglot-ko 5.8B)을 GPU에 올려서:\n",
    "1. **LangChain RAG** 파이프라인 (검색 → 프롬프트 → 내 모델 → 답변)\n",
    "2. **FastAPI** REST API (ngrok 터널로 외부 공개)\n",
    "3. **LangSmith** Tracing + Dataset 평가\n",
    "\n",
    "> 런타임 유형을 **GPU**(가능하면 A100/L4)로 설정한 뒤 위에서부터 차례로 실행하세요.",
))

cells.append(md("## 1. 패키지 설치"))
cells.append(code(
    "# Chroma 대신 InMemoryVectorStore 사용 -> chromadb 가 numpy 를 다운그레이드하는 충돌 회피\n"
    "!pip -q install langchain==0.3.13 langchain-community==0.3.13 \\\n"
    "  \"langsmith>=0.2.10,<0.3\" sentence-transformers pyngrok \\\n"
    "  fastapi \"uvicorn[standard]\" nest-asyncio langchain-google-genai==2.0.7"
))

cells.append(md("## 2. GPU 확인"))
cells.append(code(
    "import torch\n"
    "print('torch', torch.__version__, '| CUDA', torch.cuda.is_available())\n"
    "print('GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU (런타임>유형변경에서 GPU 선택)')"
))

cells.append(md("## 3. 문서 / 평가셋 파일 생성 (자체 내장)"))
cells.append(code(
    "import os, json\n"
    "os.makedirs('docs', exist_ok=True)\n"
    "docs = " + json.dumps(docs, ensure_ascii=False, indent=2) + "\n"
    "for name, content in docs.items():\n"
    "    open(f'docs/{name}', 'w', encoding='utf-8').write(content)\n"
    "\n"
    "dataset_text = " + json.dumps(dataset_text, ensure_ascii=False) + "\n"
    "open('dataset.jsonl', 'w', encoding='utf-8').write(dataset_text)\n"
    "print('문서', len(docs), '개 + dataset.jsonl 생성 완료')"
))

cells.append(md(
    "## 4. API 키 설정\n",
    "- **LangSmith** 키는 필수 (Tracing/평가 기록). https://smith.langchain.com → Settings → API Keys\n",
    "- **Google** 키는 선택 (평가 correctness judge용). 없으면 source_match만 채점.",
))
cells.append(code(
    "import os, getpass\n"
    "os.environ['LANGCHAIN_TRACING_V2'] = 'true'\n"
    "os.environ['LANGCHAIN_PROJECT'] = 'otto-rag-my-model'\n"
    "os.environ['LANGCHAIN_API_KEY'] = getpass.getpass('LangSmith API Key (lsv2_...): ')\n"
    "g = getpass.getpass('Google API Key (평가 judge용, 없으면 Enter): ')\n"
    "if g.strip():\n"
    "    os.environ['GOOGLE_API_KEY'] = g.strip()"
))

cells.append(md(
    "## 5. 내 모델 로드 + 빠른 품질 확인\n",
    "5.8B 모델이라 다운로드/로드에 몇 분 걸립니다. 아래 생성 결과로 **품질을 먼저 눈으로 확인**하세요.\n",
    "(토크나이저가 안 잡히면 자동으로 베이스 `polyglot-ko-5.8b` 토크나이저로 폴백합니다.)",
))
cells.append(code(
    "import torch\n"
    "from transformers import AutoTokenizer, AutoModelForCausalLM\n"
    "\n"
    "MODEL_ID = 'jjminu/polyglot58-chatbot'   # 더 작은 모델: 'jjminu/koalpaca-chatbot'\n"
    "BASE_TOK = 'EleutherAI/polyglot-ko-5.8b'\n"
    "\n"
    "try:\n"
    "    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)\n"
    "except Exception as e:\n"
    "    print('모델 토크나이저 로드 실패 -> 베이스 토크나이저 사용:', str(e)[:80])\n"
    "    tokenizer = AutoTokenizer.from_pretrained(BASE_TOK)\n"
    "\n"
    "model = AutoModelForCausalLM.from_pretrained(MODEL_ID, torch_dtype=torch.float16, device_map='auto')\n"
    "if tokenizer.pad_token_id is None:\n"
    "    tokenizer.pad_token = tokenizer.eos_token\n"
    "model.eval()\n"
    "print('로드 완료:', round(model.num_parameters()/1e9, 2), 'B params')\n"
    "\n"
    "# 재학습 모델과 동일하게 greedy 디코딩 + 환각 꼬리 자르기\n"
    "STOP = ['###', '[출처', '출처:', 'http', '웹사이트', '고객센터', '\\n\\n', '\\n[']\n"
    "\n"
    "def generate(prompt, max_new_tokens=80):\n"
    "    ids = tokenizer(prompt, return_tensors='pt', truncation=True, max_length=1024).to(model.device)\n"
    "    with torch.no_grad():\n"
    "        out = model.generate(**ids, max_new_tokens=max_new_tokens, do_sample=False,\n"
    "            repetition_penalty=1.3, no_repeat_ngram_size=3,\n"
    "            pad_token_id=tokenizer.pad_token_id, eos_token_id=tokenizer.eos_token_id)\n"
    "    text = tokenizer.decode(out[0][ids['input_ids'].shape[1]:], skip_special_tokens=True)\n"
    "    cut = len(text)\n"
    "    for m in STOP:\n"
    "        i = text.find(m)\n"
    "        if i != -1:\n"
    "            cut = min(cut, i)\n"
    "    return text[:cut].strip()\n"
    "\n"
    "print(generate('### 질문: 파이썬이 뭐야?\\n\\n### 답변:'))"
))

cells.append(md("## 6. 임베딩(ko-sroberta) + InMemoryVectorStore 인덱스 구축"))
cells.append(code(
    "import glob, os, torch\n"
    "from langchain_community.embeddings import HuggingFaceEmbeddings\n"
    "from langchain_community.document_loaders import TextLoader\n"
    "from langchain_text_splitters import RecursiveCharacterTextSplitter\n"
    "from langchain_core.vectorstores import InMemoryVectorStore\n"
    "\n"
    "device = 'cuda' if torch.cuda.is_available() else 'cpu'\n"
    "emb = HuggingFaceEmbeddings(model_name='jhgan/ko-sroberta-multitask', model_kwargs={'device': device})\n"
    "\n"
    "documents = []\n"
    "for p in sorted(glob.glob('docs/*.md')):\n"
    "    loaded = TextLoader(p, encoding='utf-8').load()\n"
    "    for d in loaded:\n"
    "        d.metadata['source'] = os.path.basename(p)\n"
    "    documents += loaded\n"
    "\n"
    "splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=80,\n"
    "    separators=['\\n## ', '\\n\\n', '\\n', '. ', ' ', ''])\n"
    "chunks = splitter.split_documents(documents)\n"
    "vs = InMemoryVectorStore.from_documents(chunks, emb)\n"
    "retriever = vs.as_retriever(search_kwargs={'k': 3})\n"
    "print('인덱싱 완료:', len(chunks), '청크')"
))

cells.append(md(
    "## 7. LCEL RAG 체인 (내 모델 연결)\n",
    "`retriever | prompt | 내 모델 | 답변` — LangChain의 Runnable 인터페이스로 모델만 갈아끼운 형태.",
))
cells.append(code(
    "from operator import itemgetter\n"
    "from langchain_core.prompts import PromptTemplate\n"
    "from langchain_core.runnables import RunnableLambda, RunnablePassthrough\n"
    "\n"
    "# 재파인튜닝 노트북의 학습 프롬프트와 동일해야 효과가 납니다\n"
    "PROMPT = PromptTemplate.from_template(\n"
    "    \"### 질문: 아래 [문서] 내용만 근거로 질문에 한국어 한 문장으로만 답해줘. \"\n"
    "    \"문서에 답이 없으면 다른 말 없이 정확히 '제공된 문서에서 답을 찾을 수 없습니다'라고만 답해. 추측·부연 금지.\\n\\n\"\n"
    "    '[문서]\\n{context}\\n\\n[질문] {question}\\n\\n### 답변:'\n"
    ")\n"
    "\n"
    "def format_docs(docs):\n"
    "    return '\\n\\n'.join(f\"[출처: {d.metadata.get('source','?')}] {d.page_content}\" for d in docs)\n"
    "\n"
    "# 내 모델을 LangChain Runnable 로 래핑 (PromptValue -> 문자열 -> 생성)\n"
    "llm = RunnableLambda(lambda pv: generate(pv.to_string()))\n"
    "\n"
    "rag_chain = RunnablePassthrough.assign(\n"
    "    docs=itemgetter('question') | retriever\n"
    ").assign(\n"
    "    answer={'context': itemgetter('docs') | RunnableLambda(format_docs),\n"
    "            'question': itemgetter('question')} | PROMPT | llm\n"
    ")\n"
    "\n"
    "def query(q):\n"
    "    r = rag_chain.invoke({'question': q})\n"
    "    return {'question': q, 'answer': r['answer'],\n"
    "            'sources': sorted({d.metadata.get('source','?') for d in r['docs']}),\n"
    "            'contexts': [d.page_content for d in r['docs']]}"
))

cells.append(md("## 8. RAG 동작 테스트"))
cells.append(code(
    "for q in ['어댑터즈 구독료 얼마야?', '부트캠프 환불 정책 알려줘', '비트코인 사도 돼?']:\n"
    "    r = query(q)\n"
    "    print('Q:', q)\n"
    "    print('A:', r['answer'])\n"
    "    print('출처:', r['sources'])\n"
    "    print()"
))

cells.append(md(
    "## 9. FastAPI + ngrok 으로 REST API 공개\n",
    "ngrok 무료 토큰 필요: https://dashboard.ngrok.com/get-started/your-authtoken",
))
cells.append(code(
    "import nest_asyncio, threading, time, getpass\n"
    "import uvicorn\n"
    "from fastapi import FastAPI\n"
    "from pydantic import BaseModel\n"
    "from pyngrok import ngrok\n"
    "\n"
    "nest_asyncio.apply()\n"
    "ngrok.set_auth_token(getpass.getpass('ngrok authtoken: '))\n"
    "\n"
    "api = FastAPI(title='otto RAG (my model)')\n"
    "\n"
    "class Query(BaseModel):\n"
    "    question: str\n"
    "\n"
    "@api.get('/health')\n"
    "def health():\n"
    "    return {'status': 'ok'}\n"
    "\n"
    "@api.post('/query')\n"
    "def do_query(req: Query):\n"
    "    return query(req.question)\n"
    "\n"
    "ngrok.kill()\n"
    "public = ngrok.connect(8000)\n"
    "print('PUBLIC URL:', public.public_url)\n"
    "threading.Thread(target=lambda: uvicorn.run(api, host='0.0.0.0', port=8000), daemon=True).start()\n"
    "time.sleep(3)\n"
    "print('서버 기동 완료')"
))

cells.append(md("## 10. API 호출 테스트"))
cells.append(code(
    "import requests\n"
    "print(requests.get(public.public_url + '/health').json())\n"
    "r = requests.post(public.public_url + '/query', json={'question': '부트캠프 수강료 얼마야?'})\n"
    "print(r.json())"
))

cells.append(md(
    "## 11. LangSmith Dataset 평가\n",
    "- **correctness**: Gemini judge (Google 키 있을 때만, 내 모델 답변을 채점)\n",
    "- **source_match**: 기대 출처가 검색 결과에 포함됐는지 (LLM 불필요)",
))
cells.append(code(
    "import json, os\n"
    "from langsmith import Client, evaluate\n"
    "\n"
    "client = Client()\n"
    "data = [json.loads(l) for l in open('dataset.jsonl', encoding='utf-8') if l.strip()]\n"
    "NAME = 'otto-rag-qa-my-model'\n"
    "\n"
    "if not client.has_dataset(dataset_name=NAME):\n"
    "    ds = client.create_dataset(dataset_name=NAME)\n"
    "    client.create_examples(\n"
    "        inputs=[{'question': r['question']} for r in data],\n"
    "        outputs=[{'answer': r['answer'], 'source': r['source']} for r in data],\n"
    "        dataset_id=ds.id)\n"
    "    print('Dataset 업로드:', len(data))\n"
    "\n"
    "def target(inputs):\n"
    "    return query(inputs['question'])\n"
    "\n"
    "def correctness(run, example):\n"
    "    if not os.environ.get('GOOGLE_API_KEY'):\n"
    "        return {'key': 'correctness', 'score': None}\n"
    "    from langchain_google_genai import ChatGoogleGenerativeAI\n"
    "    judge = ChatGoogleGenerativeAI(model='gemini-2.5-flash-lite', temperature=0)\n"
    "    pred = (run.outputs or {}).get('answer', '')\n"
    "    ref = (example.outputs or {}).get('answer', '')\n"
    "    v = judge.invoke('기준정답과 답변이 핵심 사실에서 일치하면 CORRECT, 아니면 INCORRECT 만 답해.\\n'\n"
    "                     f'기준: {ref}\\n답변: {pred}').content\n"
    "    return {'key': 'correctness', 'score': int('CORRECT' in v.upper() and 'INCORRECT' not in v.upper())}\n"
    "\n"
    "def source_match(run, example):\n"
    "    exp = (example.outputs or {}).get('source', '')\n"
    "    src = (run.outputs or {}).get('sources', [])\n"
    "    if not exp:\n"
    "        return {'key': 'source_match', 'score': None}\n"
    "    return {'key': 'source_match', 'score': int(exp in src)}\n"
    "\n"
    "results = evaluate(target, data=NAME, evaluators=[correctness, source_match],\n"
    "    experiment_prefix='otto-my-model', max_concurrency=1)\n"
    "print('평가 완료 — https://smith.langchain.com 에서 확인')"
))

cells.append(md(
    "---\n",
    "**확인:** https://smith.langchain.com → Projects `otto-rag-my-model`(Tracing), Datasets & Experiments `otto-rag-qa-my-model`(평가 점수).\n",
    "\n",
    "내 모델 답변 품질이 낮으면, 데이터/에폭을 늘려 재파인튜닝 후 같은 노트북에서 `MODEL_ID` 만 바꾸면 됩니다.",
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
print("생성:", OUT, "| 셀", len(cells), "개")
