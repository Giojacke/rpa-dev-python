"""Log in to the target site with the configured credentials."""

from __future__ import annotations

from core.base_task import BaseTask
from core.context import ProcessContext
from core.exceptions import BusinessException
from pages.login_page import LoginPage


class LoginTask(BaseTask):
    # Wrong credentials make every later task pointless: stop the process.
    STOP_ON_BUSINESS_ERROR = True

    def execute(self, context: ProcessContext) -> None:
        login_page = LoginPage(self._engine, self._settings.base_url)

        # Always start from the login screen so a retry is safe (idempotent).
        login_page.open_login()
        login_page.fill_username(self._settings.username)
        login_page.fill_password(self._settings.password)
        login_page.click_login()
        login_page.wait_for_flash_message()

        if not login_page.is_logged_in():
            raise BusinessException(f"Login rejected: {login_page.get_flash_message()}")

        context.is_logged_in = True
