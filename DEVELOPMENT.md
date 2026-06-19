# CrewAI Development Guide

This document covers everything a new contributor needs to get a working local development environment and understand the project conventions.

## Project Structure

```
crewai/
├── lib/                  # Core source code
│   └── crewai/           # Main package
│       ├── agent/        # Agent implementation
│       ├── crew/         # Crew orchestration
│       ├── task/         # Task definitions
│       ├── tools/        # Built-in tools
│       └── flow/         # Flow definitions
├── conftest.py           # Pytest fixtures and shared test setup
├── .env.test             # Test API keys and configuration (see below)
├── pyproject.toml        # Project metadata, dependencies, tool config
└── uv.lock               # Locked dependency graph
```

## Environment Setup

This project uses [`uv`](https://docs.astral.sh/uv/) for dependency management.

```bash
# Create a virtual environment and install all dependencies
uv sync

# Activate the virtual environment
source .venv/bin/activate

# Or run commands directly without activating
uv run python -c "import crewai; print(crewai.__version__)"
```

## Running Tests

### Configure test environment

Copy `.env.test` and fill in your API keys:

```bash
cp .env.test .env.test.local
# Edit .env.test.local with your keys
```

The `conftest.py` at the repo root loads this file automatically before any test run. Key variables:

- `OPENAI_API_KEY` — required for most integration tests
- `ANTHROPIC_API_KEY` — required for Anthropic agent tests
- `SERPER_API_KEY` — required for search tool tests

Check `.env.test` for the full list of configurable variables.

### Run the test suite

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run a specific test file
uv run pytest lib/crewai/tests/test_crew.py -v

# Run a specific test function
uv run pytest lib/crewai/tests/test_crew.py::test_crew_kickoff -v

# Run tests with coverage report
uv run pytest --cov=lib/crewai --cov-report=term-missing

# Run only unit tests (no network calls)
uv run pytest -m unit
```

## Linting and Formatting

```bash
# Check linting with ruff
uv run ruff check .

# Fix auto-fixable lint issues
uv run ruff check --fix .

# Format code
uv run ruff format .

# Type checking with mypy
uv run mypy lib/crewai --ignore-missing-imports
```

## conftest.py Setup

The root `conftest.py` provides:

- **Environment loading**: Reads `.env.test` (or `.env.test.local`) and injects API keys before tests run.
- **Mock fixtures**: Common mocks for LLM calls so unit tests don't hit real APIs.
- **Shared agents/crews**: Reusable test fixtures for `Agent`, `Task`, and `Crew` objects.
- **Cleanup hooks**: Tears down any state (e.g., in-memory stores) between tests.

When writing tests, prefer importing fixtures from `conftest.py` rather than constructing objects inline.

## Code Conventions

### Type hints

All public methods and functions must have full type annotations including return types:

```python
from typing import Any, Optional

def execute_task(self, task: Task, context: Optional[str] = None) -> str:
    """Execute a task and return the result.

    Args:
        task: The task to execute.
        context: Optional context string from prior tasks.

    Returns:
        The string result produced by the agent.
    """
    ...
```

### Error handling

Never swallow exceptions silently. Always either re-raise or log with sufficient context:

```python
# Bad — exception is lost
try:
    result = agent.execute(task)
except Exception:
    pass

# Good — exception is propagated with context
try:
    result = agent.execute(task)
except Exception as err:
    msg = f"Agent {agent.role!r} failed to execute task {task.description!r}: {err}"
    raise RuntimeError(msg) from err
```

### Async patterns

For async kickoff methods, ensure exceptions from individual agent tasks bubble up to the caller:

```python
async def kickoff_async(self) -> CrewOutput:
    """Run the crew asynchronously and return the output."""
    try:
        results = await asyncio.gather(*self._build_coroutines(), return_exceptions=False)
    except Exception as err:
        msg = f"Crew kickoff failed: {err}"
        raise RuntimeError(msg) from err
    return self._build_output(results)
```

**Do not** use `return_exceptions=True` unless you handle every exception in the returned list — it silently swallows errors otherwise.

### Pydantic models

Use Pydantic v2 patterns throughout:

```python
from pydantic import BaseModel, Field, model_validator

class AgentConfig(BaseModel):
    role: str = Field(description="The role the agent will play.")
    goal: str = Field(description="The primary goal of the agent.")
    max_iter: int = Field(default=25, ge=1, description="Maximum iterations.")

    @model_validator(mode="after")
    def validate_goal_not_empty(self) -> "AgentConfig":
        if not self.goal.strip():
            msg = "Agent goal must not be empty"
            raise ValueError(msg)
        return self
```

Do not use Pydantic v1 `@validator` decorators — use `@model_validator(mode="after")` or `@field_validator`.

## Commit Message Format

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
type: description
```

Valid types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`

Examples:

```
feat: add kickoff_async exception propagation
fix: agent execute_task missing return type annotation
docs: add DEVELOPMENT.md developer onboarding guide
chore: expand .gitignore to cover uv and coverage artifacts
```
