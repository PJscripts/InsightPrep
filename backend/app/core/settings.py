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

    gemini_api_key: str = ""
    llm_mode: str = "mock"
    gemini_model: str = "gemini-2.5-flash"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()
