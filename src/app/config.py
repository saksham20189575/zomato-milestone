import os
import re
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
    cors_allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

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

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_allowed_origins.split(",") if o.strip()]

    @property
    def cors_exact_origins(self) -> list[str]:
        """Origins without ``*`` — passed to CORSMiddleware allow_origins."""
        return [o for o in self.cors_origin_list if "*" not in o]

    @property
    def cors_origin_regex(self) -> str | None:
        """
        Combined regex for wildcard patterns (e.g. ``https://*.vercel.app``).
        Used as CORSMiddleware allow_origin_regex on Railway + Vercel deploys.
        """
        patterns = [o for o in self.cors_origin_list if "*" in o]
        if not patterns:
            return None
        parts = [_wildcard_origin_to_regex(p) for p in patterns]
        return "|".join(f"(?:{part})" for part in parts)


def _wildcard_origin_to_regex(pattern: str) -> str:
    """Turn ``https://app-*.vercel.app`` into a safe origin regex."""
    chunks = pattern.split("*")
    out: list[str] = []
    for index, chunk in enumerate(chunks):
        out.append(re.escape(chunk))
        if index < len(chunks) - 1:
            out.append(".*")
    return "".join(out)


settings = Settings()
settings.validate_budget_thresholds()
