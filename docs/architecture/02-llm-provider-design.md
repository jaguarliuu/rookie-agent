# LLM Provider 架构设计文档

## 文档信息

- **作者**: Rookie Agent Team
- **日期**: 2025-10-26
- **版本**: v1.0
- **状态**: 设计阶段

---

## 1. 设计目标

### 1.1 核心目标

LLM Provider模块是AI Agent的核心能力，负责与各种大语言模型API进行交互。设计目标如下：

- **统一接口**: 提供一致的API接口，屏蔽不同LLM厂商的差异
- **易于扩展**: 方便添加新的LLM提供商
- **配置灵活**: 支持环境变量、配置文件、代码传参等多种配置方式
- **功能完整**: 支持同步/异步、流式/非流式、Function Calling等特性
- **类型安全**: 完整的类型注解和Pydantic验证
- **错误处理**: 统一的异常处理和重试机制
- **可观测**: 详细的日志和性能监控

### 1.2 支持的LLM提供商

| 提供商 | 优先级 | 特点 | API兼容性 |
|--------|--------|------|-----------|
| OpenAI | P0 | 业界标准，功能最全 | OpenAI API |
| Qwen (通义千问) | P0 | 国产模型，性价比高 | OpenAI-Compatible |
| DeepSeek | P0 | 开源模型，推理能力强 | OpenAI-Compatible |
| Ollama | P1 | 本地部署，隐私安全 | OpenAI-Compatible |
| Claude | P1 | Anthropic，对话能力强 | Claude API |

---

## 2. 架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                    Application Layer                    │
│                  (Agent, Tools, etc.)                    │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│              LLM Provider Interface                     │
│                (BaseLLMProvider)                        │
│  ┌──────────────────────────────────────────────────┐  │
│  │  - chat()           - achat()                    │  │
│  │  - stream()         - astream()                  │  │
│  │  - embed()          - aembed()                   │  │
│  │  - count_tokens()   - validate_config()          │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┴────────────┬─────────────┬────────────┬─────────────┐
        │                         │             │            │             │
┌───────▼────────┐  ┌─────────────▼──┐  ┌──────▼──────┐ ┌──▼──────┐ ┌───▼────────┐
│  OpenAI        │  │  Qwen          │  │  DeepSeek   │ │ Ollama  │ │  Claude    │
│  Provider      │  │  Provider      │  │  Provider   │ │Provider │ │  Provider  │
└───────┬────────┘  └─────────────┬──┘  └──────┬──────┘ └──┬──────┘ └───┬────────┘
        │                         │             │            │             │
        └────────────┬────────────┴─────────────┴────────────┴─────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                HTTP Client Layer                        │
│           (HTTPClient with Retry & Streaming)           │
└─────────────────────────────────────────────────────────┘
```

### 2.2 核心组件

#### 2.2.1 消息系统（Messages）

统一的消息格式，支持多模态内容：

```python
# 消息角色枚举
class MessageRole(str, Enum):
    SYSTEM = "system"      # 系统提示
    USER = "user"          # 用户输入
    ASSISTANT = "assistant"  # AI助手回复
    FUNCTION = "function"   # 函数调用结果（OpenAI旧格式）
    TOOL = "tool"          # 工具调用结果（OpenAI新格式）

# 消息内容类型
class ContentType(str, Enum):
    TEXT = "text"          # 纯文本
    IMAGE_URL = "image_url"  # 图片URL
    IMAGE_BASE64 = "image_base64"  # Base64编码图片

# 消息内容（多模态支持）
class MessageContent(BaseModel):
    type: ContentType
    text: Optional[str] = None
    image_url: Optional[str] = None
    image_base64: Optional[str] = None
    detail: Optional[str] = "auto"  # 图片分辨率：low/high/auto

# 统一消息格式
class Message(BaseModel):
    role: MessageRole
    content: Union[str, List[MessageContent]]  # 支持纯文本或多模态
    name: Optional[str] = None  # 消息发送者名称
    function_call: Optional[Dict[str, Any]] = None  # 函数调用（旧格式）
    tool_calls: Optional[List[Dict[str, Any]]] = None  # 工具调用（新格式）
```

#### 2.2.2 工具调用（Function/Tool Calling）

```python
# 函数/工具定义
class FunctionDefinition(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema格式

class ToolDefinition(BaseModel):
    type: Literal["function"] = "function"
    function: FunctionDefinition

# 工具调用请求
class ToolCall(BaseModel):
    id: str
    type: Literal["function"] = "function"
    function: Dict[str, Any]  # {name: str, arguments: str}

# 工具调用响应
class ToolResponse(BaseModel):
    tool_call_id: str
    role: Literal["tool"] = "tool"
    content: str
```

#### 2.2.3 配置系统（Configuration）

```python
# Provider配置基类
class ProviderConfig(BaseModel):
    """所有Provider的通用配置"""

    # API认证
    api_key: Optional[str] = None
    api_base: Optional[str] = None

    # 默认参数
    model: str
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    top_p: float = 1.0

    # 高级参数
    timeout: float = 60.0
    max_retries: int = 3
    stream: bool = False

    # 其他参数
    extra_headers: Optional[Dict[str, str]] = None
    extra_body: Optional[Dict[str, Any]] = None

    class Config:
        # 允许环境变量覆盖
        env_prefix = ""  # 子类覆盖

# OpenAI配置
class OpenAIConfig(ProviderConfig):
    model: str = "gpt-4"
    api_base: Optional[str] = "https://api.openai.com/v1"

    # OpenAI特有参数
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    seed: Optional[int] = None
    response_format: Optional[Dict[str, str]] = None

    class Config:
        env_prefix = "OPENAI_"

    @validator("api_key", pre=True, always=True)
    def set_api_key(cls, v):
        return v or os.getenv("OPENAI_API_KEY")

# Qwen配置
class QwenConfig(ProviderConfig):
    model: str = "qwen-turbo"
    api_base: Optional[str] = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    # Qwen特有参数
    enable_search: bool = False

    class Config:
        env_prefix = "QWEN_"

    @validator("api_key", pre=True, always=True)
    def set_api_key(cls, v):
        return v or os.getenv("DASHSCOPE_API_KEY")
```

#### 2.2.4 响应格式（Response）

```python
# 单次响应
class CompletionChoice(BaseModel):
    index: int
    message: Message
    finish_reason: Optional[str] = None  # stop/length/tool_calls/content_filter

class CompletionUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

class ChatCompletion(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[CompletionChoice]
    usage: CompletionUsage

# 流式响应块
class CompletionChunk(BaseModel):
    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    choices: List[Dict[str, Any]]  # delta格式
```

---

## 3. Provider基类设计

### 3.1 BaseLLMProvider接口

```python
from abc import ABC, abstractmethod
from typing import List, Optional, Union, Iterator, AsyncIterator

class BaseLLMProvider(ABC):
    """LLM Provider抽象基类

    所有LLM提供商必须实现此接口，确保API的一致性。

    设计原则：
    1. 统一接口：所有Provider提供相同的方法签名
    2. 同步/异步：每个方法都有对应的异步版本
    3. 流式/非流式：统一的流式响应处理
    4. 错误处理：统一的异常类型
    """

    def __init__(self, config: ProviderConfig):
        """初始化Provider

        Args:
            config: Provider配置对象
        """
        self.config = config
        self._validate_config()
        self._setup_client()

    @abstractmethod
    def _validate_config(self) -> None:
        """验证配置有效性

        Raises:
            ConfigurationError: 配置无效
        """
        pass

    @abstractmethod
    def _setup_client(self) -> None:
        """设置HTTP客户端"""
        pass

    # ==================== 聊天补全 ====================

    @abstractmethod
    def chat(
        self,
        messages: List[Message],
        **kwargs
    ) -> ChatCompletion:
        """同步聊天补全

        Args:
            messages: 消息列表
            **kwargs: 额外参数（model, temperature等）

        Returns:
            ChatCompletion对象

        Raises:
            LLMError: LLM调用失败
        """
        pass

    @abstractmethod
    async def achat(
        self,
        messages: List[Message],
        **kwargs
    ) -> ChatCompletion:
        """异步聊天补全"""
        pass

    # ==================== 流式响应 ====================

    @abstractmethod
    def stream(
        self,
        messages: List[Message],
        **kwargs
    ) -> Iterator[CompletionChunk]:
        """同步流式聊天

        Args:
            messages: 消息列表
            **kwargs: 额外参数

        Yields:
            CompletionChunk对象
        """
        pass

    @abstractmethod
    async def astream(
        self,
        messages: List[Message],
        **kwargs
    ) -> AsyncIterator[CompletionChunk]:
        """异步流式聊天"""
        pass

    # ==================== Embeddings ====================

    @abstractmethod
    def embed(
        self,
        texts: List[str],
        **kwargs
    ) -> List[List[float]]:
        """生成文本向量

        Args:
            texts: 文本列表
            **kwargs: 额外参数

        Returns:
            向量列表
        """
        pass

    @abstractmethod
    async def aembed(
        self,
        texts: List[str],
        **kwargs
    ) -> List[List[float]]:
        """异步生成文本向量"""
        pass

    # ==================== 工具方法 ====================

    @abstractmethod
    def count_tokens(
        self,
        messages: List[Message],
        model: Optional[str] = None
    ) -> int:
        """计算消息的token数

        Args:
            messages: 消息列表
            model: 模型名称（可选）

        Returns:
            Token数量
        """
        pass

    def supports_function_calling(self) -> bool:
        """是否支持Function Calling"""
        return False

    def supports_vision(self) -> bool:
        """是否支持视觉（图片）输入"""
        return False

    def supports_streaming(self) -> bool:
        """是否支持流式响应"""
        return True

    def get_available_models(self) -> List[str]:
        """获取可用的模型列表"""
        return []
```

---

## 4. 各Provider实现规范

### 4.1 OpenAI Provider

```python
class OpenAIProvider(BaseLLMProvider):
    """OpenAI官方API实现

    特点：
    - 最完整的功能支持
    - Function Calling和Tool Calling
    - Vision能力（GPT-4V）
    - 流式响应
    - JSON模式
    """

    def __init__(self, config: Optional[OpenAIConfig] = None, **kwargs):
        if config is None:
            config = OpenAIConfig(**kwargs)
        super().__init__(config)

    def _setup_client(self):
        self.client = HTTPClient(
            base_url=self.config.api_base,
            default_headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
            timeout=self.config.timeout,
        )

    def chat(self, messages: List[Message], **kwargs) -> ChatCompletion:
        # 构建请求
        request_data = self._build_chat_request(messages, **kwargs)

        # 发送请求
        response = self.client.post(
            "/chat/completions",
            json=request_data
        )

        # 解析响应
        return ChatCompletion(**response.json())

    def stream(self, messages: List[Message], **kwargs) -> Iterator[CompletionChunk]:
        request_data = self._build_chat_request(messages, stream=True, **kwargs)

        with self.client.stream_post("/chat/completions", json=request_data) as stream:
            for event in stream:
                if not event.is_done:
                    chunk = json.loads(event.data)
                    yield CompletionChunk(**chunk)

    def supports_function_calling(self) -> bool:
        return True

    def supports_vision(self) -> bool:
        return "gpt-4" in self.config.model and "vision" in self.config.model
```

### 4.2 Qwen Provider

```python
class QwenProvider(BaseLLMProvider):
    """阿里云通义千问实现

    特点：
    - OpenAI兼容API
    - 支持联网搜索
    - 高性价比
    - 国内访问速度快
    """

    def __init__(self, config: Optional[QwenConfig] = None, **kwargs):
        if config is None:
            config = QwenConfig(**kwargs)
        super().__init__(config)

    def _setup_client(self):
        self.client = HTTPClient(
            base_url=self.config.api_base,
            default_headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
            timeout=self.config.timeout,
        )

    def _build_chat_request(self, messages: List[Message], **kwargs):
        """构建Qwen特定的请求"""
        request = super()._build_chat_request(messages, **kwargs)

        # 添加Qwen特有参数
        if self.config.enable_search:
            request["enable_search"] = True

        return request

    def supports_function_calling(self) -> bool:
        # Qwen-Max支持Function Calling
        return "max" in self.config.model.lower()
```

### 4.3 DeepSeek Provider

```python
class DeepSeekProvider(BaseLLMProvider):
    """DeepSeek API实现

    特点：
    - OpenAI兼容API
    - 强大的推理能力
    - 开源模型
    - 高性价比
    """

    def __init__(self, config: Optional[DeepSeekConfig] = None, **kwargs):
        if config is None:
            config = DeepSeekConfig(**kwargs)
        super().__init__(config)

    def supports_function_calling(self) -> bool:
        return True
```

### 4.4 Ollama Provider

```python
class OllamaProvider(BaseLLMProvider):
    """Ollama本地部署实现

    特点：
    - OpenAI兼容API
    - 本地部署，数据隐私
    - 支持多种开源模型
    - 无需API Key
    """

    def __init__(self, config: Optional[OllamaConfig] = None, **kwargs):
        if config is None:
            config = OllamaConfig(**kwargs)
        super().__init__(config)

    def _validate_config(self):
        # Ollama不需要API Key
        if not self.config.api_base:
            self.config.api_base = "http://localhost:11434/v1"

    def get_available_models(self) -> List[str]:
        """获取本地已安装的模型列表"""
        response = self.client.get("/api/tags")
        models = response.json().get("models", [])
        return [m["name"] for m in models]
```

### 4.5 Claude Provider

```python
class ClaudeProvider(BaseLLMProvider):
    """Anthropic Claude实现

    特点：
    - 独特的API格式
    - 强大的对话能力
    - 长上下文支持
    - 需要特殊适配
    """

    def __init__(self, config: Optional[ClaudeConfig] = None, **kwargs):
        if config is None:
            config = ClaudeConfig(**kwargs)
        super().__init__(config)

    def _setup_client(self):
        self.client = HTTPClient(
            base_url=self.config.api_base or "https://api.anthropic.com",
            default_headers={
                "x-api-key": self.config.api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            timeout=self.config.timeout,
        )

    def _convert_messages_to_claude_format(self, messages: List[Message]):
        """将统一消息格式转换为Claude格式

        Claude要求：
        1. 必须以user消息开始
        2. user和assistant消息交替
        3. system消息单独处理
        """
        system = None
        claude_messages = []

        for msg in messages:
            if msg.role == MessageRole.SYSTEM:
                system = msg.content
            else:
                claude_messages.append({
                    "role": msg.role.value,
                    "content": msg.content
                })

        return system, claude_messages

    def chat(self, messages: List[Message], **kwargs) -> ChatCompletion:
        system, claude_messages = self._convert_messages_to_claude_format(messages)

        request_data = {
            "model": kwargs.get("model", self.config.model),
            "messages": claude_messages,
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens or 4096),
        }

        if system:
            request_data["system"] = system

        response = self.client.post("/v1/messages", json=request_data)

        # 转换Claude响应为统一格式
        return self._convert_claude_response(response.json())
```

---

## 5. 配置管理详细设计

### 5.1 配置优先级

配置来源的优先级（从高到低）：

1. **代码传参** - 最高优先级
2. **环境变量** - 中等优先级
3. **配置文件** - 较低优先级
4. **默认值** - 最低优先级

```python
# 示例：配置优先级
# 1. 默认值
config = OpenAIConfig()  # model="gpt-4", temperature=0.7

# 2. 环境变量
# OPENAI_API_KEY=sk-xxx
# OPENAI_MODEL=gpt-3.5-turbo
config = OpenAIConfig()  # 读取环境变量

# 3. 代码传参（覆盖前两者）
config = OpenAIConfig(
    model="gpt-4-turbo",
    temperature=0.9
)

# 4. 运行时参数（临时覆盖）
provider.chat(messages, model="gpt-3.5-turbo")
```

### 5.2 环境变量命名规范

```bash
# OpenAI
OPENAI_API_KEY=sk-xxx
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL=gpt-4
OPENAI_TEMPERATURE=0.7

# Qwen
DASHSCOPE_API_KEY=sk-xxx
QWEN_MODEL=qwen-max

# DeepSeek
DEEPSEEK_API_KEY=sk-xxx
DEEPSEEK_MODEL=deepseek-chat

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2

# Claude
ANTHROPIC_API_KEY=sk-ant-xxx
CLAUDE_MODEL=claude-3-opus-20240229
```

---

## 6. 错误处理

### 6.1 异常层次

```python
# 基础异常
class LLMError(RookieAgentError):
    """所有LLM相关错误的基类"""
    pass

# 配置错误
class ConfigurationError(LLMError):
    """配置错误"""
    pass

# API错误
class LLMAPIError(LLMError):
    """API调用错误"""
    def __init__(self, message, status_code=None, response_body=None):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body

# 认证错误
class AuthenticationError(LLMAPIError):
    """认证失败（401）"""
    pass

# 权限错误
class PermissionError(LLMAPIError):
    """权限不足（403）"""
    pass

# 资源不存在
class NotFoundError(LLMAPIError):
    """资源不存在（404）"""
    pass

# 速率限制
class RateLimitError(LLMAPIError):
    """速率限制（429）"""
    pass

# 服务器错误
class ServerError(LLMAPIError):
    """服务器错误（5xx）"""
    pass

# Token限制
class TokenLimitError(LLMError):
    """Token超出限制"""
    pass

# 内容过滤
class ContentFilterError(LLMError):
    """内容被过滤"""
    pass
```

### 6.2 错误处理策略

```python
def chat(self, messages: List[Message], **kwargs) -> ChatCompletion:
    try:
        response = self.client.post("/chat/completions", json=request_data)
        return ChatCompletion(**response.json())

    except HTTPStatusError as e:
        # 根据状态码转换为对应的LLM异常
        if e.status_code == 401:
            raise AuthenticationError("Invalid API key") from e
        elif e.status_code == 429:
            raise RateLimitError("Rate limit exceeded") from e
        elif e.status_code >= 500:
            raise ServerError("LLM service unavailable") from e
        else:
            raise LLMAPIError(f"API error: {e}") from e

    except HTTPTimeoutError as e:
        raise LLMAPIError("Request timeout") from e
```

---

## 7. 使用示例

### 7.1 基础使用

```python
from rookie_agent.llm import OpenAIProvider, Message, MessageRole

# 方式1：使用环境变量
provider = OpenAIProvider()

# 方式2：传入配置
provider = OpenAIProvider(
    api_key="sk-xxx",
    model="gpt-4",
    temperature=0.8
)

# 单次对话
messages = [
    Message(role=MessageRole.SYSTEM, content="你是一个有帮助的助手"),
    Message(role=MessageRole.USER, content="什么是量子计算？")
]

response = provider.chat(messages)
print(response.choices[0].message.content)
```

### 7.2 流式响应

```python
# 流式输出
for chunk in provider.stream(messages):
    if chunk.choices:
        delta = chunk.choices[0].get("delta", {})
        content = delta.get("content", "")
        if content:
            print(content, end="", flush=True)
```

### 7.3 Function Calling

```python
# 定义工具
tools = [
    ToolDefinition(
        type="function",
        function=FunctionDefinition(
            name="get_weather",
            description="获取指定城市的天气",
            parameters={
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "城市名称"}
                },
                "required": ["city"]
            }
        )
    )
]

# 调用
response = provider.chat(
    messages=[Message(role=MessageRole.USER, content="北京天气怎么样？")],
    tools=tools
)

# 检查是否需要调用工具
if response.choices[0].message.tool_calls:
    tool_call = response.choices[0].message.tool_calls[0]
    # 执行工具调用...
```

### 7.4 多Provider切换

```python
from rookie_agent.llm import ProviderFactory

# 工厂模式创建Provider
provider = ProviderFactory.create("openai")  # 从环境变量读取配置
# provider = ProviderFactory.create("qwen")
# provider = ProviderFactory.create("claude")

# 统一的接口调用
response = provider.chat(messages)
```

---

## 8. 性能优化

### 8.1 连接池复用

```python
# Provider内部维护HTTP客户端，自动复用连接
provider = OpenAIProvider()

# 多次调用复用同一个连接
for i in range(100):
    response = provider.chat(messages)
```

### 8.2 批量请求

```python
# 并发处理多个请求
import asyncio

async def batch_chat(provider, messages_list):
    tasks = [provider.achat(messages) for messages in messages_list]
    return await asyncio.gather(*tasks)

# 使用
results = asyncio.run(batch_chat(provider, [messages1, messages2, messages3]))
```

### 8.3 Token计数缓存

```python
# 缓存Token计数结果
from functools import lru_cache

@lru_cache(maxsize=1000)
def count_tokens(self, messages_hash: str, model: str) -> int:
    # 实际计算逻辑
    pass
```

---

## 9. 测试策略

### 9.1 单元测试

```python
# 模拟HTTP响应测试Provider逻辑
def test_openai_chat():
    mock_response = {
        "id": "chatcmpl-123",
        "choices": [{
            "message": {"role": "assistant", "content": "Hello!"}
        }],
        "usage": {"total_tokens": 10}
    }

    with patch.object(HTTPClient, 'post', return_value=mock_response):
        provider = OpenAIProvider(api_key="test")
        response = provider.chat(messages)
        assert response.choices[0].message.content == "Hello!"
```

### 9.2 集成测试

```python
# 真实API测试（需要API Key）
@pytest.mark.integration
def test_real_openai_api():
    provider = OpenAIProvider()  # 从环境变量读取
    messages = [Message(role=MessageRole.USER, content="Hi")]
    response = provider.chat(messages)
    assert response.choices[0].message.content
```

---

## 10. 文档要求

每个Provider需要提供：

1. **README**: 快速开始指南
2. **配置说明**: 环境变量、参数详解
3. **使用示例**: 常见场景代码示例
4. **API文档**: 完整的API参数说明
5. **故障排查**: 常见错误和解决方案

---

## 11. 开发计划

### Phase 1: 基础架构（Week 3）
- [ ] 设计统一消息格式
- [ ] 实现BaseLLMProvider基类
- [ ] 实现配置管理系统
- [ ] 实现异常体系

### Phase 2: OpenAI Provider（Week 3）
- [ ] 实现基础chat功能
- [ ] 实现流式响应
- [ ] 实现Function Calling
- [ ] 实现Token计数
- [ ] 编写单元测试

### Phase 3: 兼容Provider（Week 4）
- [ ] 实现Qwen Provider
- [ ] 实现DeepSeek Provider
- [ ] 实现Ollama Provider
- [ ] 编写集成测试

### Phase 4: Claude Provider（Week 4）
- [ ] 实现Claude适配
- [ ] 格式转换逻辑
- [ ] 测试验证

### Phase 5: 工厂模式与工具（Week 5）
- [ ] 实现ProviderFactory
- [ ] 实现Provider注册机制
- [ ] 实现Provider切换逻辑
- [ ] 性能优化

---

## 12. 总结

本设计文档定义了LLM Provider模块的完整架构，包括：

1. **统一抽象**: BaseLLMProvider提供一致的接口
2. **灵活配置**: 支持多种配置来源和优先级
3. **多Provider支持**: OpenAI、Qwen、DeepSeek、Ollama、Claude
4. **完整功能**: 同步/异步、流式/非流式、Function Calling
5. **健壮性**: 完善的错误处理和重试机制
6. **可扩展**: 易于添加新的Provider

下一步将开始实现具体代码。

---

## 13. 附录与细则

### 13.1 设计决策与非目标

- 统一契约：`chat/achat` 返回 `ChatCompletion`，`stream/astream` 返回统一的 `CompletionChunk`。
- 适配边界：Provider层负责字段/端点差异的适配；上层不感知各家差异。
- 重试边界：仅在连接建立/首包阶段使用重试；事件迭代过程不做自动重试。
- 非目标：会话记忆/对话策略、模型自动选择、复杂Prompt编排、缓存与LRU、长程任务编排。

### 13.2 流式与SSE解析规范

- 接口契约：`stream()/astream()` 迭代产出 `CompletionChunk`；保持事件顺序与幂等。
- 事件映射：`SSEStream/AsyncSSEStream` 解析 `event.data` JSON为 chunk；遇到`[DONE]`结束。
- 规范细节：
  - 冒号后的前导空格仅移除“一个”（`field: value` → `value`；`field:  value` 保留第二个空格）。
  - 字节行容忍：按UTF-8解码；非法字节忽略并记录日志；保留合法部分。
  - 注释与空行：`:`前无字段为注释行；空行触发flush；即使无尾部空行也需flush残留事件。
  - 无效行：忽略并以`DEBUG`级别记录，不中断流；解析失败时抛出异常终止。
- 合并策略：Provider层可选择合并`delta`为累积文本；若上层合并，则Provider需保证`delta`字段一致性与顺序。

### 13.3 错误处理策略细则

- 异常映射：
  - `401` → `AuthenticationError`；`403` → `PermissionError`；`404` → `NotFoundError`。
  - `429` → `RateLimitError`（含重试建议间隔）；`5xx` → `ServerError`；其它 → `LLMAPIError`。
- 重试策略：
  - 重试条件：连接错误、超时、`5xx`；不重试：`4xx`参数/认证错误。
  - 策略：指数退避+抖动（如`base=0.5s, factor=2, max=5`）；最大次数来自`config.max_retries`。
  - 流式边界：在`stream/astream`的响应迭代期间不自动重试，避免状态错乱；仅在启动/重连阶段重试。
- 稳定性增强：建议引入断路器（连续失败阈值触发短路一段时间）与全局速率限制（令牌桶）。

### 13.4 配置与安全

- 优先级：代码传参 > 环境变量 > 配置文件 > 默认值；运行时参数仅对本次调用生效。
- 冲突处理：明确“最终值”决策来源并记录到`DEBUG`日志；发生不兼容配置时抛`ConfigurationError`。
- 日志脱敏：API Key/PII不写日志；请求ID/TraceID贯穿HTTP Client与Provider层，便于追踪。
- Secrets管理：优先从环境读取或安全存储；缺失或格式错误时立即校验并失败。

### 13.5 取消与资源管理

- 同步：使用`with`管理流式连接，退出时自动关闭并释放资源。
- 异步：使用`async with`；支持任务取消（`asyncio.CancelledError`）时关闭响应、清理后台任务与缓冲。
- 资源泄露防护：在`finally`中确保关闭流与客户端；对异常路径做幂等关闭。

### 13.6 测试建议（流式/SSE）

- 单元测试：
  - 解析规范：单空格剥离、注释/空行处理、含冒号字段值、非法字节容忍、`[DONE]`终止、尾部无空行的flush。
  - 迭代语义：`SSEStream/AsyncSSEStream` 的同步/异步迭代，事件顺序与结束语义。
- 集成测试：
  - Provider层`stream/astream` 与SSE解析的组合；错误映射与重试边界验证。
- Mock层：
  - 可控的HTTPClient与SSE流伪造；必要的E2E基准以观察吞吐与延迟。
