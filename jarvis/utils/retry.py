#!/usr/bin/env python3
"""
Retry decorator with exponential backoff for transient API errors.
"""

import asyncio
import functools
import time
from typing import Tuple, Type

from jarvis.utils.logger import JARVISLogger

_logger = JARVISLogger("utils.retry")

# HTTP status codes that are retryable
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


def _is_retryable(exc: Exception, retryable_exceptions: Tuple[Type[Exception], ...]) -> bool:
    """Check if an exception is retryable."""
    if isinstance(exc, retryable_exceptions):
        return True
    # Check for HTTP status codes in common exception types
    status = getattr(exc, "status_code", None) or getattr(exc, "code", None) or getattr(exc, "status", None)
    if status and int(status) in RETRYABLE_STATUS_CODES:
        return True
    # OpenAI API errors
    if "RateLimitError" in type(exc).__name__ or "APIError" in type(exc).__name__:
        return True
    # Connection/timeout errors
    msg = str(exc).lower()
    if any(kw in msg for kw in ("timeout", "connection", "temporarily", "overloaded", "rate limit")):
        return True
    return False


def retry(
    max_attempts: int = 3,
    backoff_base: float = 2.0,
    max_backoff: float = 30.0,
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,),
):
    """
    Decorator that retries an async function on transient failures.

    Args:
        max_attempts: Total attempts (1 initial + retries).
        backoff_base: Base seconds for exponential backoff (2.0 → 2s, 4s, 8s).
        max_backoff: Maximum backoff in seconds.
        retryable_exceptions: Tuple of exception types to retry on.

    Usage:
        @retry(max_attempts=3, backoff_base=2.0)
        async def my_api_call():
            ...
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as exc:
                    last_exc = exc
                    if attempt == max_attempts or not _is_retryable(exc, retryable_exceptions):
                        raise
                    delay = min(backoff_base ** (attempt - 1), max_backoff)
                    _logger.warning(
                        f"Retry {attempt}/{max_attempts} for {func.__name__} "
                        f"after {delay:.1f}s",
                        error=str(exc),
                    )
                    await asyncio.sleep(delay)
            raise last_exc
        return wrapper
    return decorator
