"""LLM-related exceptions.

This module defines the exception hierarchy for LLM operations,
following the error mapping strategy defined in the architecture document.

Exception Hierarchy:
    LLMError (base)
    ├── ConfigurationError (configuration issues)
    ├── LLMAPIError (API call errors)
    │   ├── AuthenticationError (401)
    │   ├── PermissionError (403)
    │   ├── NotFoundError (404)
    │   ├── RateLimitError (429)
    │   └── ServerError (5xx)
    ├── TokenLimitError (token quota exceeded)
    └── ContentFilterError (content filtered by model)
"""

from typing import Optional, Any, Dict
from rookie_agent.core.exceptions import RookieAgentError


class LLMError(RookieAgentError):
    """Base exception for all LLM-related errors.

    This is the parent class for all exceptions that can occur
    during LLM operations (configuration, API calls, etc.).
    """

    pass


class ConfigurationError(LLMError):
    """Configuration error.

    Raised when Provider configuration is invalid or incomplete.

    Examples:
        - Missing required API key
        - Invalid base URL format
        - Incompatible parameter combination
        - Model not supported by provider
    """

    pass


class LLMAPIError(LLMError):
    """Base class for API call errors.

    This exception captures errors returned by LLM APIs,
    including HTTP status codes and response bodies.

    Attributes:
        status_code: HTTP status code (if available)
        response_body: Response body text (if available)
        headers: Response headers (if available)
    """

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        """Initialize LLMAPIError.

        Args:
            message: Error message
            status_code: HTTP status code
            response_body: Response body text
            headers: Response headers
        """
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body
        self.headers = headers or {}

    def __str__(self) -> str:
        """String representation with status code."""
        if self.status_code:
            return f"[{self.status_code}] {super().__str__()}"
        return super().__str__()


class AuthenticationError(LLMAPIError):
    """Authentication error (HTTP 401).

    Raised when API key is invalid or missing.

    Common causes:
        - Invalid API key
        - Expired API key
        - Missing Authorization header
        - Wrong authentication format

    Resolution:
        - Check API key is correct
        - Verify API key has not expired
        - Ensure proper authentication header format
    """

    def __init__(
        self,
        message: str = "Authentication failed - invalid or missing API key",
        **kwargs: Any,
    ) -> None:
        super().__init__(message, status_code=401, **kwargs)


class PermissionError(LLMAPIError):
    """Permission error (HTTP 403).

    Raised when API key lacks required permissions.

    Common causes:
        - API key doesn't have access to requested model
        - Rate limit tier insufficient
        - Feature not enabled for account
        - Region/IP restrictions

    Resolution:
        - Check API key permissions
        - Verify account has access to model
        - Check if feature requires upgrade
    """

    def __init__(
        self,
        message: str = "Permission denied - insufficient access rights",
        **kwargs: Any,
    ) -> None:
        super().__init__(message, status_code=403, **kwargs)


class NotFoundError(LLMAPIError):
    """Resource not found error (HTTP 404).

    Raised when requested resource doesn't exist.

    Common causes:
        - Model name not found
        - Invalid endpoint URL
        - Deleted or renamed resource
        - Wrong API base URL

    Resolution:
        - Verify model name is correct
        - Check API endpoint URL
        - Ensure resource still exists
    """

    def __init__(
        self,
        message: str = "Resource not found",
        **kwargs: Any,
    ) -> None:
        super().__init__(message, status_code=404, **kwargs)


class RateLimitError(LLMAPIError):
    """Rate limit error (HTTP 429).

    Raised when API rate limit is exceeded.

    Attributes:
        retry_after: Suggested wait time in seconds before retry

    Common causes:
        - Too many requests in short time
        - Token quota exceeded
        - Concurrent request limit reached

    Resolution:
        - Wait for retry_after seconds
        - Implement exponential backoff
        - Reduce request frequency
        - Upgrade rate limit tier
    """

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize RateLimitError.

        Args:
            message: Error message
            retry_after: Suggested wait time in seconds
            **kwargs: Additional LLMAPIError arguments
        """
        super().__init__(message, status_code=429, **kwargs)
        self.retry_after = retry_after

    def __str__(self) -> str:
        """String representation with retry suggestion."""
        base = super().__str__()
        if self.retry_after:
            return f"{base} (retry after {self.retry_after}s)"
        return base


class ServerError(LLMAPIError):
    """Server error (HTTP 5xx).

    Raised when LLM service encounters internal errors.

    Common causes:
        - Service temporarily unavailable
        - Internal server error
        - Gateway timeout
        - Service overloaded

    Resolution:
        - Retry with exponential backoff
        - Check service status page
        - Wait for service recovery
    """

    def __init__(
        self,
        message: str = "LLM service error",
        **kwargs: Any,
    ) -> None:
        super().__init__(message, **kwargs)


class TokenLimitError(LLMError):
    """Token limit exceeded.

    Raised when input or output tokens exceed model limits.

    Attributes:
        token_count: Actual token count
        token_limit: Model's token limit
        token_type: Type of tokens (prompt/completion/total)

    Common causes:
        - Input text too long
        - Conversation history too long
        - Max tokens setting too high
        - Model context window exceeded

    Resolution:
        - Reduce input length
        - Truncate conversation history
        - Use model with larger context window
        - Split request into smaller chunks
    """

    def __init__(
        self,
        message: str,
        token_count: Optional[int] = None,
        token_limit: Optional[int] = None,
        token_type: str = "total",
    ) -> None:
        """Initialize TokenLimitError.

        Args:
            message: Error message
            token_count: Actual token count
            token_limit: Model's token limit
            token_type: Type of tokens (prompt/completion/total)
        """
        super().__init__(message)
        self.token_count = token_count
        self.token_limit = token_limit
        self.token_type = token_type

    def __str__(self) -> str:
        """String representation with token info."""
        base = super().__str__()
        if self.token_count and self.token_limit:
            return f"{base} ({self.token_count}/{self.token_limit} {self.token_type} tokens)"
        return base


class ContentFilterError(LLMError):
    """Content filter error.

    Raised when content is rejected by model's safety filters.

    Attributes:
        filter_type: Type of filter triggered (hate/violence/sexual/self-harm)
        content_snippet: Snippet of filtered content (for debugging)

    Common causes:
        - Content violates usage policies
        - Sensitive or harmful content detected
        - PII or copyrighted material
        - Jailbreak attempt detected

    Resolution:
        - Rephrase input to be more neutral
        - Remove sensitive content
        - Check content policy guidelines
        - Use different model if appropriate
    """

    def __init__(
        self,
        message: str = "Content rejected by safety filter",
        filter_type: Optional[str] = None,
        content_snippet: Optional[str] = None,
    ) -> None:
        """Initialize ContentFilterError.

        Args:
            message: Error message
            filter_type: Type of filter triggered
            content_snippet: Snippet of filtered content
        """
        super().__init__(message)
        self.filter_type = filter_type
        self.content_snippet = content_snippet

    def __str__(self) -> str:
        """String representation with filter info."""
        base = super().__str__()
        if self.filter_type:
            return f"{base} (filter: {self.filter_type})"
        return base


def map_http_error_to_llm_error(
    status_code: int,
    message: str,
    response_body: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None,
) -> LLMAPIError:
    """Map HTTP status code to appropriate LLM exception.

    This function implements the error mapping strategy from the
    architecture document (Section 13.3).

    Mapping:
        401 -> AuthenticationError
        403 -> PermissionError
        404 -> NotFoundError
        429 -> RateLimitError (with retry_after if available)
        5xx -> ServerError
        other -> LLMAPIError

    Args:
        status_code: HTTP status code
        message: Error message
        response_body: Response body text
        headers: Response headers

    Returns:
        Appropriate LLMAPIError subclass

    Examples:
        >>> error = map_http_error_to_llm_error(401, "Invalid API key")
        >>> isinstance(error, AuthenticationError)
        True

        >>> error = map_http_error_to_llm_error(429, "Too many requests")
        >>> isinstance(error, RateLimitError)
        True
    """
    headers = headers or {}

    # 401: Authentication error
    if status_code == 401:
        return AuthenticationError(
            message=message,
            response_body=response_body,
            headers=headers,
        )

    # 403: Permission error
    elif status_code == 403:
        return PermissionError(
            message=message,
            response_body=response_body,
            headers=headers,
        )

    # 404: Not found error
    elif status_code == 404:
        return NotFoundError(
            message=message,
            response_body=response_body,
            headers=headers,
        )

    # 429: Rate limit error (extract retry_after if available)
    elif status_code == 429:
        retry_after = None

        # Try to extract retry_after from headers
        if "retry-after" in headers:
            try:
                retry_after = int(headers["retry-after"])
            except (ValueError, TypeError):
                pass

        # Try to extract from x-ratelimit-reset (Unix timestamp)
        elif "x-ratelimit-reset" in headers:
            try:
                import time
                reset_time = int(headers["x-ratelimit-reset"])
                retry_after = max(0, reset_time - int(time.time()))
            except (ValueError, TypeError):
                pass

        return RateLimitError(
            message=message,
            retry_after=retry_after,
            response_body=response_body,
            headers=headers,
        )

    # 5xx: Server error
    elif 500 <= status_code < 600:
        return ServerError(
            message=message,
            status_code=status_code,
            response_body=response_body,
            headers=headers,
        )

    # Other: Generic API error
    else:
        return LLMAPIError(
            message=message,
            status_code=status_code,
            response_body=response_body,
            headers=headers,
        )
