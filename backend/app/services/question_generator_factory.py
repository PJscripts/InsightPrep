from app.services.gemini_question_generator import GeminiQuestionGenerator
from app.services.groq_question_generator import GroqQuestionGenerator
from app.services.mock_question_generator import MockQuestionGenerator


def get_question_generator(provider: str = "mock"):
    provider = provider.lower()

    if provider == "gemini":
        return GeminiQuestionGenerator()

    if provider == "groq":
        return GroqQuestionGenerator()

    return MockQuestionGenerator()
