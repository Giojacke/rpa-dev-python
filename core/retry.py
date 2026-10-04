"""Generic retry loop.

There is no sleep between attempts: waiting belongs to the engines' explicit
waits, so a retry starts immediately and waits for elements as usual.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


def retry(
    operation: Callable[[int], T],
    *,
    max_attempts: int,
    retry_on: tuple[type[BaseException], ...],
) -> T:
    """Call `operation(attempt)` until it succeeds or attempts run out.

    Exceptions in `retry_on` trigger another attempt; the last one is re-raised.
    Any other exception propagates immediately.
    """
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")
    for attempt in range(1, max_attempts + 1):
        try:
            return operation(attempt)
        except retry_on:
            if attempt == max_attempts:
                raise
    raise AssertionError("unreachable")
