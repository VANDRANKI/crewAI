"""Internationalization support for CrewAI prompts and messages."""

from functools import lru_cache
import json
import os
from typing import Literal

from pydantic import BaseModel, Field, PrivateAttr, model_validator
from typing_extensions import Self


class I18N(BaseModel):
    """Handles loading and retrieving internationalized prompts.

    Attributes:
        _prompts: Internal dictionary storing loaded prompts.
        prompt_file: Optional path to a custom JSON file containing prompts.
    """

    _prompts: dict[str, dict[str, str]] = PrivateAttr()
    prompt_file: str | None = Field(
        default=None,
        description="Path to the prompt_file file to load",
    )

    @model_validator(mode="after")
    def load_prompts(self) -> Self:
        """Load prompts from a JSON file.

        Loads from ``prompt_file`` when provided, otherwise falls back to the
        built-in ``translations/en.json`` file bundled with the package.

        Returns:
            The I18N instance with loaded prompts.

        Raises:
            FileNotFoundError: If the prompt file does not exist on disk.
            ValueError: If the prompt file exists but contains invalid JSON.
        """
        if self.prompt_file:
            path = self.prompt_file
        else:
            dir_path = os.path.dirname(os.path.realpath(__file__))
            path = os.path.join(dir_path, "../translations/en.json")

        try:
            with open(path, encoding="utf-8") as f:
                self._prompts = json.load(f)
        except FileNotFoundError as e:
            raise FileNotFoundError(
                f"Prompt file not found: '{path}'. "
                "Ensure the path is correct and the file exists."
            ) from e
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Failed to decode JSON from prompt file '{path}': {e.msg} "
                f"(line {e.lineno}, column {e.colno})."
            ) from e

        if not self._prompts:
            self._prompts = {}

        return self

    def slice(self, slice: str) -> str:
        """Retrieve a prompt slice by key.

        Args:
            slice: The key of the prompt slice to retrieve.

        Returns:
            The prompt slice as a string.
        """
        return self.retrieve("slices", slice)

    def errors(self, error: str) -> str:
        """Retrieve an error message by key.

        Args:
            error: The key of the error message to retrieve.

        Returns:
            The error message as a string.
        """
        return self.retrieve("errors", error)

    def tools(self, tool: str) -> str | dict[str, str]:
        """Retrieve a tool prompt by key.

        Args:
            tool: The key of the tool prompt to retrieve.

        Returns:
            The tool prompt as a string or dictionary.
        """
        return self.retrieve("tools", tool)

    def memory(self, key: str) -> str:
        """Retrieve a memory prompt by key.

        Args:
            key: The key of the memory prompt to retrieve.

        Returns:
            The memory prompt as a string.
        """
        return self.retrieve("memory", key)

    def retrieve(
        self,
        kind: Literal[
            "slices",
            "errors",
            "tools",
            "reasoning",
            "planning",
            "hierarchical_manager_agent",
            "memory",
        ],
        key: str,
    ) -> str:
        """Retrieve a prompt by kind and key.

        Args:
            kind: The category of prompt to look up (e.g. ``"slices"``,
                ``"errors"``, ``"tools"``).
            key: The specific prompt key within that category.

        Returns:
            The prompt string.

        Raises:
            KeyError: If ``kind`` or ``key`` is not present in the loaded
                prompts, indicating a missing translation entry.
        """
        try:
            return self._prompts[kind][key]
        except KeyError as e:
            raise KeyError(
                f"Prompt not found for kind='{kind}', key='{key}'. "
                "Check that the translation file contains this entry."
            ) from e


@lru_cache(maxsize=None)
def get_i18n(prompt_file: str | None = None) -> I18N:
    """Return a cached I18N instance.

    Caches I18N instances to avoid redundant file I/O and JSON parsing.
    Each unique ``prompt_file`` path gets its own cached instance.

    Args:
        prompt_file: Optional custom prompt file path. Defaults to ``None``
            (uses the built-in ``translations/en.json``).

    Returns:
        Cached I18N instance for the given prompt file.
    """
    return I18N(prompt_file=prompt_file)


I18N_DEFAULT: I18N = get_i18n()
