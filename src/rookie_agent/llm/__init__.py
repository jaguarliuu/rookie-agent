"""LLM Provider module for Rookie Agent.

This module provides unified interfaces for interacting with various
Large Language Model providers (OpenAI, Qwen, DeepSeek, Ollama, Claude).

Key Features:
- Unified API across different LLM providers
- Synchronous and asynchronous support
- Streaming and non-streaming responses
- Function/Tool calling support
- Comprehensive error handling
- Flexible configuration management

Examples:
    Basic usage:
    >>> from rookie_agent.llm import OpenAIProvider, Message, MessageRole
    >>> provider = OpenAIProvider(api_key="sk-xxx")
    >>> messages = [Message(role=MessageRole.USER, content="Hello!")]
    >>> response = provider.chat(messages)
    >>> print(response.choices[0].message.content)

    Streaming:
    >>> for chunk in provider.stream(messages):
    ...     print(chunk.choices[0].delta.get("content", ""), end="")
"""

from rookie_agent.llm.exceptions import (
    LLMError,
    ConfigurationError,
    LLMAPIError,
    AuthenticationError,
    PermissionError,
    NotFoundError,
    RateLimitError,
    ServerError,
    TokenLimitError,
    ContentFilterError,
    map_http_error_to_llm_error,
)
from rookie_agent.llm.types import (
    MessageRole,
    ContentType,
    FinishReason,
    MessageContent,
    Message,
    FunctionDefinition,
    ToolDefinition,
    ToolCall,
    CompletionUsage,
    CompletionChoice,
    ChatCompletion,
    CompletionChunk,
)
from rookie_agent.llm.config import (
    ProviderConfig,
    OpenAIConfig,
    QwenConfig,
    DeepSeekConfig,
    OllamaConfig,
    ClaudeConfig,
)
from rookie_agent.llm.base import BaseLLMProvider
from rookie_agent.llm.providers import QwenProvider, DeepSeekProvider

__all__ = [
    # Exceptions
    "LLMError",
    "ConfigurationError",
    "LLMAPIError",
    "AuthenticationError",
    "PermissionError",
    "NotFoundError",
    "RateLimitError",
    "ServerError",
    "TokenLimitError",
    "ContentFilterError",
    "map_http_error_to_llm_error",
    # Types
    "MessageRole",
    "ContentType",
    "FinishReason",
    "MessageContent",
    "Message",
    "FunctionDefinition",
    "ToolDefinition",
    "ToolCall",
    "CompletionUsage",
    "CompletionChoice",
    "ChatCompletion",
    "CompletionChunk",
    # Configuration
    "ProviderConfig",
    "OpenAIConfig",
    "QwenConfig",
    "DeepSeekConfig",
    "OllamaConfig",
    "ClaudeConfig",
    # Base Provider
    "BaseLLMProvider",
    # Providers
    "QwenProvider",
    "DeepSeekProvider",
]
