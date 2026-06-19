"""Execution context management for CrewAI.

This module provides two complementary abstractions for propagating
request-scoped state across asynchronous boundaries:

1. **Platform integration token** — identifies the external platform (e.g.
   CrewAI Cloud) that launched the current execution.  Stored in a
   :class:`contextvars.ContextVar` so it is automatically scoped to each
   async task.

2. **ExecutionContext snapshot** — a Pydantic model that captures the full
   set of ContextVars active at a given point in time (task ID, flow IDs,
   event tracking, etc.).  Use :func:`capture_execution_context` to snapshot
   and :func:`apply_execution_context` to restore in a different async task
   or thread.

Typical usage::

    ctx = capture_execution_context()

    async def worker() -> None:
        apply_execution_context(ctx)
        # ... worker code that needs the original context ...

    asyncio.create_task(worker())
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
    """Set the platform integration token for the current async context.

    The token is stored in a :class:`contextvars.ContextVar`, so it is
    automatically inherited by child tasks spawned from the current task but
    does not leak into sibling or parent tasks.

    Args:
        integration_token: The integration token issued by the external
            platform (e.g. CrewAI Cloud) for the current execution session.
    """
    _platform_integration_token.set(integration_token)


def get_platform_integration_token() -> str | None:
    """Return the platform integration token for the current async context.

    Falls back to the ``CREWAI_PLATFORM_INTEGRATION_TOKEN`` environment
    variable when no token has been set programmatically, making it easy
    to configure deployments via environment variables without code changes.

    Returns:
        The integration token string, or ``None`` if neither the ContextVar
        nor the environment variable is set.
    """
    token = _platform_integration_token.get()
    if token is None:
        token = os.getenv("CREWAI_PLATFORM_INTEGRATION_TOKEN")
    return token


@contextmanager
def platform_context(integration_token: str) -> Generator[None, Any, None]:
    """Temporarily override the platform integration token within a ``with`` block.

    Restores the previous token value when the block exits, even if an
    exception is raised.  Useful in tests or when a single process handles
    requests on behalf of multiple platforms.

    Args:
        integration_token: The integration token to activate for the duration
            of the ``with`` block.

    Yields:
        ``None`` — this context manager yields control back to the caller
        without producing a value.
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
    """Set the current task ID in the async context.

    Args:
        task_id: The identifier of the task that is currently executing, or
            ``None`` to clear the active task.

    Returns:
        A :class:`contextvars.Token` that can be passed to
        :func:`reset_current_task_id` to restore the previous value.
    """
    return _current_task_id.set(task_id)


def reset_current_task_id(token: contextvars.Token[str | None]) -> None:
    """Restore the task ID to the value it held before the last :func:`set_current_task_id` call.

    Args:
        token: The token returned by the matching :func:`set_current_task_id`
            call.
    """
    _current_task_id.reset(token)


def get_current_task_id() -> str | None:
    """Return the ID of the task that is currently executing.

    Returns:
        The task ID string, or ``None`` if no task is active in the current
        async context.
    """
    return _current_task_id.get()


class ExecutionContext(BaseModel):
    """Immutable snapshot of all ContextVar execution state.

    Capture an instance with :func:`capture_execution_context` at the point
    where the context should be "frozen", then pass it to another async task
    or thread and call :func:`apply_execution_context` to reinstate it.

    Attributes:
        current_task_id: ID of the task active when the snapshot was taken.
        flow_request_id: Unique ID for the current flow invocation.
        flow_id: Persistent ID of the flow definition.
        flow_method_name: Name of the flow method currently executing.
        event_id_stack: Stack of ``(event_id, event_type)`` pairs tracking
            the nesting of emitted events.
        last_event_id: ID of the most recently emitted event.
        triggering_event_id: ID of the event that triggered the current
            handler, if any.
        emission_sequence: Monotonically increasing counter used to order
            events emitted within a single flow invocation.
        feedback_callback_info: Optional metadata for human-in-the-loop
            feedback callbacks.
        platform_token: The platform integration token active at snapshot
            time.
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
    """Snapshot the current ContextVar state into an :class:`ExecutionContext`.

    Call this function in the task or coroutine that *owns* the context before
    handing work off to a background worker.  The returned object is a plain
    Pydantic model with no live references to ContextVars, so it is safe to
    pickle, serialize, or pass across thread boundaries.

    Args:
        feedback_callback_info: Optional metadata to include in the snapshot
            for human-in-the-loop feedback callbacks.  Defaults to ``None``.

    Returns:
        An :class:`ExecutionContext` capturing all currently active
        ContextVar values.
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
    """Restore a previously captured :class:`ExecutionContext` into the current task.

    Writes every field of *ctx* back into the corresponding ContextVar so that
    code running in this async context behaves as if it were part of the
    original execution that produced the snapshot.

    Args:
        ctx: The :class:`ExecutionContext` to reinstate.  Typically produced by
            :func:`capture_execution_context` in the parent task.
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
