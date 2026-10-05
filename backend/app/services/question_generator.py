from typing import Any, Protocol

from app.services.rag.question_context import QuestionRAGContext


class QuestionGenerator(Protocol):
    def generate_question(
        self,
        resume_analysis: dict[str, Any],
        interview_type: str,
        difficulty: str,
        question_number: int,
        previous_questions: list[str],
        previous_answers: list[str],
        previous_evaluations: list[dict[str, Any]],
        rag_context: QuestionRAGContext | None = None,
    ) -> str: ...
