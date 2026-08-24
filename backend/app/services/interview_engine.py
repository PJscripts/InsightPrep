from typing import Any, Protocol


class InterviewEngine(Protocol):
    def generate_question(
        self,
        resume_analysis: dict[str, Any],
        interview_type: str,
        difficulty: str,
        question_number: int,
    ) -> str: ...

    def is_complete(
        self,
        current_question: int,
        total_questions: int,
    ) -> bool: ...
