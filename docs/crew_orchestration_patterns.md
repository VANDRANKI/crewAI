# Crew Orchestration Patterns

This guide covers common patterns for building robust multi-agent crews.

## Process Selection

### Sequential Process

Tasks run one after another, each receiving the output of the previous task.
Use this when tasks have a strict dependency chain.

```python
from crewai import Crew, Process

crew = Crew(
    agents=[researcher, writer, editor],
    tasks=[research_task, write_task, edit_task],
    process=Process.sequential,
)
```

**Best for:** Pipelines where each step depends on the previous (research → write → review).

### Hierarchical Process

A manager agent coordinates other agents and assigns tasks dynamically.
The manager decides which agent handles which task based on context.

```python
crew = Crew(
    agents=[researcher, analyst, writer],
    tasks=[complex_task],
    process=Process.hierarchical,
    manager_llm="gpt-5.4",  # LLM for the auto-created manager agent
)
```

**Best for:** Complex tasks requiring dynamic agent selection and parallel work.

## Sharing Context Between Tasks

Use `context` to explicitly feed one task's output into another:

```python
research_task = Task(
    description="Research the topic: {topic}",
    agent=researcher,
    expected_output="A detailed research report",
)

write_task = Task(
    description="Write an article based on the research",
    agent=writer,
    expected_output="A polished 500-word article",
    context=[research_task],  # Receives research_task output automatically
)
```

## Memory Configuration

For crews that handle long sessions, enable memory to retain context:

```python
crew = Crew(
    agents=[agent1, agent2],
    tasks=[task1, task2],
    memory=True,          # Enable short-term memory
    embedder={
        "provider": "openai",
        "config": {"model": "text-embedding-3-small"},
    },
)
```

## Callbacks for Monitoring

```python
def on_task_complete(task_output):
    print(f"Task completed: {task_output.description[:50]}...")
    print(f"Result preview: {str(task_output.raw)[:100]}")

task = Task(
    description="Analyze market data",
    agent=analyst,
    expected_output="Market analysis report",
    callback=on_task_complete,
)
```

## Production Checklist

- [ ] Set `max_iter` on agents to prevent infinite loops
- [ ] Use `output_pydantic` or `output_json` for structured task outputs
- [ ] Enable `verbose=True` during development; disable in production
- [ ] Set appropriate LLM timeouts via the `llm` config
- [ ] Test each agent and task in isolation before assembling the crew
- [ ] Add callbacks to monitor long-running crews in production
