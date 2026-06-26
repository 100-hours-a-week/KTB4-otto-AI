"""RAG 체인: Retriever -> Prompt -> Gemini -> Parser (LCEL).

멀티턴 대응(v3):
  - RunnableWithMessageHistory 로 session_id 별 대화 기록 유지.
  - history-aware 질문 재작성: 후속 질문을 직전 대화로 보강해 '독립형 질문'으로 바꾼 뒤 검색.
  - RunnableBranch 로 첫 턴(기록 없음)에는 재작성 LLM 호출을 건너뜀.
"""
from __future__ import annotations

from operator import itemgetter
from typing import Dict, List

from langchain_core.chat_history import BaseChatMessageHistory, InMemoryChatMessageHistory
from langchain_core.documents import Document
from langchain_core.messages import trim_messages
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import (
    RunnableBranch,
    RunnablePassthrough,
)
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_google_genai import ChatGoogleGenerativeAI

from app.config import get_rate_limiter, get_settings
from app.ingest import load_index

SYSTEM_PROMPT = """당신은 주어진 '참고 문서'만을 근거로 답하는 한국어 어시스턴트입니다.
규칙:
1. 반드시 아래 참고 문서에 있는 정보만으로 답변하세요.
2. 문서에서 답을 찾을 수 없으면 "제공된 문서에서 답을 찾을 수 없습니다." 라고만 답하세요.
3. 추측하거나 지어내지 말고, 간결하고 정확하게 답하세요.

[참고 문서]
{context}
"""

# 답변 프롬프트: 시스템 + 지난 대화 + 이번 질문
ANSWER_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder("chat_history", optional=True),
        ("human", "{question}"),
    ]
)

# 후속 질문 -> 독립형 질문 재작성 프롬프트 (검색 품질용)
CONTEXTUALIZE_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "이전 대화를 참고해서, 사용자의 마지막 질문을 그 자체로 이해 가능한 "
            "'독립형 질문'으로 다시 써라. 질문에 답하지 말고 질문만 다시 쓴다. "
            "이미 독립적이면 그대로 반환한다.",
        ),
        MessagesPlaceholder("chat_history"),
        ("human", "{question}"),
    ]
)


def format_docs(docs: List[Document]) -> str:
    """검색된 Document 들을 프롬프트에 넣을 하나의 문자열로 합친다."""
    return "\n\n---\n\n".join(
        f"[출처: {d.metadata.get('source', '?')}] {d.page_content}" for d in docs
    )


class RAGChain:
    """검색기 + LLM 을 LCEL 로 묶은 RAG 파이프라인 (싱글톤으로 사용)."""

    def __init__(self) -> None:
        settings = get_settings()
        self.retriever = load_index().as_retriever(
            search_kwargs={"k": settings.top_k}
        )
        self.llm = ChatGoogleGenerativeAI(
            model=settings.gemini_chat_model,
            google_api_key=settings.google_api_key,
            temperature=0.1,
            rate_limiter=get_rate_limiter(),
        )

        # 세션별 대화 기록 저장소 (메모리)
        self._sessions: Dict[str, InMemoryChatMessageHistory] = {}

        # 대화 기록 트리머: 프롬프트에 넣을 메시지를 '최근 N개'로 제한.
        # token_counter=len 이면 '메시지 개수' 기준 → 대화가 길어져도 토큰/컨텍스트 안정.
        self._trimmer = trim_messages(
            max_tokens=settings.history_window,
            strategy="last",          # 최신 메시지부터 남김
            token_counter=len,        # 메시지 개수로 카운트
            start_on="human",         # human 메시지 경계에서 시작(human/ai 쌍 정렬)
            include_system=False,     # system 프롬프트는 기록이 아닌 템플릿에 있음
        )

        # 0) 기록을 트리밍해서 이후 단계(재작성/답변)가 모두 제한된 기록만 보게 함
        trim_history = RunnablePassthrough.assign(
            chat_history=lambda x: self._trimmer.invoke(x.get("chat_history", []))
        )

        # 1) 검색에 쓸 질문: 기록 있으면 재작성, 없으면 원문 그대로 (LLM 절약)
        contextualize = CONTEXTUALIZE_PROMPT | self.llm | StrOutputParser()
        search_query = RunnableBranch(
            (lambda x: not x.get("chat_history"), itemgetter("question")),
            contextualize,
        )

        # 2) 검색을 한 번만 하고 그 결과를 답변 생성과 출처 표시에 공유
        self.rag_chain = (
            trim_history
            | RunnablePassthrough.assign(search_query=search_query)
            .assign(docs=itemgetter("search_query") | self.retriever)
            .assign(
                answer=(
                    {
                        "context": itemgetter("docs")
                        | RunnablePassthrough()
                        | format_docs,
                        "question": itemgetter("question"),
                        "chat_history": lambda x: x.get("chat_history", []),
                    }
                    | ANSWER_PROMPT
                    | self.llm
                    | StrOutputParser()
                )
            )
        )

        # 3) 대화 기록을 자동 주입/저장하는 멀티턴 래퍼
        self.conversational = RunnableWithMessageHistory(
            self.rag_chain,
            self._get_history,
            input_messages_key="question",
            history_messages_key="chat_history",
            output_messages_key="answer",
        )

    def _get_history(self, session_id: str) -> BaseChatMessageHistory:
        if session_id not in self._sessions:
            self._sessions[session_id] = InMemoryChatMessageHistory()
        return self._sessions[session_id]

    @staticmethod
    def _pack(question: str, result: Dict) -> Dict:
        docs: List[Document] = result["docs"]
        return {
            "question": question,
            "answer": result["answer"],
            "contexts": [d.page_content for d in docs],
            "sources": sorted({d.metadata.get("source", "?") for d in docs}),
        }

    def query(self, question: str) -> Dict:
        """단발성 질문 (대화 기록 없음) -> 답변 + 근거 문서 + 출처."""
        result = self.rag_chain.invoke({"question": question})
        return self._pack(question, result)

    def chat(self, question: str, session_id: str = "default") -> Dict:
        """멀티턴 대화 -> 답변 + 근거 + 출처. session_id 로 대화 맥락 유지."""
        result = self.conversational.invoke(
            {"question": question},
            config={"configurable": {"session_id": session_id}},
        )
        return self._pack(question, result)

    def reset_session(self, session_id: str = "default") -> None:
        """해당 세션의 대화 기록 삭제."""
        self._sessions.pop(session_id, None)

    def search(self, question: str) -> List[Dict]:
        """검색만 (LLM 호출 없이) — 디버깅/검색 품질 확인용."""
        docs = self.retriever.invoke(question)
        return [
            {"text": d.page_content, "source": d.metadata.get("source", "?")}
            for d in docs
        ]


_chain: RAGChain | None = None


def get_chain() -> RAGChain:
    """싱글톤 RAG 체인 (앱 시작 시 1회 초기화)."""
    global _chain
    if _chain is None:
        _chain = RAGChain()
    return _chain


def reset_chain() -> None:
    """인덱스 재구축 후 체인을 새 인덱스로 갱신."""
    global _chain
    _chain = None
