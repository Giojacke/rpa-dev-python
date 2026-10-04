"""Shared state passed from task to task.

Tasks communicate only through this object. Add one typed field per piece of
data a later task needs (for example `invoice_files: list[Path]`); do not use
globals or untyped dictionaries.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ProcessContext:
    process_name: str
    started_at: datetime = field(default_factory=datetime.now)
    completed_tasks: list[str] = field(default_factory=list)
    skipped_tasks: list[str] = field(default_factory=list)

    # --- business data shared between tasks --------------------------------
    is_logged_in: bool = False
