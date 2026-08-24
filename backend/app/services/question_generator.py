from typing import Any, Protocol


class QuestionGenerator(Protocol):
    def generate_question(
        self,
        resume_analysis: dict[str, Any],
        interview_type: str,
        difficulty: str,
        question_number: int,
    ) -> str: ...
