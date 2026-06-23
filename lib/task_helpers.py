"""Utility helpers for working with CrewAI task results."""
from typing import Any, Optional, TypeVar

T = TypeVar("T")


def extract_task_output(result: Any, *, key: Optional[str] = None) -> str:
    """Extract string output from a task result object.

    Args:
        result: The raw result from crew.kickoff() or task.output.
        key: Optional key to look up in a dict result. When None, the
            full string representation of `result` is returned.

    Returns:
        The task output as a plain string.

    Raises:
        ValueError: If `key` is specified but not found in the result.
        TypeError: If the result type cannot be converted to a string.
    """
    if isinstance(result, str):
        return result

    if isinstance(result, dict):
        if key is None:
            return str(result)
        if key not in result:
            raise ValueError(
                f"Key '{key}' not found in task result. "
                f"Available keys: {list(result.keys())}"
            )
        return str(result[key])

    # Handle CrewOutput objects
    if hasattr(result, "raw"):
        return str(result.raw)

    return str(result)


def validate_crew_output(
    output: Any,
    expected_type: type[T],
    *,
    field: str = "output",
) -> T:
    """Validate that a crew output value matches the expected Python type.

    Args:
        output: The value to validate.
        expected_type: The expected Python type (e.g., str, dict, list).
        field: The field name for error messages.

    Returns:
        The validated value, cast to `expected_type`.

    Raises:
        TypeError: If `output` is not an instance of `expected_type`.
    """
    if not isinstance(output, expected_type):
        raise TypeError(
            f"Task '{field}' must be of type '{expected_type.__name__}', "
            f"got '{type(output).__name__}'."
        )
    return output


def truncate_output(text: str, *, max_chars: int = 2000) -> str:
    """Truncate a task output string to a maximum character count.

    Args:
        text: The string to truncate.
        max_chars: Maximum number of characters to keep.

    Returns:
        The (possibly truncated) string with an ellipsis appended if cut.
    """
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "..."
