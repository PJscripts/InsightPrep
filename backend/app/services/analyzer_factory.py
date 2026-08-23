from app.core.settings import settings
from app.services.mock_resume_analyzer import MockResumeAnalyzer
from app.services.resume_analyzer import ResumeAnalyzer


def get_resume_analyzer() -> ResumeAnalyzer:
    if settings.llm_mode.lower() == "gemini":
        from app.services.gemini_resume_analyzer import GeminiResumeAnalyzer

        return GeminiResumeAnalyzer()

    return MockResumeAnalyzer()
