from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Interview Assessment System"
    app_version: str = "0.1.0"
    environment: str = "development"

    backend_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:5173"

    openai_api_key: str = ""
    database_url: str = ""
    jwt_secret: str = ""
    jwt_expiration_minutes: int = 60
    llm_timeout_seconds: int = 30
    llm_max_retries: int = 2

    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.7-flash"

    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-120b"

    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = ""
    elevenlabs_model_id: str = "eleven_multilingual_v2"
    elevenlabs_output_format: str = "mp3_44100_128"
    elevenlabs_timeout_seconds: int = 30

    resume_primary_llm: str = "gemini"
    resume_fallback_llm: str = "groq"

    question_primary_llm: str = "groq"
    question_fallback_llm: str = "gemini"

    evaluation_primary_llm: str = "groq"
    evaluation_fallback_llm: str = "gemini"

    llm_final_fallback: str = "mock"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()
