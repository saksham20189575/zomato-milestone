"""Tests for deployment-related configuration."""

from pathlib import Path

from app.config import PROJECT_ROOT, Settings


def test_data_path_resolves_relative_to_project_root(monkeypatch, tmp_path):
    monkeypatch.delenv("DATA_PATH", raising=False)
    relative = Path("data/processed/restaurants.parquet")
    settings = Settings(data_path=relative)
    assert settings.data_path == (PROJECT_ROOT / relative).resolve()


def test_resolved_llm_api_key_prefers_settings_field(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "from-env")
    settings = Settings(llm_api_key="from-settings")
    assert settings.resolved_llm_api_key == "from-settings"


def test_has_llm_api_key_false_when_unset(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    settings = Settings(llm_api_key="")
    assert settings.has_llm_api_key is False
