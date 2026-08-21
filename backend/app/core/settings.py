from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Interview Assessment System"
    app_version: str = "0.1.0"
    environment: str = "development"

    backend_url: str = "http://127.0.0.1:8000"
    frontend_url: str = "http://localhost:5173"

    openai_api_key: str = ""
    database_url: str = ""
    jwt_secret: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()
