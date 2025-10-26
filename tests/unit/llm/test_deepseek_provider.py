"""Tests for DeepSeek Provider."""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock

from rookie_agent.llm.providers.deepseek import DeepSeekProvider
from rookie_agent.llm.config import DeepSeekConfig
from rookie_agent.llm.types import Message, MessageRole, ChatCompletion, CompletionChunk
from rookie_agent.llm.exceptions import (
    ConfigurationError,
    AuthenticationError,
    RateLimitError,
    ServerError,
)
from rookie_agent.http.streaming import SSEEvent, SSEStream


class TestDeepSeekProvider:
    """Tests for DeepSeek Provider."""

    def test_initialization_with_config(self):
        """Test initialization with DeepSeekConfig object."""
        config = DeepSeekConfig(
            api_key="test-key",
            model="deepseek-chat",
            temperature=0.8,
        )
        provider = DeepSeekProvider(config)

        assert provider.config.api_key == "test-key"
        assert provider.config.model == "deepseek-chat"
        assert provider.config.temperature == 0.8

    def test_initialization_with_kwargs(self):
        """Test initialization with keyword arguments."""
        provider = DeepSeekProvider(
            api_key="test-key",
            model="deepseek-coder",
            temperature=0.5,
        )

        assert provider.config.api_key == "test-key"
        assert provider.config.model == "deepseek-coder"
        assert provider.config.temperature == 0.5

    @patch.dict("os.environ", {"DEEPSEEK_API_KEY": "env-test-key"})
    def test_initialization_from_env(self):
        """Test initialization from environment variables."""
        provider = DeepSeekProvider()

        assert provider.config.api_key == "env-test-key"

    def test_validation_missing_api_key(self):
        """Test validation fails when API key is missing."""
        with pytest.raises(ConfigurationError, match="API key is required"):
            DeepSeekProvider(api_key="")

    def test_http_client_setup(self):
        """Test HTTP client is properly configured."""
        provider = DeepSeekProvider(api_key="test-key")

        assert provider._client is not None
        assert provider._client.base_url == "https://api.deepseek.com/v1"
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
            "model": "deepseek-chat",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "你好！我是DeepSeek，很高兴为您提供帮助。"
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 18,
                "total_tokens": 28
            }
        }
        mock_post.return_value = mock_response

        # Make request
        provider = DeepSeekProvider(api_key="test-key")
        messages = [Message(role=MessageRole.USER, content="你好")]
        response = provider.chat(messages)

        # Assertions
        assert isinstance(response, ChatCompletion)
        assert response.id == "chatcmpl-123"
        assert response.model == "deepseek-chat"
        assert len(response.choices) == 1
        assert response.choices[0].message.content == "你好！我是DeepSeek，很高兴为您提供帮助。"
        assert response.usage.total_tokens == 28

        # Verify API call
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == "/chat/completions"
        request_data = call_args[1]["json"]
        assert request_data["model"] == "deepseek-chat"
        assert len(request_data["messages"]) == 1

    @patch("rookie_agent.http.HTTPClient.post")
    def test_chat_with_coder_model(self, mock_post):
        """Test chat with deepseek-coder model."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "id": "chatcmpl-456",
            "object": "chat.completion",
            "created": 1677858242,
            "model": "deepseek-coder",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "```python\ndef quicksort(arr):\n    if len(arr) <= 1:\n        return arr\n```"
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {"prompt_tokens": 8, "completion_tokens": 25, "total_tokens": 33}
        }
        mock_post.return_value = mock_response

        provider = DeepSeekProvider(api_key="test-key", model="deepseek-coder")
        messages = [Message(role=MessageRole.USER, content="写一个快速排序")]

        response = provider.chat(messages)

        assert response.model == "deepseek-coder"
        assert "quicksort" in response.choices[0].message.content

    @patch("rookie_agent.http.HTTPClient.post")
    def test_chat_with_penalty_params(self, mock_post):
        """Test chat with DeepSeek-specific penalty parameters."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "id": "chatcmpl-789",
            "object": "chat.completion",
            "created": 1677858242,
            "model": "deepseek-chat",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": "测试响应"},
                    "finish_reason": "stop"
                }
            ],
            "usage": {"prompt_tokens": 5, "completion_tokens": 5, "total_tokens": 10}
        }
        mock_post.return_value = mock_response

        provider = DeepSeekProvider(api_key="test-key")
        messages = [Message(role=MessageRole.USER, content="测试")]

        # Use frequency and presence penalty
        response = provider.chat(
            messages,
            frequency_penalty=0.5,
            presence_penalty=0.3
        )

        # Check that penalties were included in request
        call_args = mock_post.call_args
        request_data = call_args[1]["json"]
        assert request_data.get("frequency_penalty") == 0.5
        assert request_data.get("presence_penalty") == 0.3

    @patch("rookie_agent.http.HTTPClient.post")
    def test_chat_with_override_params(self, mock_post):
        """Test chat with runtime parameter overrides."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "id": "chatcmpl-override",
            "object": "chat.completion",
            "created": 1677858242,
            "model": "deepseek-coder",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": "覆盖测试"},
                    "finish_reason": "stop"
                }
            ],
            "usage": {"prompt_tokens": 5, "completion_tokens": 5, "total_tokens": 10}
        }
        mock_post.return_value = mock_response

        provider = DeepSeekProvider(
            api_key="test-key",
            model="deepseek-chat",
            temperature=0.7
        )
        messages = [Message(role=MessageRole.USER, content="测试")]

        # Override model and temperature at runtime
        response = provider.chat(messages, model="deepseek-coder", temperature=0.2)

        # Check that overrides were used
        call_args = mock_post.call_args
        request_data = call_args[1]["json"]
        assert request_data["model"] == "deepseek-coder"
        assert request_data["temperature"] == 0.2

    @patch("rookie_agent.http.HTTPClient.post")
    def test_chat_authentication_error(self, mock_post):
        """Test chat handles authentication error."""
        # Simulate 401 error
        error = Exception("Unauthorized")
        error.status_code = 401
        error.response_body = "Invalid API key"
        error.headers = {}
        mock_post.side_effect = error

        provider = DeepSeekProvider(api_key="invalid-key")
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
        error.headers = {"retry-after": "30"}
        mock_post.side_effect = error

        provider = DeepSeekProvider(api_key="test-key")
        messages = [Message(role=MessageRole.USER, content="test")]

        with pytest.raises(RateLimitError) as exc_info:
            provider.chat(messages)

        assert exc_info.value.retry_after == 30

    @patch("rookie_agent.http.HTTPClient.post")
    def test_chat_server_error(self, mock_post):
        """Test chat handles server error."""
        # Simulate 500 error
        error = Exception("Internal server error")
        error.status_code = 500
        error.response_body = "Server error"
        error.headers = {}
        mock_post.side_effect = error

        provider = DeepSeekProvider(api_key="test-key")
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
                "model": "deepseek-chat",
                "choices": [
                    {
                        "index": 0,
                        "delta": {"role": "assistant", "content": "Deep"},
                        "finish_reason": None
                    }
                ]
            })),
            SSEEvent(data=json.dumps({
                "id": "chatcmpl-stream-1",
                "object": "chat.completion.chunk",
                "created": 1677858242,
                "model": "deepseek-chat",
                "choices": [
                    {
                        "index": 0,
                        "delta": {"content": "Seek"},
                        "finish_reason": None
                    }
                ]
            })),
            SSEEvent(data=json.dumps({
                "id": "chatcmpl-stream-1",
                "object": "chat.completion.chunk",
                "created": 1677858242,
                "model": "deepseek-chat",
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
        provider = DeepSeekProvider(api_key="test-key")
        messages = [Message(role=MessageRole.USER, content="你好")]

        chunks = list(provider.stream(messages))

        # Assertions
        assert len(chunks) == 3  # Excluding [DONE]
        assert all(isinstance(chunk, CompletionChunk) for chunk in chunks)
        assert chunks[0].get_content() == "Deep"
        assert chunks[1].get_content() == "Seek"
        assert chunks[2].is_done

        # Verify stream_post was called with stream=True
        call_args = mock_stream_post.call_args
        request_data = call_args[1]["json"]
        assert request_data["stream"] is True

    @patch("rookie_agent.http.HTTPClient.stream_post")
    def test_stream_coder_model(self, mock_stream_post):
        """Test streaming with deepseek-coder model."""
        sse_events = [
            SSEEvent(data=json.dumps({
                "id": "chatcmpl-stream-2",
                "object": "chat.completion.chunk",
                "created": 1677858242,
                "model": "deepseek-coder",
                "choices": [
                    {
                        "index": 0,
                        "delta": {"role": "assistant", "content": "def "},
                        "finish_reason": None
                    }
                ]
            })),
            SSEEvent(data=json.dumps({
                "id": "chatcmpl-stream-2",
                "object": "chat.completion.chunk",
                "created": 1677858242,
                "model": "deepseek-coder",
                "choices": [
                    {
                        "index": 0,
                        "delta": {"content": "hello():"},
                        "finish_reason": None
                    }
                ]
            })),
            SSEEvent(data=json.dumps({
                "id": "chatcmpl-stream-2",
                "object": "chat.completion.chunk",
                "created": 1677858242,
                "model": "deepseek-coder",
                "choices": [
                    {
                        "index": 0,
                        "delta": {"content": "\n    return 'world'"},
                        "finish_reason": "stop"
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

        provider = DeepSeekProvider(api_key="test-key", model="deepseek-coder")
        messages = [Message(role=MessageRole.USER, content="写一个hello函数")]

        # Collect full response
        full_response = ""
        for chunk in provider.stream(messages):
            content = chunk.get_content()
            if content:
                full_response += content

        assert "def hello():" in full_response
        assert "return 'world'" in full_response

    def test_supports_function_calling(self):
        """Test function calling support detection."""
        # All DeepSeek models support function calling
        provider_chat = DeepSeekProvider(api_key="test-key", model="deepseek-chat")
        assert provider_chat.supports_function_calling() is True

        provider_coder = DeepSeekProvider(api_key="test-key", model="deepseek-coder")
        assert provider_coder.supports_function_calling() is True

    def test_get_available_models(self):
        """Test getting available models list."""
        provider = DeepSeekProvider(api_key="test-key")
        models = provider.get_available_models()

        assert isinstance(models, list)
        assert len(models) > 0
        assert "deepseek-chat" in models
        assert "deepseek-coder" in models

    def test_context_manager(self):
        """Test provider as context manager."""
        with DeepSeekProvider(api_key="test-key") as provider:
            assert provider._client is not None

        # Client should be closed after context
        assert provider._client._client.is_closed

    def test_build_deepseek_request(self):
        """Test building DeepSeek-specific request."""
        provider = DeepSeekProvider(
            api_key="test-key",
            model="deepseek-chat",
            temperature=0.7,
        )
        messages = [
            Message(role=MessageRole.SYSTEM, content="You are a helpful assistant."),
            Message(role=MessageRole.USER, content="Hello"),
        ]

        request = provider._build_deepseek_request(messages)

        assert request["model"] == "deepseek-chat"
        assert request["temperature"] == 0.7
        assert len(request["messages"]) == 2
        assert request["messages"][0]["role"] == "system"
        assert request["messages"][1]["role"] == "user"

    def test_build_deepseek_request_with_penalties(self):
        """Test building request with frequency and presence penalties."""
        provider = DeepSeekProvider(api_key="test-key")
        messages = [Message(role=MessageRole.USER, content="测试")]

        request = provider._build_deepseek_request(
            messages,
            frequency_penalty=0.8,
            presence_penalty=0.6
        )

        assert request.get("frequency_penalty") == 0.8
        assert request.get("presence_penalty") == 0.6

    def test_multimodal_message_support(self):
        """Test support for multimodal messages."""
        from rookie_agent.llm.types import MessageContent, ContentType

        provider = DeepSeekProvider(api_key="test-key")
        messages = [
            Message(
                role=MessageRole.USER,
                content=[
                    MessageContent(type=ContentType.TEXT, text="分析这段代码"),
                    MessageContent(
                        type=ContentType.IMAGE_URL,
                        image_url="https://example.com/code.png"
                    ),
                ]
            )
        ]

        request = provider._build_deepseek_request(messages)

        assert len(request["messages"]) == 1
        assert isinstance(request["messages"][0]["content"], list)
        assert len(request["messages"][0]["content"]) == 2

    @patch("rookie_agent.http.HTTPClient.post")
    def test_chat_with_max_tokens(self, mock_post):
        """Test chat with max_tokens limit."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "id": "chatcmpl-max-tokens",
            "object": "chat.completion",
            "created": 1677858242,
            "model": "deepseek-chat",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": "简短回复"},
                    "finish_reason": "length"
                }
            ],
            "usage": {"prompt_tokens": 10, "completion_tokens": 100, "total_tokens": 110}
        }
        mock_post.return_value = mock_response

        provider = DeepSeekProvider(api_key="test-key")
        messages = [Message(role=MessageRole.USER, content="详细解释")]

        response = provider.chat(messages, max_tokens=100)

        # Check that max_tokens was sent
        call_args = mock_post.call_args
        request_data = call_args[1]["json"]
        assert request_data.get("max_tokens") == 100

        # Check finish reason
        assert response.choices[0].finish_reason == "length"
