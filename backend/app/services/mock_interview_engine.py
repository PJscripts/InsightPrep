from typing import Any

from app.services.interview_engine import InterviewEngine
from app.services.mock_question_generator import mock_question_generator


class MockInterviewEngine:
    def generate_question(
        self,
        resume_analysis: dict[str, Any],
        interview_type: str,
        difficulty: str,
        question_number: int,
    ) -> str:
        return mock_question_generator.generate_question(
            resume_analysis=resume_analysis,
            interview_type=interview_type,
            difficulty=difficulty,
            question_number=question_number,
        )

    def is_complete(
        self,
        current_question: int,
        total_questions: int,
    ) -> bool:
        return current_question >= total_questions


mock_interview_engine: InterviewEngine = MockInterviewEngine()
