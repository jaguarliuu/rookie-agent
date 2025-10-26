"""DeepSeek Provider implementation.

DeepSeek是一家提供强大推理能力的AI公司，API完全兼容OpenAI格式。

特点：
- OpenAI兼容API格式
- 支持流式响应
- 支持Function Calling
- 强大的代码和推理能力
- 性价比极高

环境变量：
- DEEPSEEK_API_KEY: API密钥（必需）
- DEEPSEEK_MODEL: 默认模型（可选）
- DEEPSEEK_API_BASE: API地址（可选）

使用示例：
    >>> from rookie_agent.llm import DeepSeekProvider, DeepSeekConfig, Message, MessageRole
    >>>
    >>> # 从环境变量读取配置
    >>> provider = DeepSeekProvider()
    >>>
    >>> # 或显式传入配置
    >>> config = DeepSeekConfig(
    ...     api_key="sk-xxx",
    ...     model="deepseek-chat"
    ... )
    >>> provider = DeepSeekProvider(config)
    >>>
    >>> # 调用
    >>> messages = [Message(role=MessageRole.USER, content="解释一下快速排序算法")]
    >>> response = provider.chat(messages)
    >>> print(response.choices[0].message.content)
"""

import json
import logging
from typing import List, Optional, Iterator, AsyncIterator, Any

from rookie_agent.http import HTTPClient, AsyncHTTPClient
from rookie_agent.llm.base import BaseLLMProvider
from rookie_agent.llm.config import DeepSeekConfig
from rookie_agent.llm.types import Message, ChatCompletion, CompletionChunk
from rookie_agent.llm.exceptions import (
    ConfigurationError,
    map_http_error_to_llm_error,
)

logger = logging.getLogger(__name__)


class DeepSeekProvider(BaseLLMProvider):
    """DeepSeek LLM Provider.

    DeepSeek提供强大的推理和代码能力，API完全兼容OpenAI格式。

    支持的模型：
    - deepseek-chat: 通用对话模型
    - deepseek-coder: 代码专用模型（强大的代码能力）

    特色功能：
    - 强大的推理能力
    - 优秀的代码生成和理解能力
    - Function Calling支持
    - 流式输出

    Examples:
        基础使用：
        >>> config = DeepSeekConfig(model="deepseek-chat")
        >>> provider = DeepSeekProvider(config)
        >>> response = provider.chat([
        ...     Message(role=MessageRole.USER, content="写一个快速排序")
        ... ])

        代码模型：
        >>> provider = DeepSeekProvider(model="deepseek-coder")
        >>> response = provider.chat(messages)

        流式输出：
        >>> for chunk in provider.stream(messages):
        ...     content = chunk.get_content()
        ...     if content:
        ...         print(content, end='', flush=True)
    """

    def __init__(self, config: Optional[DeepSeekConfig] = None, **kwargs: Any):
        """Initialize DeepSeek provider.

        Args:
            config: DeepSeek配置对象。如果为None，会从kwargs或环境变量创建
            **kwargs: 配置参数，会传递给DeepSeekConfig

        Examples:
            >>> # 方式1: 使用配置对象
            >>> config = DeepSeekConfig(api_key="sk-xxx", model="deepseek-chat")
            >>> provider = DeepSeekProvider(config)

            >>> # 方式2: 直接传参
            >>> provider = DeepSeekProvider(model="deepseek-coder", temperature=0.8)

            >>> # 方式3: 从环境变量
            >>> provider = DeepSeekProvider()  # 读取DEEPSEEK_API_KEY
        """
        if config is None:
            config = DeepSeekConfig(**kwargs)
        super().__init__(config)

    def _validate_config(self) -> None:
        """验证DeepSeek配置。

        检查：
        1. API Key是否存在
        2. API Base是否有效
        3. 模型名称是否合理

        Raises:
            ConfigurationError: 配置无效时抛出
        """
        if not self.config.api_key:
            raise ConfigurationError(
                "DeepSeek API key is required. "
                "Set DEEPSEEK_API_KEY environment variable or pass api_key parameter."
            )

        if not self.config.api_base:
            raise ConfigurationError(
                "DeepSeek API base URL is required. "
                "This should not happen with default config."
            )

        logger.debug(
            f"DeepSeek config validated: model={self.config.model}, "
            f"base={self.config.api_base}"
        )

    def _setup_client(self) -> None:
        """设置HTTP客户端。

        配置：
        - Base URL: DeepSeek API端点
        - Authorization: Bearer token格式
        - Timeout: 从配置读取
        - Retry: 从配置读取
        """
        self._client = HTTPClient(
            base_url=self.config.api_base,
            default_headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
            timeout=self.config.timeout,
            max_retries=self.config.max_retries,
        )

        logger.debug("DeepSeek HTTP client initialized")

    def _build_deepseek_request(
        self,
        messages: List[Message],
        **kwargs: Any
    ) -> dict:
        """构建DeepSeek API请求。

        在基础请求的基础上添加DeepSeek特有参数。

        Args:
            messages: 消息列表
            **kwargs: 额外参数

        Returns:
            请求字典
        """
        # 使用基类方法构建基础请求
        request = self._build_chat_request(messages, **kwargs)

        # 添加DeepSeek特有参数
        if hasattr(self.config, 'frequency_penalty'):
            request["frequency_penalty"] = kwargs.get(
                "frequency_penalty",
                self.config.frequency_penalty
            )

        if hasattr(self.config, 'presence_penalty'):
            request["presence_penalty"] = kwargs.get(
                "presence_penalty",
                self.config.presence_penalty
            )

        return request

    def chat(
        self,
        messages: List[Message],
        **kwargs: Any
    ) -> ChatCompletion:
        """同步聊天补全。

        Args:
            messages: 对话消息列表
            **kwargs: 可选参数
                - model: 覆盖默认模型
                - temperature: 覆盖温度
                - max_tokens: 最大token数
                - frequency_penalty: 频率惩罚（-2.0到2.0）
                - presence_penalty: 存在惩罚（-2.0到2.0）
                - tools: Function Calling工具列表

        Returns:
            ChatCompletion对象

        Raises:
            AuthenticationError: API Key无效
            RateLimitError: 超出速率限制
            LLMError: 其他API错误

        Examples:
            >>> response = provider.chat(messages)
            >>> print(response.choices[0].message.content)

            >>> # 使用代码模型
            >>> response = provider.chat(messages, model="deepseek-coder")

            >>> # 调整创造性
            >>> response = provider.chat(
            ...     messages,
            ...     temperature=1.0,
            ...     frequency_penalty=0.5
            ... )
        """
        logger.info(f"DeepSeek chat request: {len(messages)} messages")

        # 构建请求
        request_data = self._build_deepseek_request(messages, **kwargs)

        try:
            # 发送请求
            response = self._client.post("/chat/completions", json=request_data)

            # 解析响应
            result = ChatCompletion(**response.json())

            logger.info(
                f"DeepSeek chat completed: "
                f"{result.usage.total_tokens} tokens, "
                f"finish_reason={result.choices[0].finish_reason}"
            )

            return result

        except Exception as e:
            # HTTP异常转换为LLM异常
            if hasattr(e, 'status_code'):
                raise map_http_error_to_llm_error(
                    e.status_code,
                    str(e),
                    getattr(e, 'response_body', None),
                    getattr(e, 'headers', None)
                ) from e
            raise

    async def achat(
        self,
        messages: List[Message],
        **kwargs: Any
    ) -> ChatCompletion:
        """异步聊天补全。

        异步版本的chat()方法，参数和返回值相同。

        Args:
            messages: 对话消息列表
            **kwargs: 可选参数

        Returns:
            ChatCompletion对象

        Examples:
            >>> response = await provider.achat(messages)
            >>> print(response.choices[0].message.content)
        """
        # TODO: 实现异步版本
        logger.warning("Using sync implementation for async chat")
        return self.chat(messages, **kwargs)

    def stream(
        self,
        messages: List[Message],
        **kwargs: Any
    ) -> Iterator[CompletionChunk]:
        """同步流式聊天。

        逐块返回生成的内容，实现打字机效果。

        Args:
            messages: 对话消息列表
            **kwargs: 可选参数（同chat方法）

        Yields:
            CompletionChunk对象，包含增量内容

        Raises:
            LLMError: API错误

        Examples:
            >>> for chunk in provider.stream(messages):
            ...     content = chunk.get_content()
            ...     if content:
            ...         print(content, end='', flush=True)

            >>> # 收集完整响应
            >>> chunks = []
            >>> for chunk in provider.stream(messages):
            ...     chunks.append(chunk.get_content() or '')
            >>> full_response = ''.join(chunks)
        """
        logger.info(f"DeepSeek stream request: {len(messages)} messages")

        # 构建请求，强制启用流式
        request_data = self._build_deepseek_request(messages, stream=True, **kwargs)

        # 不使用with，因为生成器需要保持stream打开状态
        sse_stream = None
        try:
            # 发起流式请求
            sse_stream = self._client.stream_post(
                "/chat/completions",
                json=request_data
            )
            chunk_count = 0

            for event in sse_stream:
                # 跳过[DONE]事件
                if event.is_done:
                    logger.debug("Received [DONE] event")
                    break

                # 解析SSE数据
                try:
                    chunk_data = json.loads(event.data)
                    chunk = CompletionChunk(**chunk_data)
                    chunk_count += 1

                    yield chunk

                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse SSE data: {e}")
                    continue

            logger.info(f"DeepSeek stream completed: {chunk_count} chunks")

        except Exception as e:
            if hasattr(e, 'status_code'):
                raise map_http_error_to_llm_error(
                    e.status_code,
                    str(e),
                    getattr(e, 'response_body', None),
                    getattr(e, 'headers', None)
                ) from e
            raise
        finally:
            # 确保stream被正确关闭
            if sse_stream is not None:
                sse_stream.close()

    async def astream(
        self,
        messages: List[Message],
        **kwargs: Any
    ) -> AsyncIterator[CompletionChunk]:
        """异步流式聊天。

        异步版本的stream()方法。

        Args:
            messages: 对话消息列表
            **kwargs: 可选参数

        Yields:
            CompletionChunk对象

        Examples:
            >>> async for chunk in provider.astream(messages):
            ...     content = chunk.get_content()
            ...     if content:
            ...         print(content, end='', flush=True)
        """
        # TODO: 实现真正的异步流式
        logger.warning("Using sync implementation for async stream")
        for chunk in self.stream(messages, **kwargs):
            yield chunk

    def supports_function_calling(self) -> bool:
        """检查是否支持Function Calling。

        DeepSeek的所有模型都支持Function Calling。

        Returns:
            True
        """
        return True

    def get_available_models(self) -> List[str]:
        """获取可用的DeepSeek模型列表。

        Returns:
            模型名称列表
        """
        return [
            "deepseek-chat",
            "deepseek-coder",
        ]
