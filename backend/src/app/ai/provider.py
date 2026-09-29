from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.ai.config import AIConfig


class AIProviderError(Exception):
    """Base exception for AI provider failures."""


class AIProviderUnavailable(AIProviderError):
    """Raised when the configured AI provider is unavailable or incomplete."""


@dataclass(frozen=True)
class AIResponse:
    provider: str
    model: str
    output: str


class AIProvider(ABC):
    """Provider-agnostic interface for CareSphere AI operations."""

    @abstractmethod
    def generate(
        self,
        *,
        instructions: str,
        input_text: str,
    ) -> AIResponse:
        raise NotImplementedError


class OpenAIProvider(AIProvider):
    """OpenAI implementation of the CareSphere AI provider interface."""

    def __init__(self, config: AIConfig):
        self.config = config

        if not config.api_key:
            raise AIProviderUnavailable(
                "OpenAI API key is not configured"
            )

        if not config.model:
            raise AIProviderUnavailable(
                "AI model is not configured"
            )

        try:
            from openai import OpenAI
        except ImportError as exc:
            raise AIProviderUnavailable(
                "The openai package is not installed"
            ) from exc

        client_kwargs = {
            "api_key": config.api_key,
            "timeout": config.timeout_seconds,
        }

        if config.base_url:
            client_kwargs["base_url"] = config.base_url

        self.client = OpenAI(**client_kwargs)

    def generate(
        self,
        *,
        instructions: str,
        input_text: str,
    ) -> AIResponse:
        try:
            response = self.client.responses.create(
                model=self.config.model,
                instructions=instructions,
                input=input_text,
                max_output_tokens=self.config.max_output_tokens,
            )
        except Exception as exc:
            raise AIProviderError(
                f"AI provider request failed: {exc}"
            ) from exc

        output = getattr(response, "output_text", None)

        if not output:
            raise AIProviderError(
                "AI provider returned an empty response"
            )

        return AIResponse(
            provider="openai",
            model=self.config.model,
            output=output.strip(),
        )


class GeminiProvider(AIProvider):
    """Google Gemini implementation using Google's OpenAI-compatible API."""

    DEFAULT_BASE_URL = (
        "https://generativelanguage.googleapis.com/v1beta/openai/"
    )

    def __init__(self, config: AIConfig):
        self.config = config

        if not config.api_key:
            raise AIProviderUnavailable(
                "Gemini API key is not configured"
            )

        if not config.model:
            raise AIProviderUnavailable(
                "AI model is not configured"
            )

        try:
            from openai import OpenAI
        except ImportError as exc:
            raise AIProviderUnavailable(
                "The openai package is not installed"
            ) from exc

        client_kwargs = {
            "api_key": config.api_key,
            "base_url": config.base_url or self.DEFAULT_BASE_URL,
            "timeout": config.timeout_seconds,
        }

        self.client = OpenAI(**client_kwargs)

    @staticmethod
    def _extract_output(response) -> str:
        """Extract assistant text from the OpenAI-compatible response."""

        try:
            message = response.choices[0].message
        except (AttributeError, IndexError, TypeError) as exc:
            raise AIProviderError(
                "Gemini returned an unexpected response format"
            ) from exc

        content = getattr(message, "content", None)

        if isinstance(content, str):
            return content.strip()

        if isinstance(content, list):
            parts: list[str] = []

            for item in content:
                if isinstance(item, dict):
                    text_value = item.get("text")
                else:
                    text_value = getattr(item, "text", None)

                if isinstance(text_value, str) and text_value.strip():
                    parts.append(text_value.strip())

            return "\n".join(parts).strip()

        return ""

    def generate(
        self,
        *,
        instructions: str,
        input_text: str,
    ) -> AIResponse:
        try:
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {
                        "role": "system",
                        "content": instructions,
                    },
                    {
                        "role": "user",
                        "content": input_text,
                    },
                ],
                max_tokens=self.config.max_output_tokens,
            )
        except Exception as exc:
            raise AIProviderError(
                f"AI provider request failed: {exc}"
            ) from exc

        output = self._extract_output(response)

        if not output:
            raise AIProviderError(
                "Gemini provider returned an empty response"
            )

        return AIResponse(
            provider="gemini",
            model=self.config.model,
            output=output,
        )


def get_ai_provider() -> AIProvider:
    config = get_config()

    if not config.enabled:
        raise AIProviderUnavailable(
            "AI integration is disabled"
        )

    if config.provider == "openai":
        return OpenAIProvider(config)

    if config.provider == "gemini":
        return GeminiProvider(config)

    raise AIProviderUnavailable(
        f"Unsupported AI provider: {config.provider}"
    )


def get_config() -> AIConfig:
    from app.ai.config import get_ai_config

    return get_ai_config()