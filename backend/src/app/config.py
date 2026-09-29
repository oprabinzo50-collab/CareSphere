from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "CareSphere"
    app_version: str = "0.1.0"

    database_url: str = ""

    # JWT security settings
    secret_key: str = ""
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # AI settings
    ai_enabled: bool = False
    ai_provider: str = "openai"
    ai_model: str = ""
    ai_api_key: str = ""
    ai_base_url: str = ""
    ai_timeout_seconds: int = 30
    ai_max_output_tokens: int = 1200

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()