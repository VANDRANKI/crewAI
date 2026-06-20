#!/usr/bin/env python3
"""Validate CrewAI crew and agent configurations for common mistakes.

This script imports a crew definition module and checks for:

- Agents with duplicate roles
- Tasks that reference undefined agents
- Missing ``expected_output`` on tasks
- Overly long task descriptions (>500 chars) that may confuse the LLM

Usage::

    python scripts/validate_crew_config.py --module my_crew.crew --attr crew
"""

from __future__ import annotations

import argparse
import importlib
import sys
from typing import Any

MAX_DESC_LEN = 500


def validate_crew(crew: Any) -> list[str]:
    """Validate a Crew instance and return a list of issue descriptions.

    Args:
        crew: A CrewAI ``Crew`` instance to validate.

    Returns:
        List of issue strings; empty if no issues are found.
    """
    issues: list[str] = []

    # Validate agents.
    agents = getattr(crew, "agents", [])
    seen_roles: set[str] = set()
    for agent in agents:
        role = getattr(agent, "role", "<unknown>")
        if role in seen_roles:
            issues.append(f"Duplicate agent role: '{role}'")
        seen_roles.add(role)

    # Validate tasks.
    tasks = getattr(crew, "tasks", [])
    for i, task in enumerate(tasks, 1):
        desc = getattr(task, "description", "")
        expected = getattr(task, "expected_output", None)
        task_agent = getattr(task, "agent", None)

        if not expected:
            issues.append(f"Task {i}: missing 'expected_output'")

        if len(desc) > MAX_DESC_LEN:
            issues.append(
                f"Task {i}: description is {len(desc)} chars (>{MAX_DESC_LEN}); "
                "consider shortening to improve LLM compliance."
            )

        if task_agent is not None:
            agent_role = getattr(task_agent, "role", None)
            if agent_role not in seen_roles:
                issues.append(
                    f"Task {i}: assigned agent role '{agent_role}' is not in crew.agents"
                )

    return issues


def main() -> None:
    """Entry point for the crew config validator."""
    parser = argparse.ArgumentParser(
        description="Validate a CrewAI crew configuration."
    )
    parser.add_argument(
        "--module", required=True, help="Dotted module path (e.g. my_crew.crew)."
    )
    parser.add_argument(
        "--attr", default="crew", help="Attribute name of the Crew object."
    )
    args = parser.parse_args()

    try:
        mod = importlib.import_module(args.module)
    except ImportError as exc:
        print(f"ERROR: Cannot import '{args.module}': {exc}", file=sys.stderr)
        sys.exit(1)

    crew = getattr(mod, args.attr, None)
    if crew is None:
        print(f"ERROR: '{args.attr}' not found in '{args.module}'.", file=sys.stderr)
        sys.exit(1)

    issues = validate_crew(crew)
    if issues:
        print(f"Found {len(issues)} issue(s):")
        for issue in issues:
            print(f"  - {issue}")
        sys.exit(1)
    else:
        print("Crew configuration looks valid.")


if __name__ == "__main__":
    main()
