"""Build the browser engine selected by RPA_ENGINE."""

from __future__ import annotations

from core.engines.base_engine import BaseEngine

SUPPORTED_ENGINES = ("selenium", "playwright")


def create_engine(engine_name: str, *, headless: bool, timeout_seconds: float) -> BaseEngine:
    """Return a closed engine; the caller opens it and closes it in a finally block.

    Imports are lazy so a bot that only uses one engine does not need the
    other library installed.
    """
    if engine_name == "selenium":
        from core.engines.selenium_engine import SeleniumEngine

        return SeleniumEngine(headless=headless, timeout_seconds=timeout_seconds)
    if engine_name == "playwright":
        from core.engines.playwright_engine import PlaywrightEngine

        return PlaywrightEngine(headless=headless, timeout_seconds=timeout_seconds)
    raise ValueError(f"Unsupported engine '{engine_name}'. Use one of: {', '.join(SUPPORTED_ENGINES)}")
