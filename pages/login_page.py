"""Login screen of the demo site https://the-internet.herokuapp.com/login."""

from __future__ import annotations

from core.base_page import BasePage


class LoginPage(BasePage):
    URL_PATH = "/login"

    # Locators: CSS by default, "xpath=" only when unavoidable. Never absolute XPath.
    TXT_USERNAME = "#username"
    TXT_PASSWORD = "#password"
    BTN_LOGIN = "button[type='submit']"
    LBL_FLASH_MESSAGE = "#flash"
    LBL_FLASH_SUCCESS = "#flash.success"
    LNK_LOGOUT = "xpath=//a[contains(@href, '/logout')]"

    def open_login(self) -> None:
        self._open_path(self.URL_PATH)
        self._wait_for(self.TXT_USERNAME)

    def fill_username(self, username: str) -> None:
        self._fill(self.TXT_USERNAME, username)

    def fill_password(self, password: str) -> None:
        self._fill(self.TXT_PASSWORD, password)

    def click_login(self) -> None:
        self._click(self.BTN_LOGIN)

    def wait_for_flash_message(self) -> None:
        """The site shows a flash message after every login attempt, valid or not."""
        self._wait_for(self.LBL_FLASH_MESSAGE)

    def is_logged_in(self) -> bool:
        return self._is_visible(self.LBL_FLASH_SUCCESS)

    def get_flash_message(self) -> str:
        # The flash box ends with a close icon "×"; return only the message.
        return self._get_text(self.LBL_FLASH_MESSAGE).rstrip("×").strip()

    def click_logout(self) -> None:
        self._click(self.LNK_LOGOUT)
