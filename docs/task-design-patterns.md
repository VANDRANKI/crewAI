# Task Design Patterns

CrewAI tasks are the atomic unit of work assigned to an agent. Well-designed
tasks lead to more reliable, predictable crews. This guide covers patterns for
description writing, context chaining, output schemas, and error recovery.

## Task Anatomy

```python
from crewai import Task

task = Task(
    description=(
        "Analyse the financial report at {report_url} and identify "
        "the three most significant risks. Focus on liquidity, leverage, "
        "and operational risks. Return your findings as a numbered list."
    ),
    expected_output=(
        "A numbered list of exactly three risks, each with: "
        "(1) risk name, (2) severity (high/medium/low), "
        "(3) one-sentence explanation."
    ),
    agent=risk_analyst_agent,
)
```

**Key fields:**
- `description`: What to do and how to do it. More specific = more reliable.
- `expected_output`: What the agent's response should look like. Acts as an
  implicit rubric for the LLM.
- `agent`: Which agent is responsible.

---

## Pattern 1: Input Variables

Use `{variable_name}` placeholders in `description`; supply values in
`crew.kickoff(inputs=...)`:

```python
task = Task(
    description="Write a {length}-word blog post about {topic}.",
    expected_output="A polished blog post suitable for publication.",
    agent=writer_agent,
)

crew.kickoff(inputs={"topic": "LLM caching", "length": "800"})
```

---

## Pattern 2: Context Chaining

Pass the output of one task as context to a downstream task:

```python
research_task = Task(
    description="Research the latest advancements in {topic}.",
    expected_output="A bullet-point list of five key findings.",
    agent=researcher_agent,
)

summary_task = Task(
    description=(
        "Using the research findings below, write an executive summary "
        "suitable for a non-technical audience.\n\n{research_task.output}"
    ),
    expected_output="A 150-word executive summary.",
    agent=writer_agent,
    context=[research_task],  # injects research_task output automatically
)
```

When `context` is set, CrewAI injects the referenced tasks' outputs into
the agent's prompt before execution.

---

## Pattern 3: Structured Output with Pydantic

Force type-safe output by providing an `output_pydantic` model:

```python
from pydantic import BaseModel, Field
from typing import List


class CompetitorAnalysis(BaseModel):
    company_name: str = Field(..., description="Name of the competitor.")
    strengths: List[str] = Field(..., description="Key competitive advantages.")
    weaknesses: List[str] = Field(..., description="Areas where they fall short.")
    market_share_estimate: float = Field(
        ..., ge=0.0, le=1.0, description="Estimated market share (0–1)."
    )


analysis_task = Task(
    description="Analyse {company} as a competitor in the {market} market.",
    expected_output="A structured competitor analysis.",
    output_pydantic=CompetitorAnalysis,
    agent=analyst_agent,
)

result = crew.kickoff(inputs={"company": "Acme Corp", "market": "SaaS"})
analysis: CompetitorAnalysis = result.pydantic
print(analysis.market_share_estimate)  # typed float
```

---

## Pattern 4: File Output

Save task output directly to a file:

```python
report_task = Task(
    description="Generate a weekly status report in Markdown.",
    expected_output="A complete Markdown report.",
    output_file="reports/weekly_status.md",
    agent=reporter_agent,
)
```

CrewAI writes the agent's final response to the specified path after the
task completes. Combine with `output_pydantic` to get both typed data and
a persisted artefact.

---

## Pattern 5: Async Tasks (Parallel Execution)

Mark independent tasks as async to run them concurrently in a
`Process.sequential` crew:

```python
research_task = Task(
    description="Research the latest papers on {topic}.",
    expected_output="A list of five recent papers with abstracts.",
    agent=researcher_agent,
    async_execution=True,  # runs in parallel with data_task
)

data_task = Task(
    description="Pull the latest metrics for {topic} from our database.",
    expected_output="JSON with current metrics.",
    agent=data_agent,
    async_execution=True,  # runs in parallel with research_task
)

synthesis_task = Task(
    description="Synthesise the research papers and metrics into a report.",
    expected_output="A 500-word synthesis report.",
    agent=writer_agent,
    context=[research_task, data_task],  # waits for both async tasks
)
```

---

## Writing Effective Descriptions

| Avoid | Prefer |
|-------|--------|
| `"Analyse the data"` | `"Identify the three highest-revenue products from the Q2 sales CSV and calculate their YoY growth rate."` |
| `"Write a summary"` | `"Write a 200-word executive summary for a CFO audience, highlighting risk and opportunity. Use plain language, no jargon."` |
| `"Research {topic}"` | `"Find five peer-reviewed papers on {topic} published after 2023. For each, list: title, authors, publication venue, and the core contribution in one sentence."` |

**Rule of thumb**: if a junior human employee could misinterpret the task,
so can the agent. Add constraints, output format, audience, and scope.
