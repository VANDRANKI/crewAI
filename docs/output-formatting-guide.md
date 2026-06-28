# Output Formatting and Validation

This guide covers CrewAI patterns for producing reliable, structured output
from tasks and agents.

## 1. Using `output_pydantic` for typed output

Attach a Pydantic model to a task to enforce schema at runtime.

```python
from crewai import Task, Agent, Crew
from pydantic import BaseModel, Field
from typing import List

class MarketInsight(BaseModel):
    company: str
    strength: str = Field(description="Key competitive strength.")
    risk: str = Field(description="Primary risk factor.")
    score: float = Field(ge=0, le=10, description="Overall score 0-10.")

class AnalysisReport(BaseModel):
    insights: List[MarketInsight]
    recommendation: str

analysis_task = Task(
    description="Analyse the top three cloud providers and score them.",
    expected_output="A structured JSON analysis report.",
    output_pydantic=AnalysisReport,
    agent=analyst_agent,
)
```

## 2. JSON output via `output_json`

When you need JSON but not strict Pydantic validation, use `output_json`.

```python
from pydantic import BaseModel

class SummaryJson(BaseModel):
    title: str
    bullet_points: List[str]

summary_task = Task(
    description="Summarise the article into bullet points.",
    expected_output="JSON with title and bullet_points array.",
    output_json=SummaryJson,
    agent=summariser_agent,
)
```

## 3. File output

Save task output directly to disk.

```python
report_task = Task(
    description="Write a full market report.",
    expected_output="A detailed Markdown report.",
    output_file="reports/market_report.md",
    agent=writer_agent,
)
```

## 4. Chaining output between tasks

Pass a prior task as `context` so its output is available to the next task.

```python
research_task = Task(description="Research EV market trends.", agent=researcher)
write_task = Task(
    description="Write a report based on the research.",
    context=[research_task],
    agent=writer,
)
```

## 5. Validating output in callbacks

```python
def validate_report(task_output):
    report = task_output.pydantic
    if report and report.score < 0:
        raise ValueError("Score must be non-negative")

analysis_task = Task(
    ...,
    callback=validate_report,
)
```

## Output type decision guide

| Need | Use |
|---|---|
| Strict schema + type safety | `output_pydantic` |
| JSON without Pydantic | `output_json` |
| Persist result to disk | `output_file` |
| Plain text for downstream tasks | Default (no output type) |
