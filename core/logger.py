"""Standard `logging` setup with structured fields.

Structured fields travel in `extra=` (process_name, task, attempt, status,
duration_ms). The console/file formatter prints them as key=value pairs, and
OpenTelemetry's logging auto-instrumentation exports them as log attributes
without any code change: setup_logging() only manages its own handlers and
leaves any handler added by `opentelemetry-instrument` in place.

The process field is called `process_name`, not `process`: `process` is a
reserved LogRecord attribute (the OS process id), so logging refuses it in
`extra=` and OpenTelemetry would drop it anyway.
"""

from __future__ import annotations

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

STRUCTURED_FIELDS = ("process_name", "task", "attempt", "status", "duration_ms", "error_type", "screenshot")
LOG_FORMAT = "%(asctime)s %(levelname)-8s %(name)s - %(message)s"
_RPA_HANDLER_FLAG = "_is_rpa_handler"


class StructuredFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        message = super().format(record)
        fields = " ".join(
            f"{name}={getattr(record, name)}" for name in STRUCTURED_FIELDS if getattr(record, name, None) is not None
        )
        return f"{message} | {fields}" if fields else message


def setup_logging(process_name: str, logs_dir: Path, level: int = logging.INFO) -> Path:
    """Log to the console and to logs/<process>_<YYYYMMDD>.log. Returns the file path."""
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_file = logs_dir / f"{process_name}_{datetime.now():%Y%m%d}.log"

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    for handler in list(root_logger.handlers):
        if getattr(handler, _RPA_HANDLER_FLAG, False):
            root_logger.removeHandler(handler)
            handler.close()

    formatter = StructuredFormatter(LOG_FORMAT)
    for handler in (logging.StreamHandler(sys.stdout), logging.FileHandler(log_file, encoding="utf-8")):
        handler.setFormatter(formatter)
        setattr(handler, _RPA_HANDLER_FLAG, True)
        root_logger.addHandler(handler)
    return log_file


def log_event(
    logger: logging.Logger,
    level: int,
    message: str,
    *,
    process: str,
    status: str,
    task: str | None = None,
    attempt: int | None = None,
    duration_ms: int | None = None,
    **fields: Any,
) -> None:
    """Write one structured log entry. `status` is started|succeeded|failed|retrying."""
    extra = {"process_name": process, "task": task, "attempt": attempt, "status": status, "duration_ms": duration_ms}
    extra.update(fields)
    logger.log(level, message, extra={key: value for key, value in extra.items() if value is not None})
