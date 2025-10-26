"""Base class for LLM providers.

This module defines the abstract base class that all LLM providers
must implement, ensuring a consistent API across different providers.

Design Principles:
1. Unified Interface: All providers expose the same methods
2. Sync/Async: Both synchronous and asynchronous versions
3. Streaming Support: Unified streaming response handling
4. Error Handling: Consistent exception types
5. Resource Management: Proper cleanup and context managers
"""

import logging
from abc import ABC, abstractmethod
from typing import List, Optional, Iterator, AsyncIterator, Dict, Any

from rookie_agent.http import HTTPClient, AsyncHTTPClient
from rookie_agent.llm.config import ProviderConfig
from rookie_agent.llm.types import (
    Message,
    ChatCompletion,
    CompletionChunk,
    ToolDefinition,
)
from rookie_agent.llm.exceptions import ConfigurationError, LLMError

logger = logging.getLogger(__name__)


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers.

    All LLM providers must inherit from this class and implement
    all abstract methods. This ensures API consistency across
    different providers (OpenAI, Qwen, DeepSeek, etc.).

    Lifecycle:
        1. __init__: Initialize with configuration
        2. _validate_config: Validate configuration
        3. _setup_client: Set up HTTP client
        4. Ready for chat/stream/embed calls
        5. close: Clean up resources (optional)

    Context Manager Support:
        Providers can be used with 'with' statement for automatic cleanup:
        >>> with OpenAIProvider(config) as provider:
        ...     response = provider.chat(messages)

    Examples:
        Synchronous usage:
        >>> config = OpenAIConfig(api_key="sk-xxx")
        >>> provider = OpenAIProvider(config)
        >>> messages = [Message(role=MessageRole.USER, content="Hello")]
        >>> response = provider.chat(messages)
        >>> print(response.choices[0].message.content)

        Streaming:
        >>> for chunk in provider.stream(messages):
        ...     content = chunk.get_content()
        ...     if content:
        ...         print(content, end='', flush=True)

        Asynchronous:
        >>> async with AsyncOpenAIProvider(config) as provider:
        ...     response = await provider.achat(messages)
        ...     print(response.choices[0].message.content)
    """

    def __init__(self, config: ProviderConfig):
        """Initialize provider with configuration.

        Args:
            config: Provider configuration object

        Raises:
            ConfigurationError: If configuration is invalid
        """
        self.config = config
        self._validate_config()
        self._setup_client()

        logger.info(
            f"Initialized {self.__class__.__name__} "
            f"(model={config.model}, base={config.api_base})"
        )

    # ==================== Abstract Methods ====================

    @abstractmethod
    def _validate_config(self) -> None:
        """Validate provider configuration.

        Check that all required configuration parameters are present
        and valid. Subclasses should call super()._validate_config()
        and add provider-specific validation.

        Raises:
            ConfigurationError: If configuration is invalid

        Examples:
            >>> def _validate_config(self):
            ...     super()._validate_config()
            ...     if not self.config.api_key:
            ...         raise ConfigurationError("API key required")
        """
        pass

    @abstractmethod
    def _setup_client(self) -> None:
        """Set up HTTP client for API requests.

        Initialize self._client with appropriate HTTPClient instance,
        configured with auth headers, base URL, timeout, etc.

        Examples:
            >>> def _setup_client(self):
            ...     self._client = HTTPClient(
            ...         base_url=self.config.api_base,
            ...         default_headers={
            ...             "Authorization": f"Bearer {self.config.api_key}"
            ...         },
            ...         timeout=self.config.timeout
            ...     )
        """
        pass

    # ==================== Chat Completion ====================

    @abstractmethod
    def chat(
        self,
        messages: List[Message],
        **kwargs: Any
    ) -> ChatCompletion:
        """Synchronous chat completion.

        Generate a completion for the given messages.

        Args:
            messages: List of conversation messages
            **kwargs: Optional parameters to override config
                - model: Override default model
                - temperature: Override temperature
                - max_tokens: Override max tokens
                - top_p: Override top_p
                - tools: List of tools/functions available
                - tool_choice: How to choose tools
                - ... (provider-specific parameters)

        Returns:
            ChatCompletion object with generated response

        Raises:
            LLMError: If request fails
            AuthenticationError: If API key is invalid
            RateLimitError: If rate limit exceeded
            TokenLimitError: If token limit exceeded

        Examples:
            >>> messages = [
            ...     Message(role=MessageRole.SYSTEM, content="You are helpful"),
            ...     Message(role=MessageRole.USER, content="Hello!")
            ... ]
            >>> response = provider.chat(messages)
            >>> print(response.choices[0].message.content)

            Override parameters:
            >>> response = provider.chat(
            ...     messages,
            ...     model="gpt-4-turbo",
            ...     temperature=0.9,
            ...     max_tokens=500
            ... )
        """
        pass

    @abstractmethod
    async def achat(
        self,
        messages: List[Message],
        **kwargs: Any
    ) -> ChatCompletion:
        """Asynchronous chat completion.

        Async version of chat(). Same parameters and behavior.

        Args:
            messages: List of conversation messages
            **kwargs: Optional parameters

        Returns:
            ChatCompletion object

        Raises:
            LLMError: If request fails

        Examples:
            >>> messages = [Message(role=MessageRole.USER, content="Hi")]
            >>> response = await provider.achat(messages)
            >>> print(response.choices[0].message.content)
        """
        pass

    # ==================== Streaming ====================

    @abstractmethod
    def stream(
        self,
        messages: List[Message],
        **kwargs: Any
    ) -> Iterator[CompletionChunk]:
        """Synchronous streaming chat.

        Stream completion chunks as they are generated.

        Args:
            messages: List of conversation messages
            **kwargs: Optional parameters

        Yields:
            CompletionChunk objects with delta content

        Raises:
            LLMError: If request fails

        Examples:
            >>> for chunk in provider.stream(messages):
            ...     content = chunk.get_content()
            ...     if content:
            ...         print(content, end='', flush=True)

            Collect full response:
            >>> full_content = []
            >>> for chunk in provider.stream(messages):
            ...     content = chunk.get_content()
            ...     if content:
            ...         full_content.append(content)
            >>> print(''.join(full_content))

        Note:
            Per architecture doc Section 13.2, streaming iterators
            should not automatically retry during iteration to avoid
            state corruption. Retry only at connection/init phase.
        """
        pass

    @abstractmethod
    async def astream(
        self,
        messages: List[Message],
        **kwargs: Any
    ) -> AsyncIterator[CompletionChunk]:
        """Asynchronous streaming chat.

        Async version of stream(). Same parameters and behavior.

        Args:
            messages: List of conversation messages
            **kwargs: Optional parameters

        Yields:
            CompletionChunk objects

        Raises:
            LLMError: If request fails

        Examples:
            >>> async for chunk in provider.astream(messages):
            ...     content = chunk.get_content()
            ...     if content:
            ...         print(content, end='', flush=True)
        """
        pass

    # ==================== Embeddings ====================

    def embed(
        self,
        texts: List[str],
        **kwargs: Any
    ) -> List[List[float]]:
        """Generate embeddings for texts.

        Default implementation raises NotImplementedError.
        Override in providers that support embeddings.

        Args:
            texts: List of texts to embed
            **kwargs: Optional parameters

        Returns:
            List of embedding vectors (each is List[float])

        Raises:
            NotImplementedError: If provider doesn't support embeddings
            LLMError: If request fails

        Examples:
            >>> vectors = provider.embed(["Hello", "World"])
            >>> len(vectors)
            2
            >>> len(vectors[0])  # Dimension depends on model
            1536
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} does not support embeddings"
        )

    async def aembed(
        self,
        texts: List[str],
        **kwargs: Any
    ) -> List[List[float]]:
        """Asynchronous embedding generation.

        Async version of embed(). Same parameters and behavior.

        Args:
            texts: List of texts to embed
            **kwargs: Optional parameters

        Returns:
            List of embedding vectors

        Raises:
            NotImplementedError: If provider doesn't support embeddings
            LLMError: If request fails
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} does not support embeddings"
        )

    # ==================== Utility Methods ====================

    def count_tokens(
        self,
        messages: List[Message],
        model: Optional[str] = None
    ) -> int:
        """Count tokens in messages.

        Default implementation provides rough estimation.
        Override in providers that have official token counting.

        Args:
            messages: Messages to count tokens for
            model: Model name (uses config.model if None)

        Returns:
            Estimated token count

        Examples:
            >>> messages = [Message(role=MessageRole.USER, content="Hello")]
            >>> count = provider.count_tokens(messages)
            >>> print(f"Estimated tokens: {count}")
        """
        # Rough estimation: ~4 characters per token
        total_chars = sum(
            len(str(msg.content)) for msg in messages
        )
        estimated_tokens = total_chars // 4

        logger.debug(
            f"Token estimation: ~{estimated_tokens} tokens "
            f"({total_chars} characters)"
        )

        return estimated_tokens

    def supports_function_calling(self) -> bool:
        """Check if provider supports function/tool calling.

        Returns:
            True if function calling is supported

        Examples:
            >>> if provider.supports_function_calling():
            ...     response = provider.chat(messages, tools=tools)
        """
        return False

    def supports_vision(self) -> bool:
        """Check if provider supports vision (image) inputs.

        Returns:
            True if vision is supported

        Examples:
            >>> if provider.supports_vision():
            ...     # Can include images in messages
            ...     pass
        """
        return False

    def supports_streaming(self) -> bool:
        """Check if provider supports streaming responses.

        Returns:
            True if streaming is supported
        """
        return True

    def get_available_models(self) -> List[str]:
        """Get list of available models for this provider.

        Default implementation returns empty list.
        Override in providers that can query available models.

        Returns:
            List of model names

        Examples:
            >>> models = provider.get_available_models()
            >>> print(f"Available models: {models}")
        """
        return []

    # ==================== Resource Management ====================

    def close(self) -> None:
        """Close the provider and release resources.

        Clean up HTTP client and any other resources.
        Called automatically when using context manager.

        Examples:
            >>> provider = OpenAIProvider(config)
            >>> try:
            ...     response = provider.chat(messages)
            ... finally:
            ...     provider.close()

            Or use context manager:
            >>> with OpenAIProvider(config) as provider:
            ...     response = provider.chat(messages)
        """
        if hasattr(self, '_client'):
            self._client.close()
            logger.debug(f"{self.__class__.__name__} closed")

    async def aclose(self) -> None:
        """Async close for async providers.

        Close async HTTP client and release resources.
        """
        if hasattr(self, '_client'):
            await self._client.aclose()
            logger.debug(f"{self.__class__.__name__} async closed")

    def __enter__(self) -> "BaseLLMProvider":
        """Context manager entry."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit."""
        self.close()

    async def __aenter__(self) -> "BaseLLMProvider":
        """Async context manager entry."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        await self.aclose()

    # ==================== Helper Methods ====================

    def _build_chat_request(
        self,
        messages: List[Message],
        **kwargs: Any
    ) -> Dict[str, Any]:
        """Build request payload for chat API.

        Helper method to construct the request body from messages
        and configuration. Merge config defaults with kwargs.

        Args:
            messages: Conversation messages
            **kwargs: Override parameters

        Returns:
            Request dictionary ready for JSON serialization

        Examples:
            >>> request = self._build_chat_request(
            ...     messages,
            ...     temperature=0.9,
            ...     max_tokens=500
            ... )
            >>> response = self._client.post("/chat/completions", json=request)
        """
        # Convert messages to API format
        request_messages = [msg.to_dict() for msg in messages]

        # Build request with config defaults
        request: Dict[str, Any] = {
            "model": kwargs.get("model", self.config.model),
            "messages": request_messages,
            "temperature": kwargs.get("temperature", self.config.temperature),
            "top_p": kwargs.get("top_p", self.config.top_p),
        }

        # Optional parameters
        max_tokens = kwargs.get("max_tokens", self.config.max_tokens)
        if max_tokens:
            request["max_tokens"] = max_tokens

        stream = kwargs.get("stream", self.config.stream)
        if stream:
            request["stream"] = True

        # Tools/functions
        tools = kwargs.get("tools")
        if tools:
            request["tools"] = [
                tool.dict() if hasattr(tool, 'dict') else tool
                for tool in tools
            ]

            tool_choice = kwargs.get("tool_choice")
            if tool_choice:
                request["tool_choice"] = tool_choice

        # Add extra body parameters if specified
        if self.config.extra_body:
            request.update(self.config.extra_body)

        return request
