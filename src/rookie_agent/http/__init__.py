"""HTTP client module for Rookie Agent.

This module provides robust HTTP clients with support for:
- Synchronous and asynchronous requests
- Automatic retries with exponential backoff
- Comprehensive error handling
- SSE (Server-Sent Events) streaming
- Request/response logging

Examples:
    Synchronous usage:
    >>> from rookie_agent.http import HTTPClient
    >>> with HTTPClient() as client:
    ...     response = client.get("https://api.example.com/data")
    ...     print(response.json())

    Asynchronous usage:
    >>> import asyncio
    >>> from rookie_agent.http import AsyncHTTPClient
    >>> async def main():
    ...     async with AsyncHTTPClient() as client:
    ...         response = await client.get("https://api.example.com/data")
    ...         print(response.json())
    >>> asyncio.run(main())
"""

from rookie_agent.http.client import AsyncHTTPClient, HTTPClient
from rookie_agent.http.exceptions import (
    HTTPConnectionError,
    HTTPError,
    HTTPRequestError,
    HTTPStatusError,
    HTTPTimeoutError,
    RetryExhaustedError,
    SSEError,
)
from rookie_agent.http.retry import RetryConfig, retry_on_exception, async_retry_on_exception
from rookie_agent.http.streaming import SSEEvent, SSEParser, SSEStream, AsyncSSEStream
from rookie_agent.http.types import HTTPMethod, Headers, JSONData, QueryParams

__all__ = [
    # Clients
    "HTTPClient",
    "AsyncHTTPClient",
    # Exceptions
    "HTTPError",
    "HTTPRequestError",
    "HTTPTimeoutError",
    "HTTPConnectionError",
    "HTTPStatusError",
    "SSEError",
    "RetryExhaustedError",
    # Retry
    "RetryConfig",
    "retry_on_exception",
    "async_retry_on_exception",
    # Streaming
    "SSEEvent",
    "SSEParser",
    "SSEStream",
    "AsyncSSEStream",
    # Types
    "HTTPMethod",
    "Headers",
    "JSONData",
    "QueryParams",
]
