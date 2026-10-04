"""Abstract browser contract shared by every engine.

Locators are plain strings:
- CSS by default:            "#username", "button[type='submit']"
- XPath only when unavoidable, with the "xpath=" prefix:
                             "xpath=//a[contains(@href, '/logout')]"
Each engine translates the locator to its own API, so pages never depend on
Selenium or Playwright types.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

XPATH_PREFIX = "xpath="
WAIT_STATES = ("visible", "hidden")


def is_xpath(locator: str) -> bool:
    return locator.startswith(XPATH_PREFIX)


def strip_xpath_prefix(locator: str) -> str:
    return locator[len(XPATH_PREFIX):] if is_xpath(locator) else locator


class BaseEngine(ABC):
    """Every method that interacts with an element waits explicitly for it.

    Engines raise SystemException on any technical failure, never a
    library-specific exception.
    """

    def __init__(self, headless: bool, timeout_seconds: float) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be greater than 0")
        self.headless = headless
        self.timeout_seconds = timeout_seconds

    @abstractmethod
    def open(self) -> None:
        """Start the browser."""

    @abstractmethod
    def goto(self, url: str) -> None:
        """Navigate to an absolute URL."""

    @abstractmethod
    def click(self, locator: str) -> None:
        """Wait until the element is clickable and click it."""

    @abstractmethod
    def fill(self, locator: str, value: str) -> None:
        """Wait until the input is visible, clear it and type the value."""

    @abstractmethod
    def select(self, locator: str, option_text: str) -> None:
        """Select a dropdown option by its visible text."""

    @abstractmethod
    def get_text(self, locator: str) -> str:
        """Wait until the element is visible and return its text."""

    @abstractmethod
    def is_visible(self, locator: str) -> bool:
        """Return whether the element is visible right now. Never waits."""

    @abstractmethod
    def wait_for(self, locator: str, state: str = "visible", timeout_seconds: float | None = None) -> None:
        """Wait until the element reaches the state ("visible" or "hidden")."""

    @abstractmethod
    def screenshot(self, path: Path) -> Path:
        """Save a screenshot of the current page and return its path."""

    @abstractmethod
    def close(self) -> None:
        """Close the browser. Safe to call more than once."""

    def _resolve_timeout(self, timeout_seconds: float | None) -> float:
        return self.timeout_seconds if timeout_seconds is None else timeout_seconds

    @staticmethod
    def _validate_state(state: str) -> None:
        if state not in WAIT_STATES:
            raise ValueError(f"Unsupported wait state '{state}'. Use one of: {', '.join(WAIT_STATES)}")

    def __enter__(self) -> BaseEngine:
        self.open()
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()
