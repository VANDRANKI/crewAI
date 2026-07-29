"""Environment detection utilities.

Detects the coding-agent environment (e.g. Claude Code, Codex, Cursor) that
crewAI is running in and emits a corresponding event, once per context, for
telemetry purposes.
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
    """Return True if any Codex-specific environment variable is set."""
    return any(os.environ.get(var) for var in CODEX_ENV_VARS)


def _is_cursor_env() -> bool:
    """Return True if any Cursor-specific environment variable is set."""
    return any(os.environ.get(var) for var in CURSOR_ENV_VARS)


def get_env_context() -> None:
    """Emit an environment-detection event once per context.

    Inspects environment variables to determine whether crewAI is running
    under Claude Code, Codex, or Cursor, and emits the matching event on the
    crewai_event_bus. Falls back to DefaultEnvEvent if none match. Subsequent
    calls within the same context are no-ops.
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
