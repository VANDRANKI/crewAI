# Writing Effective Agent Backstories

The `backstory` field is one of the most impactful levers for guiding Agent
behavior in CrewAI. This guide explains what to include, what to avoid, and
how backstories interact with the `role` and `goal` fields.

## What the Backstory Does

The backstory is prepended to the Agent's system prompt. The LLM uses it to:

1. Adopt a persona (writing style, level of formality, area of expertise)
2. Apply domain constraints (e.g., "cite primary sources", "avoid speculation")
3. Set the reasoning approach (e.g., "think step-by-step", "prioritize speed")

## Anatomy of a Good Backstory

```python
researcher = Agent(
    role="Senior Research Analyst",
    goal="Produce accurate, well-sourced research summaries",
    backstory=(
        "You are a senior research analyst with 15 years of experience in "
        "technology policy. You excel at synthesizing complex information "
        "from multiple sources into clear, actionable summaries. "
        "You always cite your sources and flag uncertainty explicitly "
        "rather than speculating. When data is ambiguous, you present "
        "multiple interpretations rather than picking one arbitrarily."
    ),
)
```

Key elements:
- **Persona**: who the agent is (seniority, domain)
- **Strength**: what they're good at (synthesizing, writing, analyzing)
- **Constraint**: what they won't do (speculate, omit sources)
- **Fallback**: how they handle ambiguity

## Common Mistakes

**Too vague**:
```python
backstory="You are a helpful AI assistant."  # provides no useful constraints
```

**Contradicts the goal**:
```python
# goal says "fast summary" but backstory says "comprehensive analysis"
goal="Produce a quick 3-sentence summary"
backstory="You are a meticulous analyst who leaves no stone unturned and
           produces exhaustive 50-page reports."
```

**Personality-only, no domain knowledge**:
```python
backstory="You are enthusiastic, optimistic, and love solving problems!"  
# LLM has no domain grounding from this
```

## Backstory and Memory

When `memory=True` is set on the Agent, the backstory persists across
`kickoff()` calls via the agent's long-term memory store. This means
past run context can influence future runs. If you want a clean slate
between runs, set `memory=False` or clear the memory:

```python
agent = Agent(role="...", goal="...", backstory="...", memory=True)
# After run 1
agent.memory.clear()  # clear episodic and long-term memory
# Run 2 starts fresh
```
