# CrewAI Development Notes

Useful notes for contributors working on the CrewAI framework.

## Environment Setup

```bash
# Requires Python 3.12 (see .python-version)
pip install uv
uv sync
```

## Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=crewai --cov-report=term-missing

# Run a specific test file
uv run pytest tests/test_crew.py -v
```

## Code Quality

```bash
# Pre-commit hooks (run before all commits)
uv run pre-commit run --all-files
```

## Crew Architecture

A `Crew` coordinates multiple `Agent` instances working on `Task` objects:

```python
from crewai import Agent, Task, Crew, Process

researcher = Agent(
    role="Research Analyst",
    goal="Find accurate information on the given topic",
    backstory="Expert researcher with deep web search skills",
    verbose=True,
)

writer = Agent(
    role="Technical Writer",
    goal="Transform research into clear, structured content",
    backstory="Experienced writer specializing in technical documentation",
    verbose=True,
)

research_task = Task(
    description="Research the topic: {topic}",
    expected_output="A comprehensive research report with key findings",
    agent=researcher,
)

write_task = Task(
    description="Write an article based on the research findings",
    expected_output="A well-structured article of 500-700 words",
    agent=writer,
    context=[research_task],
)

crew = Crew(
    agents=[researcher, writer],
    tasks=[research_task, write_task],
    process=Process.sequential,
    verbose=True,
)

result = crew.kickoff(inputs={"topic": "AI agents"})
```

## Adding New Features

1. Follow existing patterns in `src/crewai/`
2. Add type hints to all public methods
3. Write tests in `tests/`
4. Update documentation if the feature is user-facing

## Common Issues

**Circular tool calls**: Ensure `max_iter` is set to prevent infinite agent loops.

**Context too large**: Use `memory=True` selectively; large context windows incur high costs.

**Tool output formatting**: Tool `run()` methods must return strings; wrap complex objects with `json.dumps()`.
