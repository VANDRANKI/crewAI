#!/usr/bin/env bash
# run_tests.sh
#
# Helper script for running the CrewAI test suite locally.
# Activates the virtual environment if present, loads test environment
# variables from .env.test (or .env.test.local if it exists), and
# forwards all arguments to pytest.
#
# Usage:
#   bash scripts/run_tests.sh                          # run all tests
#   bash scripts/run_tests.sh -v                       # verbose
#   bash scripts/run_tests.sh -m unit                  # unit tests only
#   bash scripts/run_tests.sh lib/crewai/tests/test_crew.py  # one file
#   bash scripts/run_tests.sh --cov=lib/crewai --cov-report=term-missing
#
# Exit codes mirror pytest exit codes:
#   0  all tests passed
#   1  some tests failed
#   2  interrupted
#   3  internal error
#   4  usage error
#   5  no tests collected

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$REPO_ROOT"

# ---------------------------------------------------------------------------
# Activate virtual environment if it exists
# ---------------------------------------------------------------------------
if [[ -f ".venv/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source ".venv/bin/activate"
  echo "Activated virtual environment: .venv"
elif command -v uv &>/dev/null; then
  echo "No .venv found; will use 'uv run' prefix"
else
  echo "WARNING: No .venv found and uv is not installed. Tests may fail." >&2
fi

# ---------------------------------------------------------------------------
# Load test environment variables
# Prefer .env.test.local (gitignored personal overrides) over .env.test
# ---------------------------------------------------------------------------
ENV_FILE=""
if [[ -f ".env.test.local" ]]; then
  ENV_FILE=".env.test.local"
  echo "Loading test env from: .env.test.local"
elif [[ -f ".env.test" ]]; then
  ENV_FILE=".env.test"
  echo "Loading test env from: .env.test"
else
  echo "WARNING: No .env.test or .env.test.local found. API key tests will likely fail." >&2
fi

if [[ -n "$ENV_FILE" ]]; then
  # Export each non-comment, non-empty line as an environment variable
  while IFS= read -r line || [[ -n "$line" ]]; do
    # Skip blank lines and comments
    [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
    # Only export lines that look like KEY=VALUE
    if [[ "$line" =~ ^[A-Za-z_][A-Za-z0-9_]*= ]]; then
      export "$line"
    fi
  done < "$ENV_FILE"
fi

# ---------------------------------------------------------------------------
# Run pytest, passing through all CLI arguments
# ---------------------------------------------------------------------------
echo ""
echo "Running: pytest $*"
echo "---"

if command -v pytest &>/dev/null; then
  exec pytest "$@"
elif command -v uv &>/dev/null; then
  exec uv run pytest "$@"
else
  echo "ERROR: pytest not found. Install dependencies with: uv sync" >&2
  exit 4
fi
