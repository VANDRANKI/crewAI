"""Timeout utilities for CrewAI task and tool execution.

Provides helpers that wrap synchronous and asynchronous callables
with a configurable execution timeout.
"""

from __future__ import annotations

import asyncio
import signal
import functools
from typing import Callable, TypeVar, Optional, Any

T = TypeVar("T")


class TaskTimeoutError(TimeoutError):
    """Raised when a task or tool execution exceeds the configured timeout.

    Attributes:
        timeout_seconds: The timeout value that was exceeded.
        task_name: Optional name of the task for diagnostic messages.
    """

    def __init__(self, timeout_seconds: float, task_name: Optional[str] = None) -> None:
        self.timeout_seconds = timeout_seconds
        self.task_name = task_name
        label = f"'{task_name}'" if task_name else "task"
        super().__init__(
            f"Execution of {label} exceeded timeout of {timeout_seconds}s"
        )


def run_with_timeout(
    func: Callable[..., T],
    *args: Any,
    timeout_seconds: float,
    task_name: Optional[str] = None,
    **kwargs: Any,
) -> T:
    """Execute *func* with a wall-clock timeout on Unix systems.

    Uses ``signal.SIGALRM`` — only available on Unix. For Windows
    compatibility use :func:`async_run_with_timeout` inside an async context.

    Args:
        func: The callable to execute.
        *args: Positional arguments forwarded to *func*.
        timeout_seconds: Maximum allowed execution time in seconds.
        task_name: Optional label used in the timeout error message.
        **kwargs: Keyword arguments forwarded to *func*.

    Returns:
        The return value of *func*.

    Raises:
        TaskTimeoutError: If *func* does not complete within *timeout_seconds*.
        NotImplementedError: On non-Unix platforms (Windows, etc.).
    """
    if not hasattr(signal, "SIGALRM"):
        raise NotImplementedError("run_with_timeout requires Unix (SIGALRM)")

    def _handler(signum: int, frame: Any) -> None:
        raise TaskTimeoutError(timeout_seconds, task_name)

    old_handler = signal.signal(signal.SIGALRM, _handler)
    signal.alarm(int(timeout_seconds) + 1)
    try:
        return func(*args, **kwargs)
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


async def async_run_with_timeout(
    coro: "asyncio.Coroutine[Any, Any, T]",
    timeout_seconds: float,
    task_name: Optional[str] = None,
) -> T:
    """Await *coro* with an asyncio timeout.

    Args:
        coro: Awaitable coroutine to execute.
        timeout_seconds: Maximum allowed execution time in seconds.
        task_name: Optional label used in the timeout error message.

    Returns:
        The result of *coro*.

    Raises:
        TaskTimeoutError: If *coro* does not complete within *timeout_seconds*.
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout_seconds)
    except asyncio.TimeoutError:
        raise TaskTimeoutError(timeout_seconds, task_name)
