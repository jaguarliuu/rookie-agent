"""Qwen (通义千问) Provider implementation.

阿里云通义千问使用DashScope API，提供OpenAI兼容的接口。

特点：
- OpenAI兼容API格式
- 支持流式响应
- 支持Function Calling（qwen-max/qwen-plus等模型）
- 支持联网搜索（enable_search参数）
- 国内访问速度快，性价比高

环境变量：
- DASHSCOPE_API_KEY: API密钥（必需）
- QWEN_MODEL: 默认模型（可选）
- QWEN_API_BASE: API地址（可选）

使用示例：
    >>> from rookie_agent.llm import QwenProvider, QwenConfig, Message, MessageRole
    >>>
    >>> # 从环境变量读取配置
    >>> provider = QwenProvider()
    >>>
    >>> # 或显式传入配置
    >>> config = QwenConfig(
    ...     api_key="sk-xxx",
    ...     model="qwen-max",
    ...     enable_search=True
    ... )
    >>> provider = QwenProvider(config)
    >>>
    >>> # 调用
    >>> messages = [Message(role=MessageRole.USER, content="你好")]
    >>> response = provider.chat(messages)
    >>> print(response.choices[0].message.content)
"""

import json
import logging
from typing import List, Optional, Iterator, AsyncIterator, Any

from rookie_agent.http import HTTPClient, AsyncHTTPClient, SSEStream, AsyncSSEStream
from rookie_agent.llm.base import BaseLLMProvider
from rookie_agent.llm.config import QwenConfig
from rookie_agent.llm.types import Message, ChatCompletion, CompletionChunk
from rookie_agent.llm.exceptions import (
    ConfigurationError,
    map_http_error_to_llm_error,
)

logger = logging.getLogger(__name__)


class QwenProvider(BaseLLMProvider):
    """Qwen (通义千问) LLM Provider.

    通义千问是阿里云推出的大语言模型，提供OpenAI兼容的API接口。

    支持的模型：
    - qwen-turbo: 快速响应，适合日常对话
    - qwen-plus: 平衡性能和成本
    - qwen-max: 最强性能，支持复杂任务
    - qwen-max-longcontext: 超长上下文支持

    特色功能：
    - 联网搜索：enable_search=True
    - Function Calling：支持工具调用
    - 流式输出：支持SSE流式响应

    Examples:
        基础使用：
        >>> config = QwenConfig(model="qwen-max")
        >>> provider = QwenProvider(config)
        >>> response = provider.chat([
        ...     Message(role=MessageRole.USER, content="介绍一下杭州")
        ... ])

        启用联网搜索：
        >>> response = provider.chat(messages, enable_search=True)

        流式输出：
        >>> for chunk in provider.stream(messages):
        ...     content = chunk.get_content()
        ...     if content:
        ...         print(content, end='', flush=True)
    """

    def __init__(self, config: Optional[QwenConfig] = None, **kwargs: Any):
        """Initialize Qwen provider.

        Args:
            config: Qwen配置对象。如果为None，会从kwargs或环境变量创建
            **kwargs: 配置参数，会传递给QwenConfig

        Examples:
            >>> # 方式1: 使用配置对象
            >>> config = QwenConfig(api_key="sk-xxx", model="qwen-max")
            >>> provider = QwenProvider(config)

            >>> # 方式2: 直接传参
            >>> provider = QwenProvider(model="qwen-turbo", temperature=0.8)

            >>> # 方式3: 从环境变量
            >>> provider = QwenProvider()  # 读取DASHSCOPE_API_KEY
        """
        if config is None:
            config = QwenConfig(**kwargs)
        super().__init__(config)

    def _validate_config(self) -> None:
        """验证Qwen配置。

        检查：
        1. API Key是否存在
        2. API Base是否有效
        3. 模型名称是否合理

        Raises:
            ConfigurationError: 配置无效时抛出
        """
        if not self.config.api_key:
            raise ConfigurationError(
                "Qwen API key is required. "
                "Set DASHSCOPE_API_KEY environment variable or pass api_key parameter."
            )

        if not self.config.api_base:
            raise ConfigurationError(
                "Qwen API base URL is required. "
                "This should not happen with default config."
            )

        logger.debug(
            f"Qwen config validated: model={self.config.model}, "
            f"base={self.config.api_base}"
        )

    def _setup_client(self) -> None:
        """设置HTTP客户端。

        配置：
        - Base URL: DashScope兼容模式端点
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

        logger.debug("Qwen HTTP client initialized")

    def _build_qwen_request(
        self,
        messages: List[Message],
        **kwargs: Any
    ) -> dict:
        """构建Qwen API请求。

        在基础请求的基础上添加Qwen特有参数。

        Args:
            messages: 消息列表
            **kwargs: 额外参数

        Returns:
            请求字典
        """
        # 使用基类方法构建基础请求
        request = self._build_chat_request(messages, **kwargs)

        # 添加Qwen特有参数
        if kwargs.get("enable_search") or self.config.enable_search:
            request["enable_search"] = True
            logger.debug("Qwen search enabled")

        # Qwen的repetition_penalty参数
        if hasattr(self.config, 'repetition_penalty') and self.config.repetition_penalty:
            request["repetition_penalty"] = self.config.repetition_penalty

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
                - enable_search: 是否启用联网搜索
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

            >>> # 启用搜索
            >>> response = provider.chat(messages, enable_search=True)

            >>> # 使用不同模型
            >>> response = provider.chat(messages, model="qwen-turbo")
        """
        logger.info(f"Qwen chat request: {len(messages)} messages")

        # 构建请求
        request_data = self._build_qwen_request(messages, **kwargs)

        try:
            # 发送请求
            response = self._client.post("/chat/completions", json=request_data)

            # 解析响应
            result = ChatCompletion(**response.json())

            logger.info(
                f"Qwen chat completed: "
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
        # 目前使用同步实现，后续优化为真正的异步
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
        logger.info(f"Qwen stream request: {len(messages)} messages")

        # 构建请求，强制启用流式
        request_data = self._build_qwen_request(messages, stream=True, **kwargs)

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

            logger.info(f"Qwen stream completed: {chunk_count} chunks")

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

        Qwen的部分模型支持Function Calling：
        - qwen-max: 支持
        - qwen-plus: 支持
        - qwen-turbo: 不支持

        Returns:
            是否支持Function Calling
        """
        model = self.config.model.lower()
        supported = "max" in model or "plus" in model
        return supported

    def get_available_models(self) -> List[str]:
        """获取可用的Qwen模型列表。

        Returns:
            模型名称列表
        """
        return [
            "qwen-turbo",
            "qwen-plus",
            "qwen-max",
            "qwen-max-longcontext",
        ]
