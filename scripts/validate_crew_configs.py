#!/usr/bin/env python3
"""Validate CrewAI agents.yaml and tasks.yaml configuration files.

Scans for config directories produced by 'crewai create crew', checks
that agents have required fields (role, goal, backstory) and tasks have
(description, expected_output, agent), and reports any missing fields.

Usage:
    python scripts/validate_crew_configs.py
    python scripts/validate_crew_configs.py --path src/my_crew
    python scripts/validate_crew_configs.py --verbose
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

AGENT_REQUIRED = {"role", "goal", "backstory"}
TASK_REQUIRED = {"description", "expected_output", "agent"}


def validate_agents_yaml(path: Path) -> list[str]:
    """Return issues found in agents.yaml."""
    issues: list[str] = []
    try:
        data = yaml.safe_load(path.read_text())
    except yaml.YAMLError as exc:
        return [f"YAML parse error: {exc}"]
    if not isinstance(data, dict):
        return ["Expected a mapping of agent_name -> config"]
    for agent_name, config in data.items():
        if not isinstance(config, dict):
            issues.append(f"{agent_name}: config is not a mapping")
            continue
        for field in sorted(AGENT_REQUIRED):
            if field not in config:
                issues.append(f"{agent_name}: missing required field '{field}'")
    return issues


def validate_tasks_yaml(path: Path) -> list[str]:
    """Return issues found in tasks.yaml."""
    issues: list[str] = []
    try:
        data = yaml.safe_load(path.read_text())
    except yaml.YAMLError as exc:
        return [f"YAML parse error: {exc}"]
    if not isinstance(data, dict):
        return ["Expected a mapping of task_name -> config"]
    for task_name, config in data.items():
        if not isinstance(config, dict):
            issues.append(f"{task_name}: config is not a mapping")
            continue
        for field in sorted(TASK_REQUIRED):
            if field not in config:
                issues.append(f"{task_name}: missing required field '{field}'")
    return issues


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--path", type=Path, default=Path("."),
        help="Root directory to search for config/ dirs (default: .)",
    )
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args(argv)

    root: Path = args.path
    found = list(root.rglob("config/agents.yaml")) + list(root.rglob("config/tasks.yaml"))

    if not found:
        print("No agents.yaml or tasks.yaml found under config/ directories.")
        return 0

    all_issues: dict[str, list[str]] = {}

    for config_dir in sorted({f.parent for f in found}):
        agents_yaml = config_dir / "agents.yaml"
        tasks_yaml = config_dir / "tasks.yaml"

        if agents_yaml.exists():
            issues = validate_agents_yaml(agents_yaml)
            if issues:
                all_issues[str(agents_yaml)] = issues
            elif args.verbose:
                print(f"OK  {agents_yaml}")

        if tasks_yaml.exists():
            issues = validate_tasks_yaml(tasks_yaml)
            if issues:
                all_issues[str(tasks_yaml)] = issues
            elif args.verbose:
                print(f"OK  {tasks_yaml}")

    if all_issues:
        print(f"\nValidation errors in {len(all_issues)} file(s):\n")
        for filepath, issues in sorted(all_issues.items()):
            for issue in issues:
                print(f"  {filepath}: {issue}")
        return 1

    yaml_count = len({f.parent for f in found})
    print(f"All config directories ({yaml_count}) passed validation.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
