"""Output model for :class:`~crewai.LiteAgent` execution results.

This module defines :class:`LiteAgentOutput`, the structured return value
produced by :meth:`~crewai.LiteAgent.run` and its async counterpart.  It
captures both the final answer text and any intermediate tool calls made
during the agent loop so callers can inspect the full reasoning trace.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class LiteAgentOutput(BaseModel):
    """Structured result returned by a :class:`~crewai.LiteAgent` run.

    Attributes:
        output: The final text answer produced by the agent after all tool
            calls have completed.  This is the value most callers care about.
        tool_calls: A list of tool-call records made during the agent loop.
            Each record is a dict with at least ``"name"`` and ``"output"``
            keys; the exact schema depends on the tools registered with the
            agent.  An empty list means the agent answered directly without
            invoking any tools.
        raw: The full raw response object from the underlying LLM call, useful
            for debugging or accessing provider-specific metadata.  The type
            depends on the LLM provider and may be ``None`` if not captured.
    """

    output: str = Field(description="The final text answer produced by the agent.")
    tool_calls: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Intermediate tool calls made during the agent loop.",
    )
    raw: Any = Field(
        default=None,
        description="Raw LLM response object for debugging or provider metadata.",
    )
