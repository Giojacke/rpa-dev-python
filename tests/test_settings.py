"""Unit tests for config/settings.py."""

from __future__ import annotations

import pytest

from config.settings import load_settings

REQUIRED_ENV = {
    "RPA_PROCESS_NAME": "sample_login",
    "RPA_BASE_URL": "https://example.com",
    "RPA_USERNAME": "user",
    "RPA_PASSWORD": "secret",
}


@pytest.fixture
def clean_env(monkeypatch):
    for name in ("RPA_ENGINE", "RPA_HEADLESS", "RPA_TIMEOUT_SECONDS", "RPA_MAX_RETRIES", *REQUIRED_ENV):
        monkeypatch.delenv(name, raising=False)
    for name, value in REQUIRED_ENV.items():
        monkeypatch.setenv(name, value)
    return monkeypatch


def test_defaults(clean_env, tmp_path):
    settings = load_settings(env_file=tmp_path / "missing.env")

    assert settings.engine == "selenium"
    assert settings.headless is True
    assert settings.max_retries == 3
    assert settings.timeout_seconds == 30
    assert "secret" not in repr(settings)


def test_missing_required_variable_fails_fast(clean_env, tmp_path):
    clean_env.delenv("RPA_PASSWORD")

    with pytest.raises(ValueError, match="RPA_PASSWORD"):
        load_settings(env_file=tmp_path / "missing.env")


def test_unsupported_engine_fails_fast(clean_env, tmp_path):
    clean_env.setenv("RPA_ENGINE", "cypress")

    with pytest.raises(ValueError, match="RPA_ENGINE"):
        load_settings(env_file=tmp_path / "missing.env")
