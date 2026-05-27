import logging
import time
from abc import ABC, abstractmethod
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)


class LLMError(Exception):
    """Base error for LLM operations."""


class LLMConfigError(LLMError):
    """Missing or invalid LLM configuration."""


class LLMRateLimitError(LLMError):
    """Groq rate limit exceeded."""


class LLMClient(ABC):
    @abstractmethod
    def complete(self, messages: list[dict[str, str]]) -> str:
        """Send chat messages and return the assistant text content."""


class GroqClient(LLMClient):
    """Groq chat completions client (primary MVP provider)."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
        max_retries: int | None = None,
    ) -> None:
        self._api_key = api_key if api_key is not None else settings.resolved_llm_api_key
        self._model = model or settings.llm_model
        self._temperature = temperature if temperature is not None else settings.llm_temperature
        self._max_retries = max_retries if max_retries is not None else settings.llm_max_retries

        if not self._api_key:
            raise LLMConfigError(
                "Groq API key not configured. Set LLM_API_KEY or GROQ_API_KEY "
                "in .env or Streamlit Secrets."
            )

    def complete(self, messages: list[dict[str, str]]) -> str:
        from groq import Groq

        client = Groq(api_key=self._api_key)
        last_error: Exception | None = None

        for attempt in range(self._max_retries + 1):
            try:
                response = client.chat.completions.create(
                    model=self._model,
                    messages=messages,
                    temperature=self._temperature,
                    response_format={"type": "json_object"},
                )
                content = response.choices[0].message.content
                if not content or not content.strip():
                    raise LLMError("Groq returned empty response")
                return content.strip()
            except Exception as e:
                last_error = e
                if _is_rate_limit(e) and attempt < self._max_retries:
                    wait = 2**attempt
                    logger.warning("Groq rate limit, retrying in %ss", wait)
                    time.sleep(wait)
                    continue
                if _is_retryable(e) and attempt < self._max_retries:
                    logger.warning("Groq request failed (%s), retrying", e)
                    time.sleep(1)
                    continue
                break

        raise LLMError(f"Groq request failed: {last_error}") from last_error


class MockLLMClient(LLMClient):
    """Returns a fixed response for tests."""

    def __init__(self, response: str) -> None:
        self._response = response

    def complete(self, messages: list[dict[str, str]]) -> str:
        return self._response


def _is_rate_limit(error: Exception) -> bool:
    status = getattr(error, "status_code", None)
    if status == 429:
        return True
    return "rate limit" in str(error).lower() or "429" in str(error)


def _is_retryable(error: Exception) -> bool:
    status = getattr(error, "status_code", None)
    if status is not None and status >= 500:
        return True
    name = type(error).__name__.lower()
    return "timeout" in name or "connection" in str(error).lower()


def get_llm_client() -> LLMClient:
    """Factory: returns GroqClient for provider 'groq'."""
    provider = settings.llm_provider.lower()
    if provider == "groq":
        return GroqClient()
    raise LLMConfigError(f"Unsupported LLM_PROVIDER: {settings.llm_provider}")
