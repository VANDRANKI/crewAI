"""Unit tests for crewai.utilities.timeout_utils."""

import asyncio
import pytest
import sys


@pytest.mark.skipif(sys.platform == "win32", reason="SIGALRM not available on Windows")
class TestRunWithTimeout:
    def test_succeeds_within_timeout(self):
        from lib.crewai.utilities.timeout_utils import run_with_timeout
        result = run_with_timeout(lambda: 42, timeout_seconds=5)
        assert result == 42

    def test_raises_task_timeout_error(self):
        import time
        from lib.crewai.utilities.timeout_utils import run_with_timeout, TaskTimeoutError

        with pytest.raises(TaskTimeoutError):
            run_with_timeout(lambda: time.sleep(10), timeout_seconds=1)


class TestAsyncRunWithTimeout:
    @pytest.mark.asyncio
    async def test_succeeds_within_timeout(self):
        from lib.crewai.utilities.timeout_utils import async_run_with_timeout

        async def fast():
            return "done"

        result = await async_run_with_timeout(fast(), timeout_seconds=5)
        assert result == "done"

    @pytest.mark.asyncio
    async def test_raises_task_timeout_error(self):
        from lib.crewai.utilities.timeout_utils import async_run_with_timeout, TaskTimeoutError

        async def slow():
            await asyncio.sleep(10)

        with pytest.raises(TaskTimeoutError) as exc_info:
            await async_run_with_timeout(slow(), timeout_seconds=0.05, task_name="my_task")

        assert exc_info.value.task_name == "my_task"


class TestTaskTimeoutError:
    def test_message_includes_timeout(self):
        from lib.crewai.utilities.timeout_utils import TaskTimeoutError
        err = TaskTimeoutError(30.0, "research_task")
        assert "30.0s" in str(err)
        assert "research_task" in str(err)

    def test_message_without_task_name(self):
        from lib.crewai.utilities.timeout_utils import TaskTimeoutError
        err = TaskTimeoutError(10.0)
        assert "10.0s" in str(err)
