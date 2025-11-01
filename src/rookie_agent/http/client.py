"""HTTP client implementation using httpx.

This module provides both synchronous and asynchronous HTTP clients
with support for retries, timeouts, and comprehensive error handling.
"""

import logging
from typing import Any, Dict, Optional, Union
from abc import ABC, abstractmethod

import httpx

from rookie_agent.http.exceptions import (
    HTTPConnectionError,
    HTTPRequestError,
    HTTPStatusError,
    HTTPTimeoutError,
)
from rookie_agent.http.retry import retry_on_exception
from rookie_agent.http.streaming import SSEStream, AsyncSSEStream
from rookie_agent.http.types import Headers, HTTPMethod, JSONData, QueryParams, Timeout

logger = logging.getLogger(__name__)


class BaseHTTPClient(ABC):
    """Base class for HTTP clients.

    This abstract base class defines the interface that all HTTP clients
    must implement, ensuring consistency across sync and async versions.
    """

    @abstractmethod
    def request(
        self,
        method: Union[str, HTTPMethod],
        url: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """Make an HTTP request.

        Args:
            method: HTTP method
            url: Request URL
            **kwargs: Additional request parameters

        Returns:
            HTTP response

        Raises:
            HTTPError: If request fails
        """
        pass

    @abstractmethod
    def get(
        self,
        url: str,
        params: Optional[QueryParams] = None,
        headers: Optional[Headers] = None,
        **kwargs: Any,
    ) -> httpx.Response:
        """Make a GET request."""
        pass

    @abstractmethod
    def post(
        self,
        url: str,
        json: Optional[JSONData] = None,
        data: Optional[Any] = None,
        headers: Optional[Headers] = None,
        **kwargs: Any,
    ) -> httpx.Response:
        """Make a POST request."""
        pass


class HTTPClient:
    """Synchronous HTTP client with retry and error handling.

    This class wraps httpx.Client and provides:
    - Automatic retries with exponential backoff
    - Comprehensive error handling
    - Request/response logging
    - Timeout configuration

    Examples:
        >>> client = HTTPClient(timeout=30.0)
        >>> response = client.get("https://api.example.com/data")
        >>> print(response.status_code)
        200

        >>> # With custom headers
        >>> headers = {"Authorization": "Bearer token"}
        >>> response = client.post(
        ...     "https://api.example.com/data",
        ...     json={"key": "value"},
        ...     headers=headers
        ... )
    """

    def __init__(
        self,
        timeout: Timeout = 30.0,
        max_retries: int = 3,
        base_url: Optional[str] = None,
        default_headers: Optional[Headers] = None,
        verify_ssl: bool = True,
    ) -> None:
        """Initialize HTTP client.

        Args:
            timeout: Default timeout in seconds
            max_retries: Maximum number of retry attempts
            base_url: Base URL for all requests
            default_headers: Default headers for all requests
            verify_ssl: Whether to verify SSL certificates
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.base_url = base_url
        self.default_headers = default_headers or {}
        self.verify_ssl = verify_ssl

        # Create httpx client
        self._client = httpx.Client(
            timeout=timeout,
            base_url=base_url,
            headers=default_headers,
            verify=verify_ssl,
        )

    def __enter__(self) -> "HTTPClient":
        """Context manager entry."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit."""
        self.close()

    def close(self) -> None:
        """Close the HTTP client and release resources."""
        self._client.close()

    def _merge_headers(self, headers: Optional[Headers]) -> Headers:
        """Merge request headers with default headers.

        Args:
            headers: Request-specific headers

        Returns:
            Merged headers dictionary
        """
        merged = self.default_headers.copy()
        if headers:
            merged.update(headers)
        return merged

    def _handle_httpx_error(self, error: Exception, url: str) -> None:
        """Convert httpx exceptions to our custom exceptions.

        This method centralizes error handling and provides clear,
        actionable error messages.

        Args:
            error: The httpx exception
            url: The request URL

        Raises:
            HTTPTimeoutError: On timeout
            HTTPConnectionError: On connection error
            HTTPStatusError: On HTTP error status
            HTTPRequestError: On other request errors
        """
        if isinstance(error, httpx.TimeoutException):
            raise HTTPTimeoutError(
                f"Request to {url} timed out after {self.timeout}s"
            ) from error
        elif isinstance(error, httpx.ConnectError):
            raise HTTPConnectionError(
                f"Failed to connect to {url}"
            ) from error
        elif isinstance(error, httpx.HTTPStatusError):
            raise HTTPStatusError(
                f"HTTP {error.response.status_code} error for {url}",
                status_code=error.response.status_code,
                response_body=error.response.text,
            ) from error
        elif isinstance(error, httpx.RequestError):
            raise HTTPRequestError(f"Request to {url} failed: {str(error)}") from error
        else:
            raise HTTPRequestError(f"Unexpected error for {url}: {str(error)}") from error

    @retry_on_exception(
        max_attempts=3,
        base_delay=1.0,
        retry_on=(HTTPConnectionError, HTTPTimeoutError),
    )
    def request(
        self,
        method: Union[str, HTTPMethod],
        url: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """Make an HTTP request with retry logic.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            **kwargs: Additional httpx request parameters

        Returns:
            HTTP response object

        Raises:
            HTTPError: On request failure after retries
        """
        method_str = method.value if isinstance(method, HTTPMethod) else method

        logger.debug(f"Making {method_str} request to {url}")

        try:
            response = self._client.request(method_str, url, **kwargs)
            response.raise_for_status()

            logger.debug(
                f"{method_str} {url} -> {response.status_code} "
                f"({len(response.content)} bytes)"
            )

            return response

        except Exception as e:
            logger.error(f"{method_str} {url} failed: {str(e)}")
            self._handle_httpx_error(e, url)
            raise  # This should never be reached due to _handle_httpx_error

    def get(
        self,
        url: str,
        params: Optional[QueryParams] = None,
        headers: Optional[Headers] = None,
        **kwargs: Any,
    ) -> httpx.Response:
        """Make a GET request.

        Args:
            url: Request URL
            params: Query parameters
            headers: Request headers
            **kwargs: Additional request parameters

        Returns:
            HTTP response
        """
        merged_headers = self._merge_headers(headers)
        return self.request(
            HTTPMethod.GET,
            url,
            params=params,
            headers=merged_headers,
            **kwargs,
        )

    def post(
        self,
        url: str,
        json: Optional[JSONData] = None,
        data: Optional[Any] = None,
        headers: Optional[Headers] = None,
        **kwargs: Any,
    ) -> httpx.Response:
        """Make a POST request.

        Args:
            url: Request URL
            json: JSON body
            data: Form data or raw body
            headers: Request headers
            **kwargs: Additional request parameters

        Returns:
            HTTP response
        """
        merged_headers = self._merge_headers(headers)
        return self.request(
            HTTPMethod.POST,
            url,
            json=json,
            data=data,
            headers=merged_headers,
            **kwargs,
        )

    def put(
        self,
        url: str,
        json: Optional[JSONData] = None,
        data: Optional[Any] = None,
        headers: Optional[Headers] = None,
        **kwargs: Any,
    ) -> httpx.Response:
        """Make a PUT request.

        Args:
            url: Request URL
            json: JSON body
            data: Form data or raw body
            headers: Request headers
            **kwargs: Additional request parameters

        Returns:
            HTTP response
        """
        merged_headers = self._merge_headers(headers)
        return self.request(
            HTTPMethod.PUT,
            url,
            json=json,
            data=data,
            headers=merged_headers,
            **kwargs,
        )

    def delete(
        self,
        url: str,
        headers: Optional[Headers] = None,
        **kwargs: Any,
    ) -> httpx.Response:
        """Make a DELETE request.

        Args:
            url: Request URL
            headers: Request headers
            **kwargs: Additional request parameters

        Returns:
            HTTP response
        """
        merged_headers = self._merge_headers(headers)
        return self.request(
            HTTPMethod.DELETE,
            url,
            headers=merged_headers,
            **kwargs,
        )

    def stream_request(
        self,
        method: Union[str, HTTPMethod],
        url: str,
        **kwargs: Any,
    ) -> SSEStream:
        """Make a streaming HTTP request for SSE.

        This method enables streaming mode for Server-Sent Events (SSE).
        Use this for streaming responses from LLM APIs.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            **kwargs: Additional httpx request parameters

        Returns:
            SSEStream object for iterating over events

        Examples:
            >>> with client.stream_request("POST", url, json=data) as stream:
            ...     for event in stream:
            ...         print(event.data)
        """
        method_str = method.value if isinstance(method, HTTPMethod) else method

        logger.debug(f"Making streaming {method_str} request to {url}")

        try:
            # Create streaming request
            # 不使用with，让SSEStream管理response的生命周期
            response = self._client.stream(method_str, url, **kwargs)
            response.__enter__()  # 手动进入上下文

            try:
                response.raise_for_status()

                logger.debug(
                    f"Streaming {method_str} {url} -> {response.status_code}"
                )

                return SSEStream(response)
            except Exception:
                # 如果raise_for_status失败，关闭response
                response.__exit__(None, None, None)
                raise

        except Exception as e:
            logger.error(f"Streaming {method_str} {url} failed: {str(e)}")
            self._handle_httpx_error(e, url)
            raise

    def stream_get(
        self,
        url: str,
        params: Optional[QueryParams] = None,
        headers: Optional[Headers] = None,
        **kwargs: Any,
    ) -> SSEStream:
        """Make a streaming GET request.

        Args:
            url: Request URL
            params: Query parameters
            headers: Request headers
            **kwargs: Additional request parameters

        Returns:
            SSEStream object

        Examples:
            >>> with client.stream_get(url) as stream:
            ...     for event in stream:
            ...         print(event.data)
        """
        merged_headers = self._merge_headers(headers)
        return self.stream_request(
            HTTPMethod.GET,
            url,
            params=params,
            headers=merged_headers,
            **kwargs,
        )

    def stream_post(
        self,
        url: str,
        json: Optional[JSONData] = None,
        data: Optional[Any] = None,
        headers: Optional[Headers] = None,
        **kwargs: Any,
    ) -> SSEStream:
        """Make a streaming POST request.

        Args:
            url: Request URL
            json: JSON body
            data: Form data or raw body
            headers: Request headers
            **kwargs: Additional request parameters

        Returns:
            SSEStream object

        Examples:
            >>> with client.stream_post(url, json={"prompt": "Hello"}) as stream:
            ...     for event in stream:
            ...         if not event.is_done:
            ...             print(event.data, end='')
        """
        merged_headers = self._merge_headers(headers)
        return self.stream_request(
            HTTPMethod.POST,
            url,
            json=json,
            data=data,
            headers=merged_headers,
            **kwargs,
        )


class AsyncHTTPClient:
    """Asynchronous HTTP client with retry and error handling.

    Similar to HTTPClient but uses async/await for non-blocking I/O.

    Examples:
        >>> import asyncio
        >>> async def main():
        ...     async with AsyncHTTPClient() as client:
        ...         response = await client.get("https://api.example.com/data")
        ...         print(response.status_code)
        >>> asyncio.run(main())
    """

    def __init__(
        self,
        timeout: Timeout = 30.0,
        max_retries: int = 3,
        base_url: Optional[str] = None,
        default_headers: Optional[Headers] = None,
        verify_ssl: bool = True,
    ) -> None:
        """Initialize async HTTP client.

        Args:
            timeout: Default timeout in seconds
            max_retries: Maximum number of retry attempts
            base_url: Base URL for all requests
            default_headers: Default headers for all requests
            verify_ssl: Whether to verify SSL certificates
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.base_url = base_url
        self.default_headers = default_headers or {}
        self.verify_ssl = verify_ssl

        self._client = httpx.AsyncClient(
            timeout=timeout,
            base_url=base_url,
            headers=default_headers,
            verify=verify_ssl,
        )

    async def __aenter__(self) -> "AsyncHTTPClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        await self.close()

    async def close(self) -> None:
        """Close the async HTTP client."""
        await self._client.aclose()

    def _merge_headers(self, headers: Optional[Headers]) -> Headers:
        """Merge request headers with default headers."""
        merged = self.default_headers.copy()
        if headers:
            merged.update(headers)
        return merged

    def _handle_httpx_error(self, error: Exception, url: str) -> None:
        """Convert httpx exceptions to our custom exceptions."""
        if isinstance(error, httpx.TimeoutException):
            raise HTTPTimeoutError(
                f"Request to {url} timed out after {self.timeout}s"
            ) from error
        elif isinstance(error, httpx.ConnectError):
            raise HTTPConnectionError(f"Failed to connect to {url}") from error
        elif isinstance(error, httpx.HTTPStatusError):
            raise HTTPStatusError(
                f"HTTP {error.response.status_code} error for {url}",
                status_code=error.response.status_code,
                response_body=error.response.text,
            ) from error
        elif isinstance(error, httpx.RequestError):
            raise HTTPRequestError(f"Request to {url} failed: {str(error)}") from error
        else:
            raise HTTPRequestError(f"Unexpected error for {url}: {str(error)}") from error

    async def request(
        self,
        method: Union[str, HTTPMethod],
        url: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """Make an async HTTP request.

        Args:
            method: HTTP method
            url: Request URL
            **kwargs: Additional request parameters

        Returns:
            HTTP response
        """
        method_str = method.value if isinstance(method, HTTPMethod) else method

        logger.debug(f"Making async {method_str} request to {url}")

        try:
            response = await self._client.request(method_str, url, **kwargs)
            response.raise_for_status()

            logger.debug(
                f"Async {method_str} {url} -> {response.status_code} "
                f"({len(response.content)} bytes)"
            )

            return response

        except Exception as e:
            logger.error(f"Async {method_str} {url} failed: {str(e)}")
            self._handle_httpx_error(e, url)
            raise

    async def get(
        self,
        url: str,
        params: Optional[QueryParams] = None,
        headers: Optional[Headers] = None,
        **kwargs: Any,
    ) -> httpx.Response:
        """Make an async GET request."""
        merged_headers = self._merge_headers(headers)
        return await self.request(
            HTTPMethod.GET,
            url,
            params=params,
            headers=merged_headers,
            **kwargs,
        )

    async def post(
        self,
        url: str,
        json: Optional[JSONData] = None,
        data: Optional[Any] = None,
        headers: Optional[Headers] = None,
        **kwargs: Any,
    ) -> httpx.Response:
        """Make an async POST request."""
        merged_headers = self._merge_headers(headers)
        return await self.request(
            HTTPMethod.POST,
            url,
            json=json,
            data=data,
            headers=merged_headers,
            **kwargs,
        )

    async def put(
        self,
        url: str,
        json: Optional[JSONData] = None,
        data: Optional[Any] = None,
        headers: Optional[Headers] = None,
        **kwargs: Any,
    ) -> httpx.Response:
        """Make an async PUT request."""
        merged_headers = self._merge_headers(headers)
        return await self.request(
            HTTPMethod.PUT,
            url,
            json=json,
            data=data,
            headers=merged_headers,
            **kwargs,
        )

    async def delete(
        self,
        url: str,
        headers: Optional[Headers] = None,
        **kwargs: Any,
    ) -> httpx.Response:
        """Make an async DELETE request."""
        merged_headers = self._merge_headers(headers)
        return await self.request(
            HTTPMethod.DELETE,
            url,
            headers=merged_headers,
            **kwargs,
        )

    async def stream_request(
        self,
        method: Union[str, HTTPMethod],
        url: str,
        **kwargs: Any,
    ) -> AsyncSSEStream:
        """Make an async streaming HTTP request for SSE.

        This method enables streaming mode for Server-Sent Events (SSE).
        Use this for streaming responses from LLM APIs.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            **kwargs: Additional httpx request parameters

        Returns:
            AsyncSSEStream object for iterating over events

        Examples:
            >>> async with client.stream_request("POST", url, json=data) as stream:
            ...     async for event in stream:
            ...         print(event.data)
        """
        method_str = method.value if isinstance(method, HTTPMethod) else method

        logger.debug(f"Making async streaming {method_str} request to {url}")

        try:
            # Create async streaming request
            # 不使用async with，让AsyncSSEStream管理response的生命周期
            response = self._client.stream(method_str, url, **kwargs)
            await response.__aenter__()  # 手动进入异步上下文

            try:
                response.raise_for_status()

                logger.debug(
                    f"Async streaming {method_str} {url} -> {response.status_code}"
                )

                return AsyncSSEStream(response)
            except Exception:
                # 如果raise_for_status失败，关闭response
                await response.__aexit__(None, None, None)
                raise

        except Exception as e:
            logger.error(f"Async streaming {method_str} {url} failed: {str(e)}")
            self._handle_httpx_error(e, url)
            raise

    async def stream_get(
        self,
        url: str,
        params: Optional[QueryParams] = None,
        headers: Optional[Headers] = None,
        **kwargs: Any,
    ) -> AsyncSSEStream:
        """Make an async streaming GET request.

        Args:
            url: Request URL
            params: Query parameters
            headers: Request headers
            **kwargs: Additional request parameters

        Returns:
            AsyncSSEStream object

        Examples:
            >>> async with client.stream_get(url) as stream:
            ...     async for event in stream:
            ...         print(event.data)
        """
        merged_headers = self._merge_headers(headers)
        return await self.stream_request(
            HTTPMethod.GET,
            url,
            params=params,
            headers=merged_headers,
            **kwargs,
        )

    async def stream_post(
        self,
        url: str,
        json: Optional[JSONData] = None,
        data: Optional[Any] = None,
        headers: Optional[Headers] = None,
        **kwargs: Any,
    ) -> AsyncSSEStream:
        """Make an async streaming POST request.

        Args:
            url: Request URL
            json: JSON body
            data: Form data or raw body
            headers: Request headers
            **kwargs: Additional request parameters

        Returns:
            AsyncSSEStream object

        Examples:
            >>> async with client.stream_post(url, json={"prompt": "Hello"}) as stream:
            ...     async for event in stream:
            ...         if not event.is_done:
            ...             print(event.data, end='')
        """
        merged_headers = self._merge_headers(headers)
        return await self.stream_request(
            HTTPMethod.POST,
            url,
            json=json,
            data=data,
            headers=merged_headers,
            **kwargs,
        )
