"""Selenium implementation of the engine contract (Chrome)."""

from __future__ import annotations

import logging
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from selenium import webdriver
from selenium.common.exceptions import (
    StaleElementReferenceException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import Select, WebDriverWait

from core.engines.base_engine import BaseEngine, is_xpath, strip_xpath_prefix
from core.exceptions import SystemException

logger = logging.getLogger(__name__)


class SeleniumEngine(BaseEngine):
    def __init__(self, headless: bool, timeout_seconds: float) -> None:
        super().__init__(headless, timeout_seconds)
        self._driver: WebDriver | None = None

    def open(self) -> None:
        options = webdriver.ChromeOptions()
        if self.headless:
            options.add_argument("--headless=new")
        options.add_argument("--window-size=1920,1080")
        with self._translate_errors("open browser"):
            self._driver = webdriver.Chrome(options=options)
            self._driver.set_page_load_timeout(self.timeout_seconds)

    def goto(self, url: str) -> None:
        with self._translate_errors("goto", url):
            self._require_driver().get(url)

    def click(self, locator: str) -> None:
        with self._translate_errors("click", locator):
            self._wait_until(expected_conditions.element_to_be_clickable(self._to_by(locator))).click()

    def fill(self, locator: str, value: str) -> None:
        with self._translate_errors("fill", locator):
            element = self._wait_until(expected_conditions.visibility_of_element_located(self._to_by(locator)))
            element.clear()
            element.send_keys(value)

    def select(self, locator: str, option_text: str) -> None:
        with self._translate_errors("select", locator):
            element = self._wait_until(expected_conditions.visibility_of_element_located(self._to_by(locator)))
            Select(element).select_by_visible_text(option_text)

    def get_text(self, locator: str) -> str:
        with self._translate_errors("get_text", locator):
            return self._wait_until(expected_conditions.visibility_of_element_located(self._to_by(locator))).text

    def is_visible(self, locator: str) -> bool:
        with self._translate_errors("is_visible", locator):
            elements = self._require_driver().find_elements(*self._to_by(locator))
            try:
                return any(element.is_displayed() for element in elements)
            except StaleElementReferenceException:
                return False

    def wait_for(self, locator: str, state: str = "visible", timeout_seconds: float | None = None) -> None:
        self._validate_state(state)
        by = self._to_by(locator)
        condition = (
            expected_conditions.visibility_of_element_located(by)
            if state == "visible"
            else expected_conditions.invisibility_of_element_located(by)
        )
        with self._translate_errors(f"wait_for {state}", locator, timeout_seconds):
            self._wait_until(condition, timeout_seconds)

    def screenshot(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        with self._translate_errors("screenshot", str(path)):
            self._require_driver().save_screenshot(str(path))
        return path

    def close(self) -> None:
        if self._driver is None:
            return
        try:
            self._driver.quit()
        except WebDriverException as error:
            logger.warning("Could not close the browser cleanly: %s", error.msg)
        finally:
            self._driver = None

    # --- internals -------------------------------------------------------

    @staticmethod
    def _to_by(locator: str) -> tuple[str, str]:
        if is_xpath(locator):
            return By.XPATH, strip_xpath_prefix(locator)
        return By.CSS_SELECTOR, locator

    def _require_driver(self) -> WebDriver:
        if self._driver is None:
            raise SystemException("The browser is not open. Call open() first.")
        return self._driver

    def _wait_until(self, condition, timeout_seconds: float | None = None):
        return WebDriverWait(self._require_driver(), self._resolve_timeout(timeout_seconds)).until(condition)

    @contextmanager
    def _translate_errors(self, action: str, target: str = "", timeout_seconds: float | None = None) -> Iterator[None]:
        try:
            yield
        except TimeoutException as error:
            timeout = self._resolve_timeout(timeout_seconds)
            raise SystemException(f"Timed out after {timeout}s on {action} '{target}'") from error
        except WebDriverException as error:
            raise SystemException(f"{action} failed on '{target}': {error.msg}") from error
