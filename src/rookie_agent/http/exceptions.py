"""HTTP-related exceptions for Rookie Agent."""

from typing import Optional

from rookie_agent.core.exceptions import RookieAgentError


class HTTPError(RookieAgentError):
    """Base exception for all HTTP-related errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None,
    ) -> None:
        """Initialize HTTP error.

        Args:
            message: Error message
            status_code: HTTP status code if available
            response_body: Response body if available
        """
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class HTTPRequestError(HTTPError):
    """Raised when an HTTP request fails."""

    pass


class HTTPTimeoutError(HTTPError):
    """Raised when an HTTP request times out."""

    pass


class HTTPConnectionError(HTTPError):
    """Raised when there is a connection error."""

    pass


class HTTPStatusError(HTTPError):
    """Raised when response has an error status code."""

    pass


class SSEError(HTTPError):
    """Raised when there is an SSE (Server-Sent Events) error."""

    pass


class RetryExhaustedError(HTTPError):
    """Raised when all retry attempts are exhausted."""

    def __init__(
        self,
        message: str,
        attempts: int,
        last_exception: Exception,
    ) -> None:
        """Initialize retry exhausted error.

        Args:
            message: Error message
            attempts: Number of attempts made
            last_exception: The last exception that occurred
        """
        super().__init__(message)
        self.attempts = attempts
        self.last_exception = last_exception
