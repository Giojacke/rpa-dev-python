"""Base class for pages and components.

Pages and components reach the browser only through these protected helpers.
Their public methods are business-readable actions (fill_username, click_login)
and queries (is_logged_in, get_flash_message). They return data and never
decide what the process does next.
"""

from __future__ import annotations

from core.engines.base_engine import BaseEngine


class BasePage:
    def __init__(self, engine: BaseEngine, base_url: str) -> None:
        self._engine = engine
        self._base_url = base_url.rstrip("/")

    def _open_path(self, path: str) -> None:
        self._engine.goto(f"{self._base_url}{path}")

    def _click(self, locator: str) -> None:
        self._engine.click(locator)

    def _fill(self, locator: str, value: str) -> None:
        self._engine.fill(locator, value)

    def _select(self, locator: str, option_text: str) -> None:
        self._engine.select(locator, option_text)

    def _get_text(self, locator: str) -> str:
        return self._engine.get_text(locator).strip()

    def _is_visible(self, locator: str) -> bool:
        return self._engine.is_visible(locator)

    def _wait_for(self, locator: str, state: str = "visible", timeout_seconds: float | None = None) -> None:
        self._engine.wait_for(locator, state, timeout_seconds)
