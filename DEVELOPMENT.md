# CrewAI Development Guide

## Setup

```bash
git clone https://github.com/VANDRANKI/crewai.git
cd crewai
uv sync
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
```

## Testing

```bash
# All tests
uv run pytest

# Specific file
uv run pytest tests/test_crew.py -v

# With coverage
uv run pytest --cov=src/crewai --cov-report=html
```

## Code Quality

```bash
# Format
uv run ruff format .

# Lint
uv run ruff check .

# Type check
uv run mypy src/
```

## Pre-commit

```bash
uv run pre-commit install
uv run pre-commit run --all-files
```

## Type Hints

All public functions and methods must have full type annotations:

```python
from typing import Optional

def kickoff(
    self,
    inputs: Optional[dict] = None,
    *,
    reset_memory: bool = False,
) -> CrewOutput:
    """Execute the crew's task pipeline."""
    ...
```

## Commit Convention

```
feat: add support for parallel tool execution
fix: prevent duplicate agent runs in hierarchical process
docs: document memory reset behavior in Crew.kickoff
test: add regression test for empty crew inputs
```
