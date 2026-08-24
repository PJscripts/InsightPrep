from app.core.settings import settings


def is_gemini_enabled() -> bool:
    return settings.llm_mode.lower() == "gemini"


def validate_llm_configuration() -> None:
    if is_gemini_enabled() and not settings.gemini_api_key:
        raise ValueError(
            "LLM_MODE is set to gemini but GEMINI_API_KEY is not configured"
        )
