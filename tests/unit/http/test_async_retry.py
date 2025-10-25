"""Tests for async retry decorator.

This test file specifically validates that the async_retry_on_exception
decorator is correctly implemented as a synchronous function that returns
an async decorator.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock

from rookie_agent.http.retry import async_retry_on_exception, RetryConfig
from rookie_agent.http.exceptions import RetryExhaustedError


class TestAsyncRetryDecorator:
    """Tests for async_retry_on_exception decorator."""

    @pytest.mark.asyncio
    async def test_decorator_is_not_coroutine(self):
        """Test that async_retry_on_exception returns a decorator, not a coroutine.

        This is a critical test that validates the fix for the decorator bug.
        The decorator factory function should be synchronous (def), not async (async def).
        """
        # Call the decorator factory
        decorator = async_retry_on_exception(max_attempts=3)

        # Verify it returns a function, not a coroutine
        assert callable(decorator), "Decorator factory should return a callable"
        assert not asyncio.iscoroutine(decorator), "Decorator factory should NOT return a coroutine"
        assert not asyncio.iscoroutinefunction(decorator), "Decorator factory should NOT be async"

    @pytest.mark.asyncio
    async def test_can_be_used_as_decorator_syntax(self):
        """Test that the decorator can be used with @ syntax.

        This test ensures the decorator works correctly when used with
        standard Python decorator syntax.
        """
        call_count = 0

        @async_retry_on_exception(max_attempts=3, base_delay=0.01)
        async def test_function():
            nonlocal call_count
            call_count += 1
            return "success"

        # The decorator should work without errors
        result = await test_function()

        assert result == "success"
        assert call_count == 1

        # Verify the decorated function is still async
        assert asyncio.iscoroutinefunction(test_function)

    @pytest.mark.asyncio
    async def test_successful_execution_no_retry(self):
        """Test that successful async function doesn't retry."""
        call_count = 0

        @async_retry_on_exception(max_attempts=3)
        async def successful_function():
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.001)
            return "success"

        result = await successful_function()

        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retry_on_exception(self):
        """Test that async function retries on exception."""
        call_count = 0

        @async_retry_on_exception(max_attempts=3, base_delay=0.01)
        async def failing_function():
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.001)
            if call_count < 3:
                raise ValueError("test error")
            return "success"

        result = await failing_function()

        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_retry_exhausted(self):
        """Test that RetryExhaustedError is raised when retries exhausted."""
        call_count = 0

        @async_retry_on_exception(max_attempts=3, base_delay=0.01)
        async def always_failing_function():
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.001)
            raise ValueError("test error")

        with pytest.raises(RetryExhaustedError) as exc_info:
            await always_failing_function()

        assert call_count == 3
        assert exc_info.value.attempts == 3
        assert isinstance(exc_info.value.last_exception, ValueError)

    @pytest.mark.asyncio
    async def test_no_retry_on_excluded_exception(self):
        """Test that function doesn't retry on non-retryable exceptions."""
        call_count = 0

        @async_retry_on_exception(
            max_attempts=3,
            retry_on=(ValueError,),
        )
        async def function_with_type_error():
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.001)
            raise TypeError("test error")

        with pytest.raises(TypeError):
            await function_with_type_error()

        assert call_count == 1

    @pytest.mark.asyncio
    async def test_async_sleep_is_used(self):
        """Test that asyncio.sleep is used instead of time.sleep.

        This ensures the retry mechanism doesn't block the event loop.
        """
        import time

        call_count = 0

        @async_retry_on_exception(max_attempts=2, base_delay=0.1, jitter=False)
        async def failing_once():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("fail once")
            return "success"

        start = time.time()
        result = await failing_once()
        elapsed = time.time() - start

        assert result == "success"
        assert call_count == 2
        # Should have slept ~0.1s, verify it's in reasonable range
        assert 0.05 < elapsed < 0.2, f"Expected ~0.1s sleep, got {elapsed}s"

    @pytest.mark.asyncio
    async def test_multiple_concurrent_retries(self):
        """Test that multiple async functions can retry concurrently."""

        @async_retry_on_exception(max_attempts=3, base_delay=0.01)
        async def task(task_id, fail_count):
            attempts = 0
            while attempts < fail_count:
                attempts += 1
                raise ValueError(f"Task {task_id} attempt {attempts}")
            return f"Task {task_id} success"

        # Run multiple tasks concurrently
        results = await asyncio.gather(
            task(1, fail_count=2),
            task(2, fail_count=1),
            task(3, fail_count=0),
        )

        assert results == [
            "Task 1 success",
            "Task 2 success",
            "Task 3 success",
        ]

    @pytest.mark.asyncio
    async def test_preserves_function_metadata(self):
        """Test that decorator preserves function name and docstring."""

        @async_retry_on_exception(max_attempts=3)
        async def my_function():
            """This is my function."""
            return "result"

        assert my_function.__name__ == "my_function"
        assert my_function.__doc__ == "This is my function."

    @pytest.mark.asyncio
    async def test_works_with_arguments(self):
        """Test that decorated function can accept arguments."""

        @async_retry_on_exception(max_attempts=3, base_delay=0.01)
        async def function_with_args(x, y, z=10):
            if x < 0:
                raise ValueError("x must be positive")
            return x + y + z

        # Test with valid arguments
        result = await function_with_args(1, 2, z=3)
        assert result == 6

        # Test with invalid arguments (should not retry ValueError)
        @async_retry_on_exception(
            max_attempts=3,
            retry_on=(ConnectionError,),  # Only retry ConnectionError
        )
        async def selective_retry(x):
            if x < 0:
                raise ValueError("negative")
            return x * 2

        with pytest.raises(ValueError):
            await selective_retry(-1)
