"""Tests for retry logic."""

import pytest
import time

from rookie_agent.http.retry import RetryConfig, retry_on_exception
from rookie_agent.http.exceptions import RetryExhaustedError


class TestRetryConfig:
    """Tests for RetryConfig class."""

    def test_default_initialization(self):
        """Test default RetryConfig initialization."""
        config = RetryConfig()

        assert config.max_attempts == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 60.0
        assert config.exponential_base == 2.0
        assert config.jitter is True

    def test_custom_initialization(self):
        """Test RetryConfig with custom values."""
        config = RetryConfig(
            max_attempts=5,
            base_delay=0.5,
            max_delay=30.0,
            exponential_base=3.0,
            jitter=False,
        )

        assert config.max_attempts == 5
        assert config.base_delay == 0.5
        assert config.max_delay == 30.0
        assert config.exponential_base == 3.0
        assert config.jitter is False

    def test_calculate_delay_exponential_backoff(self):
        """Test exponential backoff delay calculation."""
        config = RetryConfig(
            base_delay=1.0,
            exponential_base=2.0,
            max_delay=100.0,
            jitter=False,  # Disable jitter for deterministic testing
        )

        # First retry: 1.0 * (2^0) = 1.0
        assert config.calculate_delay(0) == 1.0

        # Second retry: 1.0 * (2^1) = 2.0
        assert config.calculate_delay(1) == 2.0

        # Third retry: 1.0 * (2^2) = 4.0
        assert config.calculate_delay(2) == 4.0

        # Fourth retry: 1.0 * (2^3) = 8.0
        assert config.calculate_delay(3) == 8.0

    def test_calculate_delay_max_cap(self):
        """Test that delay is capped at max_delay."""
        config = RetryConfig(
            base_delay=1.0,
            exponential_base=2.0,
            max_delay=5.0,
            jitter=False,
        )

        # Large attempt number should be capped at max_delay
        assert config.calculate_delay(10) == 5.0

    def test_calculate_delay_with_jitter(self):
        """Test that jitter adds randomness to delay."""
        config = RetryConfig(
            base_delay=1.0,
            exponential_base=2.0,
            jitter=True,
        )

        # With jitter, delay should be between base_delay * 0.5 and base_delay
        delays = [config.calculate_delay(0) for _ in range(10)]

        # All delays should be within range
        for delay in delays:
            assert 0.5 <= delay <= 1.0

        # Delays should vary (not all the same)
        assert len(set(delays)) > 1

    def test_should_retry_default(self):
        """Test should_retry with default configuration."""
        config = RetryConfig()

        # Should retry on any exception by default
        assert config.should_retry(Exception("test"))
        assert config.should_retry(ValueError("test"))
        assert config.should_retry(RuntimeError("test"))

    def test_should_retry_specific_exceptions(self):
        """Test should_retry with specific exception types."""
        config = RetryConfig(retry_on=(ValueError, KeyError))

        # Should retry on specified exceptions
        assert config.should_retry(ValueError("test"))
        assert config.should_retry(KeyError("test"))

        # Should not retry on other exceptions
        assert not config.should_retry(RuntimeError("test"))
        assert not config.should_retry(TypeError("test"))


class TestRetryDecorator:
    """Tests for retry_on_exception decorator."""

    def test_successful_execution_no_retry(self):
        """Test that successful function doesn't retry."""
        call_count = 0

        @retry_on_exception(max_attempts=3)
        def successful_function():
            nonlocal call_count
            call_count += 1
            return "success"

        result = successful_function()

        assert result == "success"
        assert call_count == 1  # Called only once

    def test_retry_on_exception(self):
        """Test that function retries on exception."""
        call_count = 0

        @retry_on_exception(max_attempts=3, base_delay=0.01)  # Fast retry for testing
        def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("test error")
            return "success"

        result = failing_function()

        assert result == "success"
        assert call_count == 3  # Retried 2 times, succeeded on 3rd

    def test_retry_exhausted(self):
        """Test that RetryExhaustedError is raised when retries exhausted."""
        call_count = 0

        @retry_on_exception(max_attempts=3, base_delay=0.01)
        def always_failing_function():
            nonlocal call_count
            call_count += 1
            raise ValueError("test error")

        with pytest.raises(RetryExhaustedError) as exc_info:
            always_failing_function()

        assert call_count == 3
        assert exc_info.value.attempts == 3
        assert isinstance(exc_info.value.last_exception, ValueError)

    def test_no_retry_on_excluded_exception(self):
        """Test that function doesn't retry on non-retryable exceptions."""
        call_count = 0

        @retry_on_exception(
            max_attempts=3,
            retry_on=(ValueError,),  # Only retry on ValueError
        )
        def function_with_type_error():
            nonlocal call_count
            call_count += 1
            raise TypeError("test error")

        with pytest.raises(TypeError):
            function_with_type_error()

        assert call_count == 1  # No retry

    def test_retry_delay_increases(self):
        """Test that retry delay increases exponentially."""
        call_times = []

        @retry_on_exception(
            max_attempts=3,
            base_delay=0.1,
            jitter=False,
        )
        def function_that_fails():
            call_times.append(time.time())
            if len(call_times) < 3:
                raise ValueError("test")
            return "success"

        function_that_fails()

        # Check that delays are increasing
        if len(call_times) >= 3:
            delay1 = call_times[1] - call_times[0]
            delay2 = call_times[2] - call_times[1]

            # Second delay should be roughly 2x the first (exponential backoff)
            # Allow some tolerance for timing variations
            assert delay2 > delay1
            assert 0.05 <= delay1 <= 0.15  # Around 0.1s
            assert 0.15 <= delay2 <= 0.25  # Around 0.2s
