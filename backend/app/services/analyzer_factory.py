from app.core.settings import settings
from app.services.gemini_resume_analyzer import GeminiResumeAnalyzer
from app.services.groq_resume_analyzer import GroqResumeAnalyzer
from app.services.mock_resume_analyzer import MockResumeAnalyzer
from app.services.resume_analyzer import ResumeAnalyzer


def get_resume_analyzer() -> ResumeAnalyzer:
    provider = settings.resume_primary_llm.lower()

    if provider == "gemini":
        return GeminiResumeAnalyzer()

    if provider == "groq":
        return GroqResumeAnalyzer()

    return MockResumeAnalyzer()
