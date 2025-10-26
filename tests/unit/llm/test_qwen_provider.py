"""Tests for Qwen Provider."""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Iterator

from rookie_agent.llm.providers.qwen import QwenProvider
from rookie_agent.llm.config import QwenConfig
from rookie_agent.llm.types import Message, MessageRole, ChatCompletion, CompletionChunk
from rookie_agent.llm.exceptions import (
    ConfigurationError,
    AuthenticationError,
    RateLimitError,
    ServerError,
)
from rookie_agent.http.streaming import SSEEvent, SSEStream


class TestQwenProvider:
    """Tests for Qwen Provider."""

    def test_initialization_with_config(self):
        """Test initialization with QwenConfig object."""
        config = QwenConfig(
            api_key="test-key",
            model="qwen-max",
            temperature=0.8,
        )
        provider = QwenProvider(config)

        assert provider.config.api_key == "test-key"
        assert provider.config.model == "qwen-max"
        assert provider.config.temperature == 0.8

    def test_initialization_with_kwargs(self):
        """Test initialization with keyword arguments."""
        provider = QwenProvider(
            api_key="test-key",
            model="qwen-turbo",
            temperature=0.5,
        )

        assert provider.config.api_key == "test-key"
        assert provider.config.model == "qwen-turbo"
        assert provider.config.temperature == 0.5

    @patch.dict("os.environ", {"DASHSCOPE_API_KEY": "env-test-key"})
    def test_initialization_from_env(self):
        """Test initialization from environment variables."""
        provider = QwenProvider()

        assert provider.config.api_key == "env-test-key"

    def test_validation_missing_api_key(self):
        """Test validation fails when API key is missing."""
        with pytest.raises(ConfigurationError, match="API key is required"):
            QwenProvider(api_key="")

    def test_http_client_setup(self):
        """Test HTTP client is properly configured."""
        provider = QwenProvider(api_key="test-key")

        assert provider._client is not None
        assert provider._client.base_url == "https://dashscope.aliyuncs.com/compatible-mode/v1"
        assert "Authorization" in provider._client.default_headers
        assert provider._client.default_headers["Authorization"] == "Bearer test-key"

    @patch("rookie_agent.http.HTTPClient.post")
    def test_chat_success(self, mock_post):
        """Test successful chat completion."""
        # Setup mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            "id": "chatcmpl-123",
            "object": "chat.completion",
            "created": 1677858242,
            "model": "qwen-max",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "你好！我是通义千问，很高兴为您服务。"
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 15,
                "total_tokens": 25
            }
        }
        mock_post.return_value = mock_response

        # Make request
        provider = QwenProvider(api_key="test-key")
        messages = [Message(role=MessageRole.USER, content="你好")]
        response = provider.chat(messages)

        # Assertions
        assert isinstance(response, ChatCompletion)
        assert response.id == "chatcmpl-123"
        assert response.model == "qwen-max"
        assert len(response.choices) == 1
        assert response.choices[0].message.content == "你好！我是通义千问，很高兴为您服务。"
        assert response.usage.total_tokens == 25

        # Verify API call
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == "/chat/completions"
        request_data = call_args[1]["json"]
        assert request_data["model"] == "qwen-max"
        assert len(request_data["messages"]) == 1

    @patch("rookie_agent.http.HTTPClient.post")
    def test_chat_with_override_params(self, mock_post):
        """Test chat with runtime parameter overrides."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "id": "chatcmpl-456",
            "object": "chat.completion",
            "created": 1677858242,
            "model": "qwen-turbo",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": "快速响应"},
                    "finish_reason": "stop"
                }
            ],
            "usage": {"prompt_tokens": 5, "completion_tokens": 8, "total_tokens": 13}
        }
        mock_post.return_value = mock_response

        provider = QwenProvider(api_key="test-key", model="qwen-max", temperature=0.7)
        messages = [Message(role=MessageRole.USER, content="测试")]

        # Override model and temperature at runtime
        response = provider.chat(messages, model="qwen-turbo", temperature=0.3)

        # Check that overrides were used
        call_args = mock_post.call_args
        request_data = call_args[1]["json"]
        assert request_data["model"] == "qwen-turbo"
        assert request_data["temperature"] == 0.3

    @patch("rookie_agent.http.HTTPClient.post")
    def test_chat_with_enable_search(self, mock_post):
        """Test chat with Qwen-specific enable_search parameter."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "id": "chatcmpl-789",
            "object": "chat.completion",
            "created": 1677858242,
            "model": "qwen-max",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": "根据搜索结果..."},
                    "finish_reason": "stop"
                }
            ],
            "usage": {"prompt_tokens": 20, "completion_tokens": 30, "total_tokens": 50}
        }
        mock_post.return_value = mock_response

        provider = QwenProvider(api_key="test-key")
        messages = [Message(role=MessageRole.USER, content="今天杭州天气怎么样")]

        # Enable search
        response = provider.chat(messages, enable_search=True)

        # Check that enable_search was included
        call_args = mock_post.call_args
        request_data = call_args[1]["json"]
        assert request_data.get("enable_search") is True

    @patch("rookie_agent.http.HTTPClient.post")
    def test_chat_authentication_error(self, mock_post):
        """Test chat handles authentication error."""
        # Simulate 401 error
        error = Exception("Unauthorized")
        error.status_code = 401
        error.response_body = "Invalid API key"
        error.headers = {}
        mock_post.side_effect = error

        provider = QwenProvider(api_key="invalid-key")
        messages = [Message(role=MessageRole.USER, content="test")]

        with pytest.raises(AuthenticationError):
            provider.chat(messages)

    @patch("rookie_agent.http.HTTPClient.post")
    def test_chat_rate_limit_error(self, mock_post):
        """Test chat handles rate limit error."""
        # Simulate 429 error
        error = Exception("Too many requests")
        error.status_code = 429
        error.response_body = "Rate limit exceeded"
        error.headers = {"retry-after": "60"}
        mock_post.side_effect = error

        provider = QwenProvider(api_key="test-key")
        messages = [Message(role=MessageRole.USER, content="test")]

        with pytest.raises(RateLimitError) as exc_info:
            provider.chat(messages)

        assert exc_info.value.retry_after == 60

    @patch("rookie_agent.http.HTTPClient.post")
    def test_chat_server_error(self, mock_post):
        """Test chat handles server error."""
        # Simulate 500 error
        error = Exception("Internal server error")
        error.status_code = 500
        error.response_body = "Server error"
        error.headers = {}
        mock_post.side_effect = error

        provider = QwenProvider(api_key="test-key")
        messages = [Message(role=MessageRole.USER, content="test")]

        with pytest.raises(ServerError):
            provider.chat(messages)

    @patch("rookie_agent.http.HTTPClient.stream_post")
    def test_stream_success(self, mock_stream_post):
        """Test successful streaming chat."""
        # Create mock SSE events
        sse_events = [
            SSEEvent(data=json.dumps({
                "id": "chatcmpl-stream-1",
                "object": "chat.completion.chunk",
                "created": 1677858242,
                "model": "qwen-max",
                "choices": [
                    {
                        "index": 0,
                        "delta": {"role": "assistant", "content": "你"},
                        "finish_reason": None
                    }
                ]
            })),
            SSEEvent(data=json.dumps({
                "id": "chatcmpl-stream-1",
                "object": "chat.completion.chunk",
                "created": 1677858242,
                "model": "qwen-max",
                "choices": [
                    {
                        "index": 0,
                        "delta": {"content": "好"},
                        "finish_reason": None
                    }
                ]
            })),
            SSEEvent(data=json.dumps({
                "id": "chatcmpl-stream-1",
                "object": "chat.completion.chunk",
                "created": 1677858242,
                "model": "qwen-max",
                "choices": [
                    {
                        "index": 0,
                        "delta": {},
                        "finish_reason": "stop"
                    }
                ]
            })),
            SSEEvent(data="[DONE]"),
        ]

        # Create mock SSEStream
        mock_stream = MagicMock(spec=SSEStream)
        mock_stream.__enter__.return_value = mock_stream
        mock_stream.__exit__.return_value = None
        mock_stream.__iter__.return_value = iter(sse_events)
        mock_stream_post.return_value = mock_stream

        # Make streaming request
        provider = QwenProvider(api_key="test-key")
        messages = [Message(role=MessageRole.USER, content="你好")]

        chunks = list(provider.stream(messages))

        # Assertions
        assert len(chunks) == 3  # Excluding [DONE]
        assert all(isinstance(chunk, CompletionChunk) for chunk in chunks)
        assert chunks[0].get_content() == "你"
        assert chunks[1].get_content() == "好"
        assert chunks[2].is_done

        # Verify stream_post was called with stream=True
        call_args = mock_stream_post.call_args
        request_data = call_args[1]["json"]
        assert request_data["stream"] is True

    @patch("rookie_agent.http.HTTPClient.stream_post")
    def test_stream_collect_full_response(self, mock_stream_post):
        """Test collecting full response from stream."""
        sse_events = [
            SSEEvent(data=json.dumps({
                "id": "chatcmpl-stream-2",
                "object": "chat.completion.chunk",
                "created": 1677858242,
                "model": "qwen-max",
                "choices": [
                    {
                        "index": 0,
                        "delta": {"role": "assistant", "content": "通"},
                        "finish_reason": None
                    }
                ]
            })),
            SSEEvent(data=json.dumps({
                "id": "chatcmpl-stream-2",
                "object": "chat.completion.chunk",
                "created": 1677858242,
                "model": "qwen-max",
                "choices": [
                    {
                        "index": 0,
                        "delta": {"content": "义"},
                        "finish_reason": None
                    }
                ]
            })),
            SSEEvent(data=json.dumps({
                "id": "chatcmpl-stream-2",
                "object": "chat.completion.chunk",
                "created": 1677858242,
                "model": "qwen-max",
                "choices": [
                    {
                        "index": 0,
                        "delta": {"content": "千问"},
                        "finish_reason": None
                    }
                ]
            })),
            SSEEvent(data="[DONE]"),
        ]

        mock_stream = MagicMock(spec=SSEStream)
        mock_stream.__enter__.return_value = mock_stream
        mock_stream.__exit__.return_value = None
        mock_stream.__iter__.return_value = iter(sse_events)
        mock_stream_post.return_value = mock_stream

        provider = QwenProvider(api_key="test-key")
        messages = [Message(role=MessageRole.USER, content="你是谁")]

        # Collect full response
        full_response = ""
        for chunk in provider.stream(messages):
            content = chunk.get_content()
            if content:
                full_response += content

        assert full_response == "通义千问"

    def test_supports_function_calling(self):
        """Test function calling support detection."""
        # qwen-max supports function calling
        provider_max = QwenProvider(api_key="test-key", model="qwen-max")
        assert provider_max.supports_function_calling() is True

        # qwen-plus supports function calling
        provider_plus = QwenProvider(api_key="test-key", model="qwen-plus")
        assert provider_plus.supports_function_calling() is True

        # qwen-turbo doesn't support function calling
        provider_turbo = QwenProvider(api_key="test-key", model="qwen-turbo")
        assert provider_turbo.supports_function_calling() is False

    def test_get_available_models(self):
        """Test getting available models list."""
        provider = QwenProvider(api_key="test-key")
        models = provider.get_available_models()

        assert isinstance(models, list)
        assert len(models) > 0
        assert "qwen-max" in models
        assert "qwen-plus" in models
        assert "qwen-turbo" in models
        assert "qwen-max-longcontext" in models

    def test_context_manager(self):
        """Test provider as context manager."""
        with QwenProvider(api_key="test-key") as provider:
            assert provider._client is not None

        # Client should be closed after context
        assert provider._client._client.is_closed

    def test_build_qwen_request(self):
        """Test building Qwen-specific request."""
        provider = QwenProvider(
            api_key="test-key",
            model="qwen-max",
            temperature=0.7,
            enable_search=False,
        )
        messages = [
            Message(role=MessageRole.SYSTEM, content="You are helpful."),
            Message(role=MessageRole.USER, content="Hello"),
        ]

        request = provider._build_qwen_request(messages)

        assert request["model"] == "qwen-max"
        assert request["temperature"] == 0.7
        assert len(request["messages"]) == 2
        assert request["messages"][0]["role"] == "system"
        assert request["messages"][1]["role"] == "user"

    def test_build_qwen_request_with_search(self):
        """Test building request with enable_search."""
        provider = QwenProvider(api_key="test-key", enable_search=True)
        messages = [Message(role=MessageRole.USER, content="今天天气")]

        request = provider._build_qwen_request(messages)

        assert request.get("enable_search") is True

    def test_multimodal_message_support(self):
        """Test support for multimodal messages."""
        from rookie_agent.llm.types import MessageContent, ContentType

        provider = QwenProvider(api_key="test-key")
        messages = [
            Message(
                role=MessageRole.USER,
                content=[
                    MessageContent(type=ContentType.TEXT, text="这是什么图片？"),
                    MessageContent(
                        type=ContentType.IMAGE_URL,
                        image_url="https://example.com/image.jpg"
                    ),
                ]
            )
        ]

        request = provider._build_qwen_request(messages)

        assert len(request["messages"]) == 1
        assert isinstance(request["messages"][0]["content"], list)
        assert len(request["messages"][0]["content"]) == 2
