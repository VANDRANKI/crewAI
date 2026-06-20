# CrewAI Contributor Quick Reference

## Setup

```bash
git clone https://github.com/crewAIInc/crewAI.git
cd crewAI
pip install -e ".[dev]"
```

## Testing

```bash
# Run the full test suite
pytest tests/ -v

# Run a single test file
pytest tests/test_crew.py -v

# Run with coverage
pytest tests/ --cov=crewai --cov-report=term-missing
```

## Code quality

```bash
# Format
black crewai/ tests/

# Lint
ruff check crewai/ tests/

# Type check
mypy crewai/
```

## Common mistakes to avoid

1. **Hard-coding model names** — use `os.environ.get("MODEL", "gpt-4o")` instead.
2. **Missing `expected_output` on tasks** — always set this so the LLM knows
   what to produce.
3. **Creating agents inside the crew kickoff** — instantiate agents once and
   reuse them.
4. **Not handling `CrewAIException`** — wrap `crew.kickoff()` in a try/except
   block in production code.

## PR conventions

- Target the `main` branch.
- Reference the issue number in the PR description.
- Include at least one new test for every bug fix or feature.
