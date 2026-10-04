"""Playwright (sync API) implementation of the engine contract (Chromium)."""

from __future__ import annotations

import logging
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from playwright.sync_api import Browser, Locator, Page, Playwright, sync_playwright
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from core.engines.base_engine import BaseEngine
from core.exceptions import SystemException

logger = logging.getLogger(__name__)


class PlaywrightEngine(BaseEngine):
    def __init__(self, headless: bool, timeout_seconds: float) -> None:
        super().__init__(headless, timeout_seconds)
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._page: Page | None = None

    def open(self) -> None:
        with self._translate_errors("open browser"):
            self._playwright = sync_playwright().start()
            self._browser = self._playwright.chromium.launch(headless=self.headless)
            self._page = self._browser.new_page(viewport={"width": 1920, "height": 1080})
            self._page.set_default_timeout(self.timeout_seconds * 1000)

    def goto(self, url: str) -> None:
        with self._translate_errors("goto", url):
            self._require_page().goto(url)

    def click(self, locator: str) -> None:
        with self._translate_errors("click", locator):
            self._locate(locator).click()

    def fill(self, locator: str, value: str) -> None:
        with self._translate_errors("fill", locator):
            self._locate(locator).fill(value)

    def select(self, locator: str, option_text: str) -> None:
        with self._translate_errors("select", locator):
            self._locate(locator).select_option(label=option_text)

    def get_text(self, locator: str) -> str:
        with self._translate_errors("get_text", locator):
            element = self._locate(locator)
            element.wait_for(state="visible")
            return element.inner_text()

    def is_visible(self, locator: str) -> bool:
        with self._translate_errors("is_visible", locator):
            return self._locate(locator).is_visible()

    def wait_for(self, locator: str, state: str = "visible", timeout_seconds: float | None = None) -> None:
        self._validate_state(state)
        timeout = self._resolve_timeout(timeout_seconds)
        with self._translate_errors(f"wait_for {state}", locator, timeout_seconds):
            self._locate(locator).wait_for(state=state, timeout=timeout * 1000)

    def screenshot(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        with self._translate_errors("screenshot", str(path)):
            self._require_page().screenshot(path=str(path), full_page=True)
        return path

    def close(self) -> None:
        try:
            if self._browser is not None:
                self._browser.close()
            if self._playwright is not None:
                self._playwright.stop()
        except PlaywrightError as error:
            logger.warning("Could not close the browser cleanly: %s", error.message)
        finally:
            self._page = None
            self._browser = None
            self._playwright = None

    # --- internals -------------------------------------------------------

    def _require_page(self) -> Page:
        if self._page is None:
            raise SystemException("The browser is not open. Call open() first.")
        return self._page

    def _locate(self, locator: str) -> Locator:
        # Playwright understands both plain CSS and the "xpath=" prefix natively.
        # ".first" mirrors Selenium, which always acts on the first match.
        return self._require_page().locator(locator).first

    @contextmanager
    def _translate_errors(self, action: str, target: str = "", timeout_seconds: float | None = None) -> Iterator[None]:
        try:
            yield
        except PlaywrightTimeoutError as error:
            timeout = self._resolve_timeout(timeout_seconds)
            raise SystemException(f"Timed out after {timeout}s on {action} '{target}'") from error
        except PlaywrightError as error:
            raise SystemException(f"{action} failed on '{target}': {error.message}") from error
