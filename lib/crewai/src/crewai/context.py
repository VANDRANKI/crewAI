"""Execution context management for CrewAI.

This module provides two complementary context abstractions:

1. **Platform integration token** (`_platform_integration_token`): A
   :class:`contextvars.ContextVar` that carries the CREWAI platform auth token
   for the duration of a request.  Use :func:`set_platform_integration_token`
   for a one-shot assignment, or the :func:`platform_context` context manager
   when you need to restore the previous value on exit (e.g. in concurrent
   async code).

2. **ExecutionContext snapshot** (:class:`ExecutionContext` +
   :func:`capture_execution_context` / :func:`apply_execution_context`): A
   Pydantic model that serialises all relevant :mod:`contextvars` values into a
   plain object.  Use this to propagate context across thread boundaries or
   :class:`asyncio.Task` boundaries where context is not inherited
   automatically.

Typical async-task usage::

    import asyncio
    from crewai.context import capture_execution_context, apply_execution_context

    ctx = capture_execution_context()

    async def worker() -> None:
        apply_execution_context(ctx)  # restore context inside the new task
        ...

    asyncio.create_task(worker())

Raises:
    RuntimeError: If :func:`apply_execution_context` is called with an
        :class:`ExecutionContext` whose ``flow_method_name`` is an empty string
        and the downstream code requires a non-empty value.  Callers should
        validate the snapshot before applying it.
"""

from collections.abc import Generator
from contextlib import contextmanager
import contextvars
import os
from typing import Any

from pydantic import BaseModel, Field

from crewai.events.base_events import (
    get_emission_sequence,
    set_emission_counter,
)
from crewai.events.event_context import (
    _event_id_stack,
    _last_event_id,
    _triggering_event_id,
)
from crewai.flow.flow_context import (
    current_flow_id,
    current_flow_method_name,
    current_flow_request_id,
)


_platform_integration_token: contextvars.ContextVar[str | None] = (
    contextvars.ContextVar("platform_integration_token", default=None)
)


def set_platform_integration_token(integration_token: str) -> None:
    """Set the platform integration token in the current context.

    This is a fire-and-forget assignment.  If you need to restore the
    previous value after a block of code (e.g. in concurrent async code),
    use :func:`platform_context` instead.

    Args:
        integration_token: The integration token to set.  Must be a non-empty
            string; passing an empty string will overwrite any existing token
            with an invalid value.
    """
    _platform_integration_token.set(integration_token)


def get_platform_integration_token() -> str | None:
    """Get the platform integration token from the current context or environment.

    Resolution order:

    1. The value set via :func:`set_platform_integration_token` or
       :func:`platform_context` for the current context.
    2. The ``CREWAI_PLATFORM_INTEGRATION_TOKEN`` environment variable.
    3. ``None`` if neither source has a value.

    Returns:
        The integration token string if one is available, otherwise ``None``.
    """
    token = _platform_integration_token.get()
    if token is None:
        token = os.getenv("CREWAI_PLATFORM_INTEGRATION_TOKEN")
    return token


@contextmanager
def platform_context(integration_token: str) -> Generator[None, Any, None]:
    """Context manager to temporarily set the platform integration token.

    On exit (both normal and exceptional) the previous token value is
    restored via :meth:`contextvars.ContextVar.reset`, making this safe to
    nest and to use inside concurrent :class:`asyncio.Task` code.

    Args:
        integration_token: The integration token to use within this context
            block.  Must be a non-empty string.

    Yields:
        ``None`` — the body of the ``with`` block runs between entry and exit.

    Example::

        with platform_context("tok_abc123"):
            result = call_platform_api()  # sees "tok_abc123"
        # original token restored here
    """
    token = _platform_integration_token.set(integration_token)
    try:
        yield
    finally:
        _platform_integration_token.reset(token)


_current_task_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "current_task_id", default=None
)


def set_current_task_id(task_id: str | None) -> contextvars.Token[str | None]:
    """Set the current task ID in the context.

    Args:
        task_id: The task identifier to store, or ``None`` to clear it.
            Use the returned token to restore the previous value via
            :func:`reset_current_task_id`.

    Returns:
        A :class:`contextvars.Token` that captures the previous value.  Pass
        this token to :func:`reset_current_task_id` to undo the assignment.
    """
    return _current_task_id.set(task_id)


def reset_current_task_id(token: contextvars.Token[str | None]) -> None:
    """Reset the current task ID to its previous value.

    Args:
        token: The token returned by :func:`set_current_task_id`.  Using a
            token that belongs to a different :class:`contextvars.ContextVar`
            raises :class:`ValueError`.

    Raises:
        ValueError: If ``token`` was created by a different
            :class:`contextvars.ContextVar` than ``_current_task_id``.
    """
    _current_task_id.reset(token)


def get_current_task_id() -> str | None:
    """Get the current task ID from the context.

    Returns:
        The task ID string for the currently executing task, or ``None`` if
        no task is active in this context.
    """
    return _current_task_id.get()


class ExecutionContext(BaseModel):
    """Immutable snapshot of all ContextVar execution state.

    Instances are produced by :func:`capture_execution_context` and consumed
    by :func:`apply_execution_context`.  The model is serialisable via
    :meth:`model_dump` / :meth:`model_dump_json`, which makes it suitable for
    passing across thread or process boundaries.

    Attributes:
        current_task_id: Identifier of the task currently being executed, or
            ``None`` if no task is active.
        flow_request_id: Unique identifier for the current Flow request, or
            ``None`` outside of a Flow execution.
        flow_id: Identifier of the active Flow instance, or ``None`` outside
            of a Flow execution.
        flow_method_name: Name of the Flow method currently executing.
            Defaults to ``"unknown"`` when called outside a Flow.
        event_id_stack: Ordered stack of ``(event_id, event_type)`` pairs
            representing the chain of events that led to the current execution
            point.  Stored as a tuple of tuples for hashability.
        last_event_id: ID of the most recently emitted event, or ``None`` if
            no events have been emitted.
        triggering_event_id: ID of the event that triggered the current
            execution, or ``None`` at the top level.
        emission_sequence: Monotonically increasing counter tracking the
            emission order of events within a single Flow execution.
        feedback_callback_info: Arbitrary metadata passed by the caller to
            associate a feedback callback with this context snapshot.  ``None``
            if no callback info was provided.
        platform_token: The platform integration token active at snapshot
            time, or ``None`` if none was set.
    """

    current_task_id: str | None = Field(default=None)
    flow_request_id: str | None = Field(default=None)
    flow_id: str | None = Field(default=None)
    flow_method_name: str = Field(default="unknown")

    event_id_stack: tuple[tuple[str, str], ...] = Field(default_factory=tuple)
    last_event_id: str | None = Field(default=None)
    triggering_event_id: str | None = Field(default=None)
    emission_sequence: int = Field(default=0)

    feedback_callback_info: dict[str, Any] | None = Field(default=None)
    platform_token: str | None = Field(default=None)


def capture_execution_context(
    feedback_callback_info: dict[str, Any] | None = None,
) -> ExecutionContext:
    """Read the current ContextVar values into an :class:`ExecutionContext`.

    This function is safe to call from any thread or coroutine — each
    execution context inherits its own copy of all ContextVars.  The
    resulting snapshot can be serialised and applied in a different thread
    or task via :func:`apply_execution_context`.

    Args:
        feedback_callback_info: Optional dictionary of metadata to embed in
            the snapshot so that the recipient can locate a feedback callback
            (e.g. ``{"callback_id": "cb_42"}``).  Defaults to ``None``.

    Returns:
        An :class:`ExecutionContext` reflecting all ContextVar values at the
        moment of the call.
    """
    return ExecutionContext(
        current_task_id=_current_task_id.get(),
        flow_request_id=current_flow_request_id.get(),
        flow_id=current_flow_id.get(),
        flow_method_name=current_flow_method_name.get(),
        event_id_stack=_event_id_stack.get(),
        last_event_id=_last_event_id.get(),
        triggering_event_id=_triggering_event_id.get(),
        emission_sequence=get_emission_sequence(),
        feedback_callback_info=feedback_callback_info,
        platform_token=_platform_integration_token.get(),
    )


def apply_execution_context(ctx: ExecutionContext) -> None:
    """Write an :class:`ExecutionContext` snapshot back into the ContextVars.

    Call this at the start of a worker thread or :class:`asyncio.Task` to
    restore the execution context captured by :func:`capture_execution_context`
    in the parent.

    .. warning::
        This function mutates the calling context's ContextVar state.  In
        async code, each :class:`asyncio.Task` has its own context copy, so
        calling this inside a task will not affect the event loop or sibling
        tasks.  In threaded code, ContextVars are per-thread, so this is
        similarly isolated.

    Args:
        ctx: The :class:`ExecutionContext` snapshot to restore.  All fields
            are written unconditionally, overwriting any values that were
            previously set in the current context.
    """
    _current_task_id.set(ctx.current_task_id)
    current_flow_request_id.set(ctx.flow_request_id)
    current_flow_id.set(ctx.flow_id)
    current_flow_method_name.set(ctx.flow_method_name)

    _event_id_stack.set(ctx.event_id_stack)
    _last_event_id.set(ctx.last_event_id)
    _triggering_event_id.set(ctx.triggering_event_id)
    set_emission_counter(ctx.emission_sequence)

    _platform_integration_token.set(ctx.platform_token)
