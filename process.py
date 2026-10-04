"""The end-to-end business process: the ordered list of tasks.

The order of PROCESS_TASKS is the order of execution. To add a step, create
the task in tasks/ and add its class here. File names are never numbered.
"""

from __future__ import annotations

import logging
from time import perf_counter

from config.settings import Settings
from core.base_task import BaseTask
from core.context import ProcessContext
from core.engines.base_engine import BaseEngine
from core.logger import log_event
from tasks.login_task import LoginTask

logger = logging.getLogger(__name__)

PROCESS_TASKS: list[type[BaseTask]] = [
    LoginTask,
]


class Process:
    def __init__(self, engine: BaseEngine, settings: Settings) -> None:
        self._engine = engine
        self._settings = settings

    def run(self) -> ProcessContext:
        context = ProcessContext(process_name=self._settings.process_name)
        started = perf_counter()
        self._log(logging.INFO, "Process started", "started")
        try:
            for task_class in PROCESS_TASKS:
                context = task_class(self._engine, self._settings).run(context)
        except Exception as error:
            self._log(logging.ERROR, f"Process failed: {error}", "failed", started)
            raise
        self._log(logging.INFO, "Process succeeded", "succeeded", started)
        return context

    def _log(self, level: int, message: str, status: str, started: float | None = None) -> None:
        duration_ms = round((perf_counter() - started) * 1000) if started is not None else None
        log_event(logger, level, message, process=self._settings.process_name, status=status, duration_ms=duration_ms)
