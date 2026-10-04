"""End-to-end: run LoginTask against the public demo site, once per engine."""

from __future__ import annotations

from dataclasses import replace

import pytest

from core.context import ProcessContext
from core.exceptions import BusinessException
from tasks.login_task import LoginTask


@pytest.mark.e2e
def test_login_task_logs_in_with_valid_credentials(engine, settings):
    context = ProcessContext(process_name=settings.process_name)

    context = LoginTask(engine, settings).run(context)

    assert context.is_logged_in
    assert context.completed_tasks == ["login_task"]


@pytest.mark.e2e
def test_login_task_raises_business_exception_with_invalid_password(engine, settings):
    invalid_settings = replace(settings, password="wrong-password")
    context = ProcessContext(process_name=settings.process_name)

    with pytest.raises(BusinessException, match="password is invalid"):
        LoginTask(engine, invalid_settings).run(context)

    # Business errors are not retried: exactly one attempt, one screenshot.
    assert len(list(settings.evidence_dir.glob("login_task_attempt1_*.png"))) == 1
    assert not list(settings.evidence_dir.glob("login_task_attempt2_*.png"))
