from dataclasses import dataclass

from app.config import settings


@dataclass(frozen=True)
class AIConfig:
    enabled: bool
    provider: str
    model: str
    api_key: str
    base_url: str
    timeout_seconds: int
    max_output_tokens: int


def get_ai_config() -> AIConfig:
    return AIConfig(
        enabled=settings.ai_enabled,
        provider=settings.ai_provider.strip().lower(),
        model=settings.ai_model.strip(),
        api_key=settings.ai_api_key,
        base_url=settings.ai_base_url.strip(),
        timeout_seconds=settings.ai_timeout_seconds,
        max_output_tokens=settings.ai_max_output_tokens,
    )