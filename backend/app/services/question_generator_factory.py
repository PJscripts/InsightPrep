from app.core.settings import settings
from app.services.mock_question_generator import MockQuestionGenerator
from app.services.question_generator import QuestionGenerator


def get_question_generator() -> QuestionGenerator:
    if settings.llm_mode.lower() == "gemini":
        from app.services.gemini_question_generator import (
            GeminiQuestionGenerator,
        )

        return GeminiQuestionGenerator()

    return MockQuestionGenerator()
