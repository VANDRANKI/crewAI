"""Utilities for detecting the coding-agent environment CrewAI runs in.

Emits a one-time telemetry event identifying whether CrewAI is running under
Claude Code, Codex, Cursor, or a default (unrecognized) environment.
"""

import contextvars
import os

from crewai.events.event_bus import crewai_event_bus
from crewai.events.types.env_events import (
    CCEnvEvent,
    CodexEnvEvent,
    CursorEnvEvent,
    DefaultEnvEvent,
)
from crewai.utilities.constants import CC_ENV_VAR, CODEX_ENV_VARS, CURSOR_ENV_VARS


_env_context_emitted: contextvars.ContextVar[bool] = contextvars.ContextVar(
    "_env_context_emitted", default=False
)


def _is_codex_env() -> bool:
    """Returns True if any Codex-specific environment variable is set."""
    return any(os.environ.get(var) for var in CODEX_ENV_VARS)


def _is_cursor_env() -> bool:
    """Returns True if any Cursor-specific environment variable is set."""
    return any(os.environ.get(var) for var in CURSOR_ENV_VARS)


def get_env_context() -> None:
    """Emit a single telemetry event identifying the current coding-agent environment.

    Checks, in order, for Claude Code, Codex, and Cursor environment
    variables, falling back to a default event when none match. The event
    is only emitted once per context (tracked via `_env_context_emitted`).
    """
    if _env_context_emitted.get():
        return
    _env_context_emitted.set(True)

    if os.environ.get(CC_ENV_VAR):
        crewai_event_bus.emit(None, CCEnvEvent())
    elif _is_codex_env():
        crewai_event_bus.emit(None, CodexEnvEvent())
    elif _is_cursor_env():
        crewai_event_bus.emit(None, CursorEnvEvent())
    else:
        crewai_event_bus.emit(None, DefaultEnvEvent())
