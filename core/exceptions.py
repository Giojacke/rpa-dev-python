"""Exception hierarchy that drives the retry policy.

- SystemException: technical failure (timeout, element not found, site down).
  The task is retried up to RPA_MAX_RETRIES.
- BusinessException: the data or a business rule is wrong (invalid credentials,
  record not found). Retrying will not help, so the task is never retried.
"""


class RpaException(Exception):
    """Base class for every exception raised on purpose by the bot."""


class BusinessException(RpaException):
    """A business rule failed. Never retried."""


class SystemException(RpaException):
    """A technical failure. Retried up to RPA_MAX_RETRIES."""
