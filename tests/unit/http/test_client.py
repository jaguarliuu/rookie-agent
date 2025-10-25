"""Tests for HTTP client."""

import pytest
from unittest.mock import Mock, patch
import httpx

from rookie_agent.http.client import HTTPClient, AsyncHTTPClient
from rookie_agent.http.exceptions import (
    HTTPTimeoutError,
    HTTPConnectionError,
    HTTPStatusError,
    HTTPRequestError,
)
from rookie_agent.http.types import HTTPMethod


class TestHTTPClient:
    """Tests for synchronous HTTP client."""

    def test_initialization(self):
        """Test HTTP client initialization."""
        client = HTTPClient(
            timeout=60.0,
            max_retries=5,
            base_url="https://api.example.com",
        )

        assert client.timeout == 60.0
        assert client.max_retries == 5
        assert client.base_url == "https://api.example.com"

    def test_context_manager(self):
        """Test HTTP client as context manager."""
        with HTTPClient() as client:
            assert client._client is not None

        # Client should be closed after context
        assert client._client.is_closed

    def test_merge_headers(self):
        """Test header merging."""
        default_headers = {"User-Agent": "TestAgent"}
        client = HTTPClient(default_headers=default_headers)

        # Request headers should override defaults
        request_headers = {"Authorization": "Bearer token"}
        merged = client._merge_headers(request_headers)

        assert merged["User-Agent"] == "TestAgent"
        assert merged["Authorization"] == "Bearer token"

        # Original headers should not be modified
        assert "Authorization" not in default_headers

    @patch("httpx.Client.request")
    def test_successful_get_request(self, mock_request):
        """Test successful GET request."""
        # Setup mock
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.content = b"test content"
        mock_response.text = "test content"
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response

        # Make request
        with HTTPClient() as client:
            response = client.get("https://api.example.com/data")

        # Assertions
        assert response.status_code == 200
        assert response.text == "test content"
        mock_request.assert_called_once()
        mock_response.raise_for_status.assert_called_once()

    @patch("httpx.Client.request")
    def test_successful_post_request(self, mock_request):
        """Test successful POST request with JSON body."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 201
        mock_response.content = b'{"id": 123}'
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response

        with HTTPClient() as client:
            response = client.post(
                "https://api.example.com/data",
                json={"key": "value"},
            )

        assert response.status_code == 201
        mock_request.assert_called_once()

        # Check that JSON was passed
        call_kwargs = mock_request.call_args[1]
        assert call_kwargs["json"] == {"key": "value"}

    @patch("httpx.Client.request")
    def test_get_with_params(self, mock_request):
        """Test GET request with query parameters."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.content = b"test"
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response

        with HTTPClient() as client:
            client.get(
                "https://api.example.com/search",
                params={"q": "test", "limit": 10},
            )

        call_kwargs = mock_request.call_args[1]
        assert call_kwargs["params"] == {"q": "test", "limit": 10}

    @patch("httpx.Client.request")
    def test_timeout_error(self, mock_request):
        """Test handling of timeout errors."""
        mock_request.side_effect = httpx.TimeoutException("Request timeout")

        with HTTPClient(timeout=5.0) as client:
            with pytest.raises(HTTPTimeoutError) as exc_info:
                client.get("https://api.example.com/data")

        assert "timed out" in str(exc_info.value).lower()

    @patch("httpx.Client.request")
    def test_connection_error(self, mock_request):
        """Test handling of connection errors."""
        mock_request.side_effect = httpx.ConnectError("Connection failed")

        with HTTPClient() as client:
            with pytest.raises(HTTPConnectionError) as exc_info:
                client.get("https://api.example.com/data")

        assert "connect" in str(exc_info.value).lower()

    @patch("httpx.Client.request")
    def test_http_status_error(self, mock_request):
        """Test handling of HTTP status errors."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Not found"

        error = httpx.HTTPStatusError(
            "404 error",
            request=Mock(),
            response=mock_response,
        )
        mock_request.side_effect = error

        with HTTPClient() as client:
            with pytest.raises(HTTPStatusError) as exc_info:
                client.get("https://api.example.com/data")

        assert exc_info.value.status_code == 404
        assert exc_info.value.response_body == "Not found"

    @patch("httpx.Client.request")
    def test_all_http_methods(self, mock_request):
        """Test all HTTP methods (GET, POST, PUT, DELETE)."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.content = b"success"
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response

        with HTTPClient() as client:
            # GET
            client.get("https://api.example.com/data")
            assert mock_request.call_args[0][0] == "GET"

            # POST
            client.post("https://api.example.com/data", json={"test": "data"})
            assert mock_request.call_args[0][0] == "POST"

            # PUT
            client.put("https://api.example.com/data/1", json={"test": "data"})
            assert mock_request.call_args[0][0] == "PUT"

            # DELETE
            client.delete("https://api.example.com/data/1")
            assert mock_request.call_args[0][0] == "DELETE"


@pytest.mark.asyncio
class TestAsyncHTTPClient:
    """Tests for asynchronous HTTP client."""

    async def test_initialization(self):
        """Test async HTTP client initialization."""
        client = AsyncHTTPClient(
            timeout=60.0,
            max_retries=5,
            base_url="https://api.example.com",
        )

        assert client.timeout == 60.0
        assert client.max_retries == 5
        assert client.base_url == "https://api.example.com"

        await client.close()

    async def test_context_manager(self):
        """Test async HTTP client as context manager."""
        async with AsyncHTTPClient() as client:
            assert client._client is not None

        # Client should be closed after context
        assert client._client.is_closed

    @patch("httpx.AsyncClient.request")
    async def test_successful_get_request(self, mock_request):
        """Test successful async GET request."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.content = b"test content"
        mock_response.text = "test content"
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response

        async with AsyncHTTPClient() as client:
            response = await client.get("https://api.example.com/data")

        assert response.status_code == 200
        assert response.text == "test content"

    @patch("httpx.AsyncClient.request")
    async def test_successful_post_request(self, mock_request):
        """Test successful async POST request."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 201
        mock_response.content = b'{"id": 123}'
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response

        async with AsyncHTTPClient() as client:
            response = await client.post(
                "https://api.example.com/data",
                json={"key": "value"},
            )

        assert response.status_code == 201

    @patch("httpx.AsyncClient.request")
    async def test_timeout_error(self, mock_request):
        """Test handling of async timeout errors."""
        mock_request.side_effect = httpx.TimeoutException("Request timeout")

        async with AsyncHTTPClient(timeout=5.0) as client:
            with pytest.raises(HTTPTimeoutError):
                await client.get("https://api.example.com/data")

    @patch("httpx.AsyncClient.request")
    async def test_connection_error(self, mock_request):
        """Test handling of async connection errors."""
        mock_request.side_effect = httpx.ConnectError("Connection failed")

        async with AsyncHTTPClient() as client:
            with pytest.raises(HTTPConnectionError):
                await client.get("https://api.example.com/data")
