"""Unit tests for the retry/evidence policy. No browser needed."""

from __future__ import annotations

import logging
from pathlib import Path

import pytest

from core.base_task import BaseTask
from core.context import ProcessContext
from core.engines.base_engine import BaseEngine
from core.exceptions import BusinessException, SystemException


class FakeEngine(BaseEngine):
    def __init__(self) -> None:
        super().__init__(headless=True, timeout_seconds=1)

    def open(self) -> None: ...
    def goto(self, url: str) -> None: ...
    def click(self, locator: str) -> None: ...
    def fill(self, locator: str, value: str) -> None: ...
    def select(self, locator: str, option_text: str) -> None: ...
    def get_text(self, locator: str) -> str:
        return ""
    def is_visible(self, locator: str) -> bool:
        return True
    def wait_for(self, locator: str, state: str = "visible", timeout_seconds: float | None = None) -> None: ...
    def close(self) -> None: ...

    def screenshot(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"fake")
        return path


class FailingTask(BaseTask):
    """Raises `error` on the first `failures` attempts, then succeeds."""

    def __init__(self, engine, settings, error: Exception, failures: int) -> None:
        super().__init__(engine, settings)
        self.error = error
        self.failures = failures
        self.attempts = 0

    def execute(self, context: ProcessContext) -> None:
        self.attempts += 1
        if self.attempts <= self.failures:
            raise self.error


class SkippableTask(FailingTask):
    STOP_ON_BUSINESS_ERROR = False


def screenshots(settings, task_name: str) -> list[Path]:
    return sorted(settings.evidence_dir.glob(f"{task_name}_attempt*.png"))


@pytest.fixture
def context(settings) -> ProcessContext:
    return ProcessContext(process_name=settings.process_name)


def test_system_exception_is_retried_until_success(settings, context):
    task = FailingTask(FakeEngine(), settings, SystemException("timeout"), failures=2)

    result = task.run(context)

    assert task.attempts == 3
    assert result.completed_tasks == ["failing_task"]
    assert len(screenshots(settings, "failing_task")) == 2


def test_system_exception_fails_after_max_retries(settings, context):
    task = FailingTask(FakeEngine(), settings, SystemException("site down"), failures=99)

    with pytest.raises(SystemException):
        task.run(context)

    assert task.attempts == settings.max_retries
    assert len(screenshots(settings, "failing_task")) == settings.max_retries


def test_business_exception_is_not_retried(settings, context):
    task = FailingTask(FakeEngine(), settings, BusinessException("record not found"), failures=99)

    with pytest.raises(BusinessException):
        task.run(context)

    assert task.attempts == 1
    assert len(screenshots(settings, "failing_task")) == 1


def test_business_exception_skips_task_when_configured(settings, context):
    task = SkippableTask(FakeEngine(), settings, BusinessException("invalid row"), failures=99)

    result = task.run(context)

    assert task.attempts == 1
    assert result.skipped_tasks == ["skippable_task"]
    assert result.completed_tasks == []


def test_unexpected_error_is_wrapped_and_retried(settings, context):
    task = FailingTask(FakeEngine(), settings, KeyError("missing"), failures=1)

    task.run(context)

    assert task.attempts == 2


def test_failed_attempts_are_logged_with_structured_fields(settings, context, caplog):
    caplog.set_level(logging.INFO)
    task = FailingTask(FakeEngine(), settings, SystemException("timeout"), failures=1)

    task.run(context)

    statuses = [(record.attempt, record.status) for record in caplog.records if hasattr(record, "status")]
    assert statuses == [(1, "started"), (1, "retrying"), (2, "started"), (2, "succeeded")]
    failed_record = next(record for record in caplog.records if getattr(record, "status", None) == "retrying")
    assert failed_record.process_name == settings.process_name
    assert failed_record.task == "failing_task"
    assert failed_record.duration_ms >= 0
