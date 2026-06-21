"""Runtime environment detection and telemetry event emission.

This module inspects the process environment to determine which editor or
runtime context CrewAI is being used from (Claude Code, OpenAI Codex, Cursor,
or a default/unknown environment) and emits the corresponding event on the
global event bus.

Each process context emits the event at most once per async-context thanks to
the :data:`_env_context_emitted` :class:`contextvars.ContextVar` guard.
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
    """Return True if the process is running inside OpenAI Codex.

    Checks whether any of the well-known Codex environment variables are
    present and non-empty.

    Returns:
        ``True`` when at least one Codex indicator variable is set,
        ``False`` otherwise.
    """
    return any(os.environ.get(var) for var in CODEX_ENV_VARS)


def _is_cursor_env() -> bool:
    """Return True if the process is running inside the Cursor editor.

    Checks whether any of the well-known Cursor environment variables are
    present and non-empty.

    Returns:
        ``True`` when at least one Cursor indicator variable is set,
        ``False`` otherwise.
    """
    return any(os.environ.get(var) for var in CURSOR_ENV_VARS)


def get_env_context() -> None:
    """Detect the current runtime environment and emit the matching event.

    The detection order is:
    1. Claude Code (``CC_ENV_VAR`` is set)
    2. OpenAI Codex (any ``CODEX_ENV_VARS`` variable is set)
    3. Cursor editor (any ``CURSOR_ENV_VARS`` variable is set)
    4. Default / unknown environment

    The event is emitted at most once per async context; subsequent calls
    within the same context are no-ops.
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
