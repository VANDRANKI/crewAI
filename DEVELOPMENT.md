# Development Guide

This guide helps you set up a local development environment and contribute
to CrewAI.

## Prerequisites

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) or [Poetry](https://python-poetry.org/)

## Setup

```bash
# Clone the repository
git clone https://github.com/crewAIInc/crewAI
cd crewAI

# Install with uv (recommended)
uv sync --all-groups

# Or with Poetry
poetry install
```

## Running Tests

```bash
# All tests
uv run pytest tests/ -v

# Unit tests only (no LLM calls)
uv run pytest tests/unit/ -v

# A specific test file
uv run pytest tests/test_agent.py -v

# A specific test
uv run pytest tests/test_agent.py::TestAgent::test_execute_task -v
```

## Code Style

CrewAI uses **Black** for formatting and **Ruff** for linting.

```bash
# Format
uv run black .

# Lint
uv run ruff check .

# Type check
uv run mypy src/crewai/
```

## Adding a New Tool

1. Create `src/crewai/tools/<tool_name>.py` inheriting from `BaseTool`.
2. Implement `_run(self, **kwargs)` and optionally `_arun` for async support.
3. Add the tool to `src/crewai/tools/__init__.py`.
4. Write tests in `tests/tools/test_<tool_name>.py`.

Example skeleton:

```python
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

class MyToolInput(BaseModel):
    query: str = Field(description="The search query")

class MyTool(BaseTool):
    name: str = "My Tool"
    description: str = "Does something useful."
    args_schema: type[BaseModel] = MyToolInput

    def _run(self, query: str) -> str:
        return f"Result for: {query}"
```

## Adding a New Agent Type

1. Subclass `Agent` in `src/crewai/agent.py` or create a new file under
   `src/crewai/agents/`.
2. Override `execute_task()` with the custom logic.
3. Register the agent type in the appropriate factory or `__init__.py`.
4. Add integration tests that exercise the full crew pipeline with the new agent.

## Pre-Commit Checklist

- [ ] `uv run black . --check` passes
- [ ] `uv run ruff check .` reports no errors
- [ ] `uv run pytest tests/unit/` passes
- [ ] New feature has tests covering the happy path and error cases
- [ ] Docstrings added for all new public methods (Google style)
- [ ] `CHANGELOG.md` updated if the change is user-facing
