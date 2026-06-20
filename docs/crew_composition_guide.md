# Crew Composition Guide

Best practices for structuring agents, tasks, and crews in production
CrewAI applications.

---

## Agent design principles

### One role per agent

Each agent should have a single, well-defined role. Avoid catch-all agents that
handle unrelated responsibilities — they are harder to debug and their outputs
are harder to evaluate.

```python
from crewai import Agent

# Good: focused role
researcher = Agent(
    role="Senior Research Analyst",
    goal="Find and synthesise accurate information from reliable sources",
    backstory=(
        "You are an expert researcher with 10 years of experience in "
        "scientific literature review."
    ),
    verbose=True,
)

# Avoid: vague, multi-purpose role
general_agent = Agent(
    role="General Assistant",
    goal="Do whatever is needed",
    backstory="You can do anything.",
)
```

### Memory and caching

Enable memory for agents that need context across multiple task executions:

```python
agent = Agent(
    role="Data Analyst",
    goal="Analyse financial reports",
    backstory="Expert in financial modelling.",
    memory=True,          # retain context between runs
    cache=True,           # cache tool results to avoid redundant calls
    max_iter=10,          # guard against infinite tool loops
)
```

---

## Task dependency patterns

### Sequential tasks with `context`

Pass the output of earlier tasks as context to later tasks:

```python
from crewai import Task

research_task = Task(
    description="Research the top 5 competitors of {company}.",
    expected_output="A bullet-point list of competitors with their main products.",
    agent=researcher,
)

analysis_task = Task(
    description="Analyse the competitive landscape based on the research.",
    expected_output="A SWOT analysis in markdown format.",
    agent=analyst,
    context=[research_task],   # receives research_task.output
)
```

### Parallel execution with `async_execution`

Mark independent tasks to run in parallel:

```python
task_a = Task(
    description="Gather financial data for Q1.",
    expected_output="Raw Q1 financial figures.",
    agent=data_agent,
    async_execution=True,
)

task_b = Task(
    description="Gather financial data for Q2.",
    expected_output="Raw Q2 financial figures.",
    agent=data_agent,
    async_execution=True,
)

summary_task = Task(
    description="Summarise the full-year financial performance.",
    expected_output="Full-year financial summary.",
    agent=analyst,
    context=[task_a, task_b],  # waits for both
)
```

---

## Error handling

### Catching `CrewAIException`

```python
from crewai import Crew, CrewOutput
from crewai.exceptions import CrewAIException

try:
    result: CrewOutput = crew.kickoff(inputs={"company": "Acme Corp"})
except CrewAIException as exc:
    # Log structured details and surface a user-friendly message.
    print(f"Crew execution failed: {exc}")
    raise
```

### Validating crew outputs

Always specify `expected_output` on tasks so that the LLM has a clear target
format to produce. For structured data, use `output_pydantic`:

```python
from pydantic import BaseModel

class CompetitorList(BaseModel):
    companies: list[str]
    sources: list[str]

task = Task(
    description="List the top 5 competitors.",
    expected_output="JSON matching the CompetitorList schema.",
    agent=researcher,
    output_pydantic=CompetitorList,
)
```
