"""Execution process strategies available to a :class:`~crewai.Crew`."""

from enum import Enum


class Process(str, Enum):
    """Execution strategy that controls how a Crew assigns and runs tasks.

    Pass one of these values to the ``process`` argument of
    :class:`~crewai.Crew` to select the desired task-dispatch model.

    Members
    -------
    sequential:
        Tasks are executed one after another in the order they are defined.
        Each task starts only after the previous one completes.
    hierarchical:
        A manager agent orchestrates the crew, delegating tasks to worker
        agents and synthesising their outputs.

    Note
    ----
    Additional process types (e.g. consensual) may be added here in the
    future.  Each new entry must also be handled in the Crew kickoff logic.
    """

    sequential = "sequential"
    """Run tasks one after another in definition order."""

    hierarchical = "hierarchical"
    """Delegate tasks via a manager agent and collect their outputs."""
