from app.core.settings import settings
from app.services.answer_evaluator import AnswerEvaluator
from app.services.mock_answer_evaluator import MockAnswerEvaluator


def get_answer_evaluator() -> AnswerEvaluator:
    if settings.llm_mode.lower() == "gemini":
        from app.services.gemini_answer_evaluator import (
            GeminiAnswerEvaluator,
        )

        return GeminiAnswerEvaluator()

    return MockAnswerEvaluator()
