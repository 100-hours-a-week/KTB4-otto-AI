"""RAG 파이프라인: 검색(Retrieve) -> 프롬프트 구성 -> Gemini 생성(Generate)."""
from __future__ import annotations

from typing import Dict, List

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_google_genai import ChatGoogleGenerativeAI

from app.config import get_settings
from app.vector_store import load_index

SYSTEM_PROMPT = """당신은 주어진 '문맥(context)'만을 근거로 답하는 한국어 어시스턴트입니다.
규칙:
1. 반드시 아래 문맥에 있는 정보만으로 답변하세요.
2. 문맥에서 답을 찾을 수 없으면 "제공된 문서에서 답을 찾을 수 없습니다." 라고 답하세요.
3. 추측하지 말고, 간결하고 정확하게 답하세요.

[문맥]
{context}
"""

PROMPT = ChatPromptTemplate.from_messages(
    [("system", SYSTEM_PROMPT), ("human", "{question}")]
)


def _format_docs(docs: List[Document]) -> str:
    return "\n\n---\n\n".join(
        f"[출처: {d.metadata.get('source', '?')}] {d.page_content}" for d in docs
    )


class RAGPipeline:
    """검색기 + LLM을 묶은 RAG 파이프라인."""

    def __init__(self) -> None:
        settings = get_settings()
        self.vectorstore = load_index()
        self.retriever = self.vectorstore.as_retriever(
            search_kwargs={"k": settings.top_k}
        )
        self.llm = ChatGoogleGenerativeAI(
            model=settings.gemini_chat_model,
            google_api_key=settings.google_api_key,
            temperature=0.1,
        )
        # LCEL 체인: 답변 문자열만 생성
        self.answer_chain = (
            {
                "context": (lambda x: x["question"]) | self.retriever | _format_docs,
                "question": (lambda x: x["question"]),
            }
            | PROMPT
            | self.llm
            | StrOutputParser()
        )

    def retrieve(self, question: str) -> List[Document]:
        return self.retriever.invoke(question)

    def query(self, question: str) -> Dict:
        """질문에 대해 답변 + 근거 문서를 함께 반환."""
        contexts = self.retrieve(question)
        answer = self.answer_chain.invoke({"question": question})
        return {
            "question": question,
            "answer": answer,
            "contexts": [c.page_content for c in contexts],
            "sources": sorted({c.metadata.get("source", "?") for c in contexts}),
        }


_pipeline: RAGPipeline | None = None


def get_pipeline() -> RAGPipeline:
    """싱글톤 파이프라인 (앱 시작 시 1회 초기화)."""
    global _pipeline
    if _pipeline is None:
        _pipeline = RAGPipeline()
    return _pipeline
