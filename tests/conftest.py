"""Shared fixtures.

- `settings`: demo-site settings that write logs/evidence to a temp folder.
- `engine`: real headless browser, parametrized over both engines. A test that
  uses it runs once per engine and is skipped if that library is missing.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from config.settings import Settings
from core.engines.engine_factory import SUPPORTED_ENGINES, create_engine

DEMO_BASE_URL = "https://the-internet.herokuapp.com"
DEMO_USERNAME = "tomsmith"
DEMO_PASSWORD = "SuperSecretPassword!"


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        process_name="sample_login_test",
        engine="selenium",
        headless=True,
        base_url=os.environ.get("RPA_BASE_URL", DEMO_BASE_URL),
        timeout_seconds=20,
        max_retries=3,
        username=DEMO_USERNAME,
        password=DEMO_PASSWORD,
        logs_dir=tmp_path / "logs",
        evidence_dir=tmp_path / "evidence",
        input_dir=tmp_path / "input",
        output_dir=tmp_path / "output",
    )


@pytest.fixture(params=SUPPORTED_ENGINES)
def engine(request: pytest.FixtureRequest, settings: Settings):
    engine_name = request.param
    pytest.importorskip(engine_name, reason=f"{engine_name} is not installed")
    browser_engine = create_engine(engine_name, headless=True, timeout_seconds=settings.timeout_seconds)
    browser_engine.open()
    try:
        yield browser_engine
    finally:
        browser_engine.close()
