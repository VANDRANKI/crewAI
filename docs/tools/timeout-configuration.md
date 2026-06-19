# Tool and Task Timeout Configuration

CrewAI allows you to set execution timeouts on tasks and tools to prevent
runaway executions from blocking the entire crew.

## Setting a task timeout

```python
from crewai import Task

task = Task(
    description="Research the latest AI papers",
    agent=researcher,
    timeout=120,  # seconds
)
```

## Setting a tool timeout

Tools inherit their timeout from the task unless overridden:

```python
from crewai.tools import tool

@tool("web_search")
def web_search(query: str) -> str:
    """Search the web for information about the given query."""
    # implementation
```

## Timeout propagation

When a task timeout fires, CrewAI raises `TaskTimeoutError`. The crew
continues with remaining tasks — the timed-out task is marked as `failed`.

## Best practices

- Set tight timeouts on network-bound tools (web scraping, API calls)
- Leave generous timeouts (5+ minutes) for LLM-heavy tasks
- Always handle `TaskTimeoutError` in your crew's error handler
