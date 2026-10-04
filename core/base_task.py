"""Base class for every task (step) of the process.

The only public method is `run(context) -> context`. It wraps the task's
`execute(context)` with the standard policy:

- SystemException (or any unexpected error) -> retried up to RPA_MAX_RETRIES.
- BusinessException -> never retried. The task stops the process, or is
  skipped when STOP_ON_BUSINESS_ERROR = False.
- Every failed attempt -> screenshot in evidence/ + structured log entry.
- Every attempt is timed and logged as started / succeeded / failed / retrying.

Concrete tasks implement `execute()` only, and it must be idempotent: a retry
calls it again from the start in the same browser.
"""

from __future__ import annotations

import logging
import re
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from time import perf_counter
from typing import TYPE_CHECKING

from core.context import ProcessContext
from core.engines.base_engine import BaseEngine
from core.exceptions import BusinessException, SystemException
from core.logger import log_event
from core.retry import retry

if TYPE_CHECKING:
    from config.settings import Settings

logger = logging.getLogger(__name__)


def to_snake_case(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


class BaseTask(ABC):
    STOP_ON_BUSINESS_ERROR: bool = True

    def __init__(self, engine: BaseEngine, settings: Settings) -> None:
        self._engine = engine
        self._settings = settings

    @property
    def name(self) -> str:
        return to_snake_case(type(self).__name__)

    def run(self, context: ProcessContext) -> ProcessContext:
        try:
            retry(
                lambda attempt: self._run_attempt(context, attempt),
                max_attempts=self._settings.max_retries,
                retry_on=(SystemException,),
            )
        except BusinessException:
            if self.STOP_ON_BUSINESS_ERROR:
                raise
            context.skipped_tasks.append(self.name)
            self._log(logging.WARNING, "Task skipped after business error", status="failed")
            return context
        context.completed_tasks.append(self.name)
        return context

    @abstractmethod
    def execute(self, context: ProcessContext) -> None:
        """Do the work of the task. Read and write data through `context`."""

    # --- internals -------------------------------------------------------

    def _run_attempt(self, context: ProcessContext, attempt: int) -> None:
        started = perf_counter()
        self._log(logging.INFO, "Task attempt started", status="started", attempt=attempt)
        try:
            self.execute(context)
        except BusinessException as error:
            self._record_failure(error, attempt, "failed", started)
            raise
        except SystemException as error:
            self._record_failure(error, attempt, self._failure_status(attempt), started)
            raise
        except Exception as error:
            # Unknown errors are treated as technical failures (retryable).
            wrapped = SystemException(f"Unexpected error: {error}")
            self._record_failure(wrapped, attempt, self._failure_status(attempt), started, error_type=type(error).__name__)
            raise wrapped from error
        self._log(logging.INFO, "Task attempt succeeded", status="succeeded", attempt=attempt, started=started)

    def _failure_status(self, attempt: int) -> str:
        return "retrying" if attempt < self._settings.max_retries else "failed"

    def _record_failure(
        self,
        error: Exception,
        attempt: int,
        status: str,
        started: float,
        error_type: str | None = None,
    ) -> None:
        screenshot = self._take_screenshot(attempt)
        self._log(
            logging.ERROR,
            f"Task attempt failed: {error}",
            status=status,
            attempt=attempt,
            started=started,
            error_type=error_type or type(error).__name__,
            screenshot=str(screenshot) if screenshot else None,
        )

    def _take_screenshot(self, attempt: int) -> Path | None:
        path = self._settings.evidence_dir / f"{self.name}_attempt{attempt}_{datetime.now():%Y%m%d_%H%M%S}.png"
        try:
            return self._engine.screenshot(path)
        except Exception as error:  # Never hide the original failure.
            logger.warning("Could not take screenshot %s: %s", path, error)
            return None

    def _log(self, level: int, message: str, *, status: str, started: float | None = None, **fields) -> None:
        duration_ms = round((perf_counter() - started) * 1000) if started is not None else None
        log_event(
            logger,
            level,
            message,
            process=self._settings.process_name,
            task=self.name,
            status=status,
            duration_ms=duration_ms,
            **fields,
        )
