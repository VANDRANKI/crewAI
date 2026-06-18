# Type Hints Guide

All public functions and methods in CrewAI must have complete type
annotations. This document covers the expected patterns.

## Basic Patterns

```python
from __future__ import annotations
from typing import Any, Optional

def kickoff(
    self,
    inputs: Optional[dict[str, Any]] = None,
) -> CrewOutput:
    """Execute the crew and return a structured output."""
    ...
```

## Optional vs Union

Prefer `Optional[X]` over `X | None` for Python 3.10 compatibility:

```python
# Good
def get_agent(name: Optional[str] = None) -> Agent: ...

# Avoid (requires Python 3.10+)
def get_agent(name: str | None = None) -> Agent: ...
```

## Return Types

Always annotate return types, even when returning `None`:

```python
def reset_memory(self) -> None:
    self._memory = []
```

## Error Handling

Raise specific exception types. Never catch `Exception` without re-raising:

```python
try:
    result = agent.execute_task(task)
except ToolExecutionError as e:
    logger.error("Tool failed", tool=e.tool_name, error=str(e))
    raise  # always re-raise unless you have a recovery strategy
```

## Pydantic Models

CrewAI uses Pydantic v2. Use `model_validator` over deprecated `validator`:

```python
from pydantic import BaseModel, model_validator

class CrewConfig(BaseModel):
    max_iterations: int = 10
    verbose: bool = False

    @model_validator(mode="after")
    def check_iterations(self) -> "CrewConfig":
        if self.max_iterations < 1:
            raise ValueError("max_iterations must be at least 1")
        return self
```
