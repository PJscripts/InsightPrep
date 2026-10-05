from typing import Any, Protocol

from app.services.rag.answer_context import AnswerRAGContext


class AnswerEvaluator(Protocol):
    def evaluate(
        self,
        question: str,
        answer: str,
        resume_analysis: dict[str, Any],
        rag_context: AnswerRAGContext | None = None,
    ) -> dict[str, Any]: ...
