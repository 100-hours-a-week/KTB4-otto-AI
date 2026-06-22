# otto-GPT : 처음부터 만드는 한국어 언어모델

토크나이저·아키텍처·가중치를 전부 직접 만드는 from-scratch GPT.

| 항목 | 내용 |
|---|---|
| 아키텍처 | GPT (Decoder-only Transformer) 직접 구현 |
| 규모 | 약 57M (n_layer=10, n_embd=624) |
| 토크나이저 | SentencePiece BPE 직접 학습 (vocab 16K) |
| 학습 | 한국어 위키로 사전학습 → KoAlpaca instruction 튜닝 |
| 환경 | Colab GPU |

## 파일
- `otto_gpt_scratch.ipynb` — 토크나이저 학습 → 사전학습 (체크포인트 재개 지원)
- `finetune_instruct_colab.ipynb` — 사전학습 모델을 질문-답변으로 추가 학습

## 실행 순서
1. `otto_gpt_scratch.ipynb` 를 위에서부터 실행 → `otto_gpt.pt` 생성
2. `finetune_instruct_colab.ipynb` 실행 → `otto_gpt_instruct.pt` 생성 (질문에 답하는 모델)

체크포인트·토크나이저는 Google Drive(`MyDrive/otto_gpt/`)에 저장되어, 다음 세션에서 이어서 학습할 수 있다.
