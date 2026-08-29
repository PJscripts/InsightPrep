from app.services.gemini_answer_evaluator import GeminiAnswerEvaluator
from app.services.groq_answer_evaluator import GroqAnswerEvaluator
from app.services.mock_answer_evaluator import MockAnswerEvaluator


def get_answer_evaluator(provider: str = "mock"):
    provider = provider.lower()

    if provider == "gemini":
        return GeminiAnswerEvaluator()

    if provider == "groq":
        return GroqAnswerEvaluator()

    return MockAnswerEvaluator()
