"""Retry logic for HTTP requests."""

import time
import random
import logging
from typing import Callable, Type, Tuple, Optional, Any
from functools import wraps

from rookie_agent.http.exceptions import RetryExhaustedError

logger = logging.getLogger(__name__)


class RetryConfig:
    """Configuration for retry behavior.

    This class encapsulates all retry-related configuration,
    following the Single Responsibility Principle.

    Examples:
        >>> config = RetryConfig(max_attempts=3, base_delay=1.0)
        >>> config.max_attempts
        3
    """

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retry_on: Tuple[Type[Exception], ...] = (Exception,),
    ) -> None:
        """Initialize retry configuration.

        Args:
            max_attempts: Maximum number of retry attempts
            base_delay: Base delay in seconds between retries
            max_delay: Maximum delay in seconds
            exponential_base: Base for exponential backoff
            jitter: Whether to add random jitter to delays
            retry_on: Tuple of exception types to retry on
        """
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retry_on = retry_on

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for a given attempt using exponential backoff.

        The formula is: min(max_delay, base_delay * (exponential_base ** attempt))
        With optional jitter: delay * (0.5 + random() * 0.5)

        Args:
            attempt: The attempt number (0-indexed)

        Returns:
            Delay in seconds

        Examples:
            >>> config = RetryConfig(base_delay=1.0, exponential_base=2.0)
            >>> config.calculate_delay(0)  # First retry
            1.0
            >>> config.calculate_delay(1)  # Second retry
            2.0
            >>> config.calculate_delay(2)  # Third retry
            4.0
        """
        # Exponential backoff
        delay = self.base_delay * (self.exponential_base**attempt)

        # Cap at max_delay
        delay = min(delay, self.max_delay)

        # Add jitter to prevent thundering herd
        if self.jitter:
            delay = delay * (0.5 + random.random() * 0.5)

        return delay

    def should_retry(self, exception: Exception) -> bool:
        """Check if an exception should trigger a retry.

        Args:
            exception: The exception that occurred

        Returns:
            True if should retry, False otherwise
        """
        return isinstance(exception, self.retry_on)


def retry_on_exception(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retry_on: Tuple[Type[Exception], ...] = (Exception,),
) -> Callable:
    """Decorator to retry a function on exception with exponential backoff.

    This decorator implements a robust retry mechanism with:
    - Exponential backoff
    - Jitter to prevent thundering herd
    - Configurable retry conditions
    - Detailed logging

    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Base delay in seconds between retries
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff
        jitter: Whether to add random jitter to delays
        retry_on: Tuple of exception types to retry on

    Returns:
        Decorated function

    Raises:
        RetryExhaustedError: When all retry attempts are exhausted

    Examples:
        >>> @retry_on_exception(max_attempts=3, base_delay=1.0)
        ... def unstable_function():
        ...     # Function that might fail
        ...     pass
    """
    config = RetryConfig(
        max_attempts=max_attempts,
        base_delay=base_delay,
        max_delay=max_delay,
        exponential_base=exponential_base,
        jitter=jitter,
        retry_on=retry_on,
    )

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception: Optional[Exception] = None

            for attempt in range(config.max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    # Check if we should retry this exception
                    if not config.should_retry(e):
                        logger.debug(
                            f"Not retrying {func.__name__} - "
                            f"exception type {type(e).__name__} not in retry_on"
                        )
                        raise

                    # Check if we have attempts left
                    if attempt >= config.max_attempts - 1:
                        logger.warning(
                            f"Retry exhausted for {func.__name__} "
                            f"after {config.max_attempts} attempts"
                        )
                        break

                    # Calculate delay and wait
                    delay = config.calculate_delay(attempt)
                    logger.info(
                        f"Retry {attempt + 1}/{config.max_attempts} "
                        f"for {func.__name__} after {delay:.2f}s - "
                        f"Error: {str(e)}"
                    )
                    time.sleep(delay)

            # If we get here, all retries were exhausted
            raise RetryExhaustedError(
                f"Failed after {config.max_attempts} attempts",
                attempts=config.max_attempts,
                last_exception=last_exception or Exception("Unknown error"),
            )

        return wrapper

    return decorator


def async_retry_on_exception(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retry_on: Tuple[Type[Exception], ...] = (Exception,),
) -> Callable:
    """Async version of retry decorator.

    Same as retry_on_exception but for async functions.

    IMPORTANT: This is a regular function (not async def) that returns
    a decorator. The decorator itself wraps async functions.

    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Base delay in seconds between retries
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff
        jitter: Whether to add random jitter to delays
        retry_on: Tuple of exception types to retry on

    Returns:
        Decorated async function

    Raises:
        RetryExhaustedError: When all retry attempts are exhausted

    Examples:
        >>> @async_retry_on_exception(max_attempts=3, base_delay=1.0)
        ... async def fetch_data():
        ...     # Async function that might fail
        ...     pass
    """
    import asyncio

    config = RetryConfig(
        max_attempts=max_attempts,
        base_delay=base_delay,
        max_delay=max_delay,
        exponential_base=exponential_base,
        jitter=jitter,
        retry_on=retry_on,
    )

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception: Optional[Exception] = None

            for attempt in range(config.max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    if not config.should_retry(e):
                        logger.debug(
                            f"Not retrying {func.__name__} - "
                            f"exception type {type(e).__name__} not in retry_on"
                        )
                        raise

                    if attempt >= config.max_attempts - 1:
                        logger.warning(
                            f"Retry exhausted for {func.__name__} "
                            f"after {config.max_attempts} attempts"
                        )
                        break

                    delay = config.calculate_delay(attempt)
                    logger.info(
                        f"Retry {attempt + 1}/{config.max_attempts} "
                        f"for {func.__name__} after {delay:.2f}s - "
                        f"Error: {str(e)}"
                    )
                    await asyncio.sleep(delay)

            raise RetryExhaustedError(
                f"Failed after {config.max_attempts} attempts",
                attempts=config.max_attempts,
                last_exception=last_exception or Exception("Unknown error"),
            )

        return wrapper

    return decorator
