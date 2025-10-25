"""Core exceptions for Rookie Agent."""


class RookieAgentError(Exception):
    """Base exception for all Rookie Agent errors."""

    def __init__(self, message: str, *args: object) -> None:
        """Initialize the exception.

        Args:
            message: Error message
            *args: Additional arguments
        """
        super().__init__(message, *args)
        self.message = message


class ConfigurationError(RookieAgentError):
    """Raised when there is a configuration error."""

    pass


class ExecutionError(RookieAgentError):
    """Raised when there is an execution error."""

    pass


class ValidationError(RookieAgentError):
    """Raised when there is a validation error."""

    pass


class RetryError(RookieAgentError):
    """Raised when retry attempts are exhausted."""

    def __init__(
        self, message: str, attempts: int, last_exception: Exception
    ) -> None:
        """Initialize the retry error.

        Args:
            message: Error message
            attempts: Number of retry attempts made
            last_exception: The last exception that occurred
        """
        super().__init__(message)
        self.attempts = attempts
        self.last_exception = last_exception
