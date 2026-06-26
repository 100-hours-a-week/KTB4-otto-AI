"""otto_gpt_instruct 추론 래퍼 → Agent 에 넣을 generate_fn 제공.

Colab(또는 체크포인트가 있는 로컬)에서:
    from otto_model import OttoModel
    from agent import Agent
    gen = OttoModel("/content/drive/MyDrive/otto_gpt").generate_fn
    agent = Agent(generate_fn=gen)
    print(agent.run("부산 날씨 어때?"))
"""
from __future__ import annotations

import os

import torch
import torch.nn.functional as F
import sentencepiece as spm

from model import GPT, GPTConfig


class OttoModel:
    # 318M instruct 우선, 없으면 57M instruct 폴백
    _PREFERRED = ["otto_gpt_350m_instruct.pt", "otto_gpt_instruct.pt"]

    def __init__(self, project_dir: str, ckpt_name: str | None = None):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.sp = spm.SentencePieceProcessor(
            model_file=f"{project_dir}/tokenizer_ko.model"
        )
        if ckpt_name is None:  # 가장 좋은 체크포인트 자동 선택 (318M → 57M)
            ckpt_name = next(
                (c for c in self._PREFERRED if os.path.exists(f"{project_dir}/ckpt/{c}")),
                self._PREFERRED[-1],
            )
        print(f"[OttoModel] 라우터 체크포인트: {ckpt_name}")
        ckpt = torch.load(f"{project_dir}/ckpt/{ckpt_name}", map_location=self.device)
        self.config = GPTConfig(**ckpt["config"])
        self.model = GPT(self.config).to(self.device)
        self.model.load_state_dict(ckpt["model"])
        self.model.eval()

    @torch.no_grad()
    def generate_fn(self, prompt: str, max_new_tokens: int = 150,
                    temperature: float = 0.7, top_k: int = 40,
                    rep_penalty: float = 1.3) -> str:
        bs = self.config.block_size
        x = torch.tensor([self.sp.encode(prompt)], dtype=torch.long, device=self.device)
        start = x.size(1)
        for _ in range(max_new_tokens):
            logits, _ = self.model(x[:, -bs:])
            logits = logits[:, -1, :] / temperature
            for t in set(x[0].tolist()):
                logits[0, t] /= rep_penalty
            v, _ = torch.topk(logits, min(top_k, logits.size(-1)))
            logits[logits < v[:, [-1]]] = -float("inf")
            nxt = torch.multinomial(F.softmax(logits, dim=-1), 1)
            if nxt.item() == self.sp.eos_id():
                break
            x = torch.cat((x, nxt), dim=1)
        # 프롬프트 이후 생성분만 반환 (Agent 가 도구호출/답변을 파싱)
        return self.sp.decode(x[0, start:].tolist()).strip()
