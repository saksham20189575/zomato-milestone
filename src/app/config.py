import os
from pathlib import Path
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _secret_value(name: str) -> str:
    """Read a flat secret from Streamlit when running under `streamlit run`."""
    try:
        import streamlit as st

        if name not in st.secrets:
            return ""
        return str(st.secrets[name] or "")
    except Exception:
        return ""


def _hydrate_env_from_streamlit_secrets() -> None:
    """Map Streamlit secrets to env vars for pydantic-settings (Cloud + local secrets.toml)."""
    try:
        import streamlit as st
    except ImportError:
        return

    try:
        items = dict(st.secrets)
    except Exception:
        return

    def _walk(prefix: str, node: Any) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                segment = f"{prefix}_{key}" if prefix else str(key)
                _walk(segment, value)
            return
        env_key = prefix.upper()
        if env_key and env_key not in os.environ:
            os.environ[env_key] = str(node)

    for key, value in items.items():
        _walk(str(key), value)


_hydrate_env_from_streamlit_secrets()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    data_path: Path = PROJECT_ROOT / "data/processed/restaurants.parquet"
    budget_low_max: float = 500.0
    budget_medium_max: float = 1500.0
    max_candidates: int = 30

    llm_provider: str = "groq"
    llm_api_key: str = ""
    llm_model: str = "llama-3.3-70b-versatile"
    llm_temperature: float = 0.3
    llm_max_retries: int = 1
    additional_preferences_max_length: int = 2000

    @field_validator("data_path", mode="after")
    @classmethod
    def resolve_data_path(cls, value: Path) -> Path:
        if value.is_absolute():
            return value.resolve()
        return (PROJECT_ROOT / value).resolve()

    def validate_budget_thresholds(self) -> None:
        if self.budget_low_max <= 0:
            raise ValueError("BUDGET_LOW_MAX must be positive")
        if self.budget_medium_max <= self.budget_low_max:
            raise ValueError("BUDGET_MEDIUM_MAX must be greater than BUDGET_LOW_MAX")

    @property
    def resolved_llm_api_key(self) -> str:
        return (
            self.llm_api_key
            or os.getenv("GROQ_API_KEY", "")
            or os.getenv("LLM_API_KEY", "")
            or _secret_value("GROQ_API_KEY")
            or _secret_value("LLM_API_KEY")
        )

    @property
    def has_llm_api_key(self) -> bool:
        return bool(self.resolved_llm_api_key.strip())


settings = Settings()
settings.validate_budget_thresholds()
