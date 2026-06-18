# CrewAI Task Execution Lifecycle

This guide explains how Tasks move through states during a Crew kickoff,
how output is passed between tasks, and how to safely reuse a Crew across
multiple `kickoff()` calls.

## Task State Machine

Each Task transitions through these states during a Crew run:

```
pending → running → (complete | failed)
                         ↓
                   output available
```

- **pending**: Initial state. The task has not been assigned to an Agent yet.
- **running**: An Agent is currently working on the task.
- **complete**: The Agent produced an output and it passed validation (if a `Pydantic` model is set).
- **failed**: The Agent hit the `max_retries` limit without a valid output.

## Task Output Propagation

By default, CrewAI chains task outputs sequentially. The output of task N
becomes the context for task N+1 via `context`:

```python
from crewai import Task, Crew, Agent

researcher = Agent(role="Researcher", goal="Find facts", backstory="...")
writer = Agent(role="Writer", goal="Write report", backstory="...")

research_task = Task(
    description="Research the topic: {topic}",
    expected_output="A bullet list of key facts",
    agent=researcher,
)

writing_task = Task(
    description="Write a 500-word report on the research",
    expected_output="A formatted report",
    agent=writer,
    context=[research_task],  # explicitly reference upstream task
)

crew = Crew(agents=[researcher, writer], tasks=[research_task, writing_task])
result = crew.kickoff(inputs={"topic": "AI safety"})
```

## Structured Output with Pydantic

Use `output_pydantic` to enforce structured output. If the Agent returns
malformed JSON, the task is retried up to `max_retries` times:

```python
from pydantic import BaseModel
from typing import Optional

class ResearchOutput(BaseModel):
    title: str
    key_facts: list[str]
    sources: list[str]
    confidence: Optional[float] = None

research_task = Task(
    description="Research {topic} and return structured findings",
    expected_output="JSON matching ResearchOutput schema",
    agent=researcher,
    output_pydantic=ResearchOutput,
)
```

## Reusing a Crew Across Multiple Runs

When you call `crew.kickoff()` a second time, task outputs from the first run
are **not automatically cleared**. This causes stale context to leak into the
new run.

**Always reset before reusing:**

```python
crew = Crew(agents=[researcher, writer], tasks=[research_task, writing_task])

# Run 1
result1 = crew.kickoff(inputs={"topic": "AI safety"})

# Reset task state before run 2
for task in crew.tasks:
    task.output = None

# Run 2 — clean slate
result2 = crew.kickoff(inputs={"topic": "AI regulation"})
```

Alternatively, construct a new `Crew` instance for each run if the tasks
are lightweight to construct.

## Async Execution

For parallel task execution (tasks with no dependencies), use `kickoff_async`:

```python
import asyncio

async def main():
    crew = Crew(
        agents=[researcher, writer],
        tasks=[research_task, writing_task],
        process="parallel",  # run independent tasks in parallel
    )
    result = await crew.kickoff_async(inputs={"topic": "AI safety"})
    print(result.raw)

asyncio.run(main())
```

Note: tasks with `context=[other_task]` always wait for the referenced task
even in parallel mode. Only tasks with no `context` dependencies run in parallel.

## Debugging Failed Tasks

```python
result = crew.kickoff(inputs={"topic": "AI safety"})

for task in crew.tasks:
    if task.output is None:
        print(f"Task failed or not run: {task.description[:50]}")
    else:
        print(f"Task complete: {task.output.summary[:100]}")
```
