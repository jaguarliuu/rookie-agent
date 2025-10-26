# LLM基础架构深度解析：从设计到实现

## 文档信息

- **作者**: Rookie Agent Team
- **日期**: 2025-10-26
- **难度**: ⭐⭐⭐⭐ (高级)
- **预计学习时间**: 90分钟
- **前置知识**: Python高级特性、HTTP协议、异步编程、Pydantic

---

## 目录

1. [为什么需要LLM抽象层？](#1-为什么需要llm抽象层)
2. [架构设计思想](#2-架构设计思想)
3. [核心模块详解](#3-核心模块详解)
4. [设计模式与最佳实践](#4-设计模式与最佳实践)
5. [实现细节与技术难点](#5-实现细节与技术难点)
6. [使用示例](#6-使用示例)
7. [常见问题](#7-常见问题)
8. [总结与延伸](#8-总结与延伸)

---

## 1. 为什么需要LLM抽象层？

### 1.1 问题背景

在开发AI Agent时，我们需要与各种LLM API交互。如果直接调用各家API，会遇到什么问题？

```python
# ❌ 直接调用OpenAI API
import openai
openai_response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello"}]
)

# ❌ 直接调用Qwen API
import dashscope
qwen_response = dashscope.Generation.call(
    model="qwen-max",
    messages=[{"role": "user", "content": "Hello"}]
)

# ❌ 直接调用Claude API
import anthropic
claude = anthropic.Anthropic()
claude_response = claude.messages.create(
    model="claude-3-opus-20240229",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello"}]
)
```

**问题显而易见**：
1. **API不统一**：每家API的调用方式、参数格式、响应结构都不同
2. **切换成本高**：换个模型需要改一堆代码
3. **配置混乱**：API Key、Base URL等配置分散在各处
4. **错误处理不一致**：每家的错误码和异常类型都不同
5. **功能差异**：有的支持流式，有的支持Function Calling，难以统一

### 1.2 为什么不用LangChain？

你可能会问：LangChain不是已经做了这件事吗？

**是的，但是**：

| 维度 | LangChain | Rookie Agent |
|------|-----------|--------------|
| **学习目的** | ❌ 生产工具，抽象层次高 | ✅ 教学导向，每行代码可理解 |
| **可控性** | ⚠️ 黑盒封装，难以调试 | ✅ 白盒设计，完全可控 |
| **依赖复杂度** | ❌ 依赖众多，体积庞大 | ✅ 依赖最小，轻量简洁 |
| **定制化** | ⚠️ 受限于框架设计 | ✅ 随意修改，深度定制 |
| **原理理解** | ❌ 难以理解底层原理 | ✅ 从第一性原理出发 |

我们的目标是**从零手写**，彻底掌握LLM抽象层的设计与实现。

### 1.3 我们的设计目标

构建一个：
- ✅ **统一抽象**：一套API调用所有LLM
- ✅ **易于扩展**：新增Provider只需实现接口
- ✅ **配置灵活**：环境变量、代码传参、配置文件多种方式
- ✅ **功能完整**：同步/异步、流式/非流式、Function Calling
- ✅ **类型安全**：完整的类型注解和Pydantic验证
- ✅ **错误处理**：统一的异常体系和重试机制
- ✅ **可观测**：详细的日志和性能监控

---

## 2. 架构设计思想

### 2.1 整体架构

我们的LLM模块采用**分层设计 + 适配器模式**：

```
┌─────────────────────────────────────────────────────┐
│                  Application Layer                  │
│             (Agent, Tools, Memory, etc.)            │
└──────────────────────┬──────────────────────────────┘
                       │
         ┌─────────────▼──────────────┐
         │    Unified Interface       │  ← BaseLLMProvider
         │  chat() / stream() / embed()│
         └─────────────┬──────────────┘
                       │
    ┌──────────────────┴──────────────────┬───────────┬──────────┐
    │                  │                  │           │          │
┌───▼────┐  ┌─────────▼──────┐  ┌───────▼─────┐ ┌───▼───┐ ┌───▼────┐
│OpenAI  │  │  Qwen          │  │ DeepSeek    │ │Ollama │ │ Claude │
│Provider│  │  Provider      │  │ Provider    │ │Provide│ │Provider│
└───┬────┘  └─────────┬──────┘  └───────┬─────┘ └───┬───┘ └───┬────┘
    │                 │                 │            │          │
    │                 │ (适配层：格式转换、错误映射) │          │
    │                 │                 │            │          │
    └─────────────────┴─────────────────┴────────────┴──────────┘
                              │
                ┌─────────────▼──────────────┐
                │   HTTP Client Layer        │
                │  (Retry, Streaming, SSE)   │
                └────────────────────────────┘
```

**关键设计点**：

1. **统一契约**：所有Provider实现相同的`BaseLLMProvider`接口
2. **适配边界**：Provider层负责差异适配，上层无感知
3. **职责分离**：HTTP通信、重试、流式解析由底层处理
4. **配置分层**：通用配置在基类，特定配置在子类

### 2.2 核心设计原则

#### 原则1: 依赖倒置（DIP）

```python
# ❌ Bad: 上层依赖具体实现
class Agent:
    def __init__(self):
        self.llm = OpenAI()  # 硬编码，难以切换

    def chat(self, message):
        return self.llm.create_completion(message)

# ✅ Good: 依赖抽象接口
class Agent:
    def __init__(self, llm: BaseLLMProvider):  # 依赖抽象
        self.llm = llm

    def chat(self, message):
        return self.llm.chat(message)  # 统一接口

# 可以随意切换Provider
agent = Agent(OpenAIProvider())
# agent = Agent(QwenProvider())
# agent = Agent(ClaudeProvider())
```

**好处**：
- 上层代码不关心具体Provider
- 轻松切换不同LLM
- 方便测试（可以Mock Provider）

#### 原则2: 开闭原则（OCP）

```python
# 对扩展开放
class CustomProvider(BaseLLMProvider):
    """新增Provider只需实现接口，不修改现有代码"""

    def chat(self, messages, **kwargs):
        # 自定义实现
        pass

# 对修改封闭
# 添加新Provider不影响现有的OpenAI、Qwen等实现
```

#### 原则3: 接口隔离（ISP）

```python
# BaseLLMProvider定义最小必要接口
class BaseLLMProvider(ABC):
    @abstractmethod
    def chat(self, messages, **kwargs):
        """所有Provider必须实现"""
        pass

    def embed(self, texts, **kwargs):
        """可选功能，不支持的抛出NotImplementedError"""
        raise NotImplementedError()
```

**好处**：
- 不强制所有Provider实现所有功能
- Ollama不支持embeddings？没问题，用默认实现即可
- Claude有特殊API格式？在子类中特殊处理

### 2.3 模块职责划分

| 模块 | 职责 | 不负责 |
|------|------|--------|
| **exceptions.py** | 异常定义、错误映射 | 异常处理逻辑（在Provider中） |
| **types.py** | 消息格式、类型定义 | 消息生成逻辑 |
| **config.py** | 配置管理、参数验证 | 配置使用逻辑 |
| **base.py** | 接口定义、通用逻辑 | 具体API调用 |
| **providers/** | API调用、格式适配 | 通用功能（在基类中） |

**设计理念**：单一职责，高内聚低耦合。

---

## 3. 核心模块详解

### 3.1 异常体系设计 (exceptions.py)

#### 3.1.1 为什么需要自定义异常？

```python
# ❌ Bad: 使用通用异常
try:
    response = requests.post(url, json=data)
except Exception as e:
    # 无法区分错误类型
    # 是网络错误？认证错误？还是服务器错误？
    print(f"Error: {e}")

# ✅ Good: 使用自定义异常
try:
    response = provider.chat(messages)
except AuthenticationError:
    # 明确知道是认证错误，可以提示用户检查API Key
    print("Invalid API Key, please check your configuration")
except RateLimitError as e:
    # 明确知道是限流，可以等待后重试
    print(f"Rate limited, retry after {e.retry_after}s")
except ServerError:
    # 明确知道是服务器错误，可以记录并重试
    logger.error("LLM service unavailable, will retry")
```

**好处**：
1. **精确的错误处理**：针对不同错误采取不同策略
2. **丰富的上下文**：携带status_code、response_body等信息
3. **统一的接口**：所有Provider抛出相同的异常类型

#### 3.1.2 异常层次设计

```python
LLMError (基类)
├── ConfigurationError (配置错误)
├── LLMAPIError (API错误基类)
│   ├── AuthenticationError (401 - 认证失败)
│   ├── PermissionError (403 - 权限不足)
│   ├── NotFoundError (404 - 资源不存在)
│   ├── RateLimitError (429 - 速率限制)
│   └── ServerError (5xx - 服务器错误)
├── TokenLimitError (Token超限)
└── ContentFilterError (内容过滤)
```

**设计思想**：
- **树形结构**：可以catch基类捕获所有LLM错误
- **粒度适中**：既不过于细分，也不过于粗糙
- **语义清晰**：异常名称一看就知道什么问题

#### 3.1.3 错误映射函数

这是一个关键的设计，将HTTP错误统一映射为LLM异常：

```python
def map_http_error_to_llm_error(
    status_code: int,
    message: str,
    response_body: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None,
) -> LLMAPIError:
    """HTTP状态码 -> LLM异常的映射

    映射规则（来自架构文档13.3）：
    401 -> AuthenticationError
    403 -> PermissionError
    404 -> NotFoundError
    429 -> RateLimitError (提取retry_after)
    5xx -> ServerError
    其他 -> LLMAPIError
    """
    if status_code == 401:
        return AuthenticationError(message, ...)
    elif status_code == 429:
        # 从header提取retry_after
        retry_after = extract_retry_after(headers)
        return RateLimitError(message, retry_after=retry_after, ...)
    # ...
```

**巧妙之处**：
1. **集中映射**：错误转换逻辑集中在一处，易于维护
2. **信息提取**：从header提取retry_after等有用信息
3. **可扩展**：新增错误类型只需修改这一个函数

#### 3.1.4 异常使用示例

```python
# Provider中使用
def chat(self, messages, **kwargs):
    try:
        response = self._client.post("/chat/completions", json=data)
        return self._parse_response(response)
    except HTTPStatusError as e:
        # 统一映射为LLM异常
        raise map_http_error_to_llm_error(
            e.status_code,
            str(e),
            e.response_body,
            e.headers
        ) from e

# 上层调用
try:
    response = provider.chat(messages)
except RateLimitError as e:
    # 精确处理速率限制
    wait_time = e.retry_after or 60
    logger.warning(f"Rate limited, waiting {wait_time}s")
    time.sleep(wait_time)
    response = provider.chat(messages)  # 重试
except AuthenticationError:
    # 认证错误，提示用户
    raise RuntimeError("Please set OPENAI_API_KEY environment variable")
except LLMError as e:
    # 捕获所有LLM错误
    logger.error(f"LLM error: {e}")
```

### 3.2 类型系统设计 (types.py)

#### 3.2.1 为什么使用Pydantic？

```python
# ❌ Bad: 使用字典，缺少验证
message = {
    "role": "usr",  # 拼写错误！
    "content": 123,  # 类型错误！
}

# ✅ Good: 使用Pydantic，自动验证
class Message(BaseModel):
    role: MessageRole  # 枚举，只能是system/user/assistant
    content: Union[str, List[MessageContent]]  # 类型检查

message = Message(role="usr", content=123)
# ValidationError: role must be one of system/user/assistant
```

**Pydantic的优势**：
1. **类型验证**：自动检查类型是否正确
2. **数据转换**：自动将兼容类型转换（如int -> str）
3. **清晰的错误**：验证失败时给出明确的错误信息
4. **IDE支持**：完整的类型提示和自动补全
5. **序列化**：方便地转换为dict/JSON

#### 3.2.2 消息系统设计

**设计目标**：支持纯文本和多模态（文本+图片）

```python
# 简单文本消息
msg = Message(
    role=MessageRole.USER,
    content="Hello"  # 字符串
)

# 多模态消息（文本+图片）
msg = Message(
    role=MessageRole.USER,
    content=[
        MessageContent(type=ContentType.TEXT, text="What's in this image?"),
        MessageContent(type=ContentType.IMAGE_URL, image_url="https://...")
    ]
)
```

**关键设计**：
- `content`字段可以是`str`或`List[MessageContent]`
- 使用`Union`类型支持两种格式
- `is_multimodal`属性方便检查
- `has_images`属性检查是否包含图片
- `to_dict()`方法转换为API格式

**难点：API格式转换**

不同Provider的API格式略有差异，`to_dict()`方法负责转换：

```python
def to_dict(self) -> Dict[str, Any]:
    """转换为API请求格式"""
    result = {"role": self.role}

    if isinstance(self.content, str):
        # 简单文本
        result["content"] = self.content
    else:
        # 多模态内容
        result["content"] = [
            {
                "type": c.type.value,
                "text": c.text if c.text else ...,
                "image_url": {
                    "url": c.image_url,
                    "detail": c.detail
                } if c.image_url else ...
            }
            for c in self.content
        ]

    return result
```

#### 3.2.3 响应格式设计

**两种响应格式**：

1. **非流式** - `ChatCompletion`：
```python
{
    "id": "chatcmpl-123",
    "object": "chat.completion",
    "created": 1677858242,
    "model": "gpt-4",
    "choices": [
        {
            "index": 0,
            "message": {"role": "assistant", "content": "Hello!"},
            "finish_reason": "stop"
        }
    ],
    "usage": {
        "prompt_tokens": 10,
        "completion_tokens": 5,
        "total_tokens": 15
    }
}
```

2. **流式** - `CompletionChunk`：
```python
{
    "id": "chatcmpl-123",
    "object": "chat.completion.chunk",
    "created": 1677858242,
    "model": "gpt-4",
    "choices": [
        {
            "index": 0,
            "delta": {"content": "Hello"},  # 增量内容
            "finish_reason": None
        }
    ]
}
```

**设计考量**：
- 统一的ID贯穿所有chunk（方便追踪）
- `delta`格式表示增量内容
- `finish_reason`在最后一个chunk中出现
- `get_content()`辅助方法快速提取内容

#### 3.2.4 Function Calling类型

```python
# 函数定义（JSON Schema格式）
func_def = FunctionDefinition(
    name="get_weather",
    description="获取指定城市的天气",
    parameters={
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "description": "城市名称"
            },
            "unit": {
                "type": "string",
                "enum": ["celsius", "fahrenheit"]
            }
        },
        "required": ["city"]
    }
)

# 工具定义（包装函数定义）
tool = ToolDefinition(type="function", function=func_def)

# 工具调用（模型返回）
tool_call = ToolCall(
    id="call_abc123",
    type="function",
    function={
        "name": "get_weather",
        "arguments": '{"city": "Beijing", "unit": "celsius"}'
    }
)
```

**设计亮点**：
- 完全符合OpenAI的Function Calling规范
- Pydantic验证确保schema正确
- 方便与真实函数绑定

### 3.3 配置管理设计 (config.py)

#### 3.3.1 配置优先级

这是一个**非常重要**的设计：

```
1. 代码传参      (最高优先级)
    ↓
2. 环境变量      (中等优先级)
    ↓
3. 配置文件      (较低优先级, 未实现)
    ↓
4. 默认值        (最低优先级)
```

**实现原理**：

```python
class OpenAIConfig(ProviderConfig):
    model: str = "gpt-4"  # 默认值

    @validator("api_key", pre=True, always=True)
    def load_api_key(cls, v):
        """优先级：代码传参 > 环境变量"""
        if v is not None:  # 代码传参
            return v
        return os.getenv("OPENAI_API_KEY")  # 环境变量

# 使用示例
config1 = OpenAIConfig()
# api_key从环境变量读取，model使用默认值"gpt-4"

config2 = OpenAIConfig(model="gpt-3.5-turbo")
# model被覆盖为"gpt-3.5-turbo"，api_key仍从环境变量读取

config3 = OpenAIConfig(api_key="sk-xxx", model="gpt-4-turbo")
# 完全覆盖，不读取环境变量
```

**Pydantic的`@validator`巧妙应用**：
- `pre=True`：在Pydantic验证之前执行
- `always=True`：即使字段有值也执行
- 实现了灵活的配置加载逻辑

#### 3.3.2 安全性设计

**API Key脱敏**：

```python
def __repr__(self) -> str:
    """日志输出时自动脱敏"""
    fields = []
    for field_name, field_value in self.dict().items():
        if "key" in field_name.lower():
            if field_value:
                masked = f"{field_value[:7]}..."  # sk-xxx...
                fields.append(f"{field_name}='{masked}'")
        else:
            fields.append(f"{field_name}={field_value!r}")
    return f"{self.__class__.__name__}({', '.join(fields)})"

# 使用效果
config = OpenAIConfig(api_key="sk-1234567890abcdef")
print(config)
# OpenAIConfig(api_key='sk-1234...', model='gpt-4', ...)
```

**验证失败提示清晰**：

```python
@root_validator(pre=False)
def validate_config(cls, values):
    api_key = values.get("api_key")
    if api_key is None:
        raise ConfigurationError(
            f"API key is required for {cls.__name__}. "
            f"Set it via environment variable or pass as parameter."
        )
    return values

# 使用效果
config = OpenAIConfig()
# ConfigurationError: API key is required for OpenAIConfig.
# Set it via environment variable or pass as parameter.
```

**设计思想**：
- **安全第一**：API Key不会出现在日志中
- **开发友好**：错误信息给出明确的解决方案
- **生产可用**：配置验证在初始化时完成，快速失败

#### 3.3.3 Provider特定配置

每个Provider可以有自己的特殊参数：

```python
# OpenAI特有参数
class OpenAIConfig(ProviderConfig):
    frequency_penalty: float = 0.0  # 频率惩罚
    presence_penalty: float = 0.0   # 存在惩罚
    seed: Optional[int] = None      # 随机种子
    response_format: Optional[Dict] = None  # JSON模式

# Qwen特有参数
class QwenConfig(ProviderConfig):
    enable_search: bool = False     # 联网搜索
    repetition_penalty: float = 1.0 # 重复惩罚

# Ollama特殊处理
class OllamaConfig(ProviderConfig):
    @classmethod
    def _allow_none_api_key(cls) -> bool:
        """Ollama本地部署不需要API Key"""
        return True
```

**设计巧妙之处**：
- 基类定义通用参数
- 子类扩展特定参数
- 通过`@classmethod`钩子实现特殊逻辑

### 3.4 BaseLLMProvider设计 (base.py)

#### 3.4.1 抽象基类的设计

```python
from abc import ABC, abstractmethod

class BaseLLMProvider(ABC):
    """所有Provider的基类

    设计目标：
    1. 定义统一接口
    2. 提供通用实现
    3. 强制子类实现关键方法
    4. 提供辅助工具方法
    """

    # 抽象方法：子类必须实现
    @abstractmethod
    def chat(self, messages, **kwargs):
        pass

    @abstractmethod
    async def achat(self, messages, **kwargs):
        pass

    # 具体方法：提供默认实现
    def count_tokens(self, messages, model=None):
        """默认的粗略估算"""
        return sum(len(str(msg.content)) for msg in messages) // 4

    def supports_function_calling(self):
        """默认不支持，子类可覆盖"""
        return False
```

**ABC的作用**：
- 无法直接实例化抽象基类
- 子类必须实现所有`@abstractmethod`
- Python会在实例化时检查，防止遗漏

#### 3.4.2 初始化流程设计

```python
def __init__(self, config: ProviderConfig):
    """初始化流程：配置->验证->设置客户端"""
    self.config = config
    self._validate_config()  # 1. 验证配置
    self._setup_client()     # 2. 设置HTTP客户端

    logger.info(
        f"Initialized {self.__class__.__name__} "
        f"(model={config.model})"
    )
```

**模板方法模式**：
1. 基类定义流程框架（`__init__`）
2. 子类实现具体步骤（`_validate_config`、`_setup_client`）
3. 保证所有Provider的初始化流程一致

#### 3.4.3 辅助方法：_build_chat_request

这是一个非常实用的设计：

```python
def _build_chat_request(self, messages, **kwargs):
    """构建聊天请求的通用逻辑

    功能：
    1. 合并配置默认值和运行时参数
    2. 转换消息格式
    3. 处理可选参数
    """
    # 转换消息格式
    request_messages = [msg.to_dict() for msg in messages]

    # 合并参数（运行时参数优先）
    request = {
        "model": kwargs.get("model", self.config.model),
        "messages": request_messages,
        "temperature": kwargs.get("temperature", self.config.temperature),
        "top_p": kwargs.get("top_p", self.config.top_p),
    }

    # 可选参数
    if max_tokens := kwargs.get("max_tokens", self.config.max_tokens):
        request["max_tokens"] = max_tokens

    if tools := kwargs.get("tools"):
        request["tools"] = [t.dict() for t in tools]

    return request
```

**优点**：
- 子类只需调用这个方法，不用重复写参数合并逻辑
- 统一的参数处理，减少bug
- 使用海象运算符`:=`简化代码

#### 3.4.4 资源管理：Context Manager

```python
# 同步版本
def __enter__(self):
    return self

def __exit__(self, *args):
    self.close()

def close(self):
    """关闭HTTP客户端，释放资源"""
    if hasattr(self, '_client'):
        self._client.close()

# 异步版本
async def __aenter__(self):
    return self

async def __aexit__(self, *args):
    await self.aclose()

async def aclose(self):
    if hasattr(self, '_client'):
        await self._client.aclose()
```

**使用效果**：

```python
# 自动资源管理
with OpenAIProvider(config) as provider:
    response = provider.chat(messages)
# 自动调用close()

# 异步版本
async with OpenAIProvider(config) as provider:
    response = await provider.achat(messages)
# 自动调用aclose()
```

**设计思想**：
- Python的`with`语句自动管理资源
- 即使异常发生也能确保清理
- 符合"资源获取即初始化"(RAII)模式

---

## 4. 设计模式与最佳实践

### 4.1 适配器模式（Adapter Pattern）

**问题**：不同LLM的API格式不同，如何统一？

**解决**：每个Provider作为一个适配器，将特定API转换为统一接口。

```python
class ClaudeProvider(BaseLLMProvider):
    """Claude的API格式与OpenAI不同，需要适配"""

    def _convert_messages_to_claude_format(self, messages):
        """适配：统一格式 -> Claude格式"""
        system = None
        claude_messages = []

        for msg in messages:
            if msg.role == MessageRole.SYSTEM:
                # Claude的system是单独的参数
                system = msg.content
            else:
                claude_messages.append({
                    "role": msg.role.value,
                    "content": msg.content
                })

        return system, claude_messages

    def chat(self, messages, **kwargs):
        # 1. 适配请求格式
        system, claude_messages = self._convert_messages_to_claude_format(messages)

        request = {
            "model": kwargs.get("model", self.config.model),
            "messages": claude_messages,
            "max_tokens": kwargs.get("max_tokens", 4096),
        }

        if system:
            request["system"] = system

        # 2. 调用API
        response = self._client.post("/v1/messages", json=request)

        # 3. 适配响应格式
        return self._convert_claude_response_to_standard(response.json())
```

**适配器模式的好处**：
- 上层代码只看到统一接口
- 所有差异在适配器内部处理
- 新增Provider不影响现有代码

### 4.2 模板方法模式（Template Method Pattern）

**应用场景**：初始化流程

```python
# 基类定义模板
class BaseLLMProvider(ABC):
    def __init__(self, config):
        self.config = config
        self._validate_config()  # 步骤1：验证
        self._setup_client()     # 步骤2：设置客户端
        # 流程固定，但具体实现由子类决定

# 子类实现具体步骤
class OpenAIProvider(BaseLLMProvider):
    def _validate_config(self):
        if not self.config.api_key:
            raise ConfigurationError("API key required")

    def _setup_client(self):
        self._client = HTTPClient(
            base_url=self.config.api_base,
            default_headers={
                "Authorization": f"Bearer {self.config.api_key}"
            }
        )
```

### 4.3 策略模式（Strategy Pattern）

**应用场景**：错误处理策略

```python
# 不同的错误有不同的处理策略
try:
    response = provider.chat(messages)
except RateLimitError as e:
    # 策略1：等待后重试
    time.sleep(e.retry_after or 60)
    response = provider.chat(messages)
except AuthenticationError:
    # 策略2：提示用户配置
    raise RuntimeError("Please configure API key")
except ServerError:
    # 策略3：记录日志并重试
    logger.error("Server error, retrying...")
    response = provider.chat(messages)
```

### 4.4 工厂模式（Factory Pattern）

虽然还未实现，但我们会用工厂模式创建Provider：

```python
class ProviderFactory:
    _providers = {
        "openai": OpenAIProvider,
        "qwen": QwenProvider,
        "deepseek": DeepSeekProvider,
        "ollama": OllamaProvider,
        "claude": ClaudeProvider,
    }

    @classmethod
    def create(cls, provider_name: str, **kwargs):
        """工厂方法：根据名称创建Provider"""
        provider_class = cls._providers.get(provider_name.lower())
        if not provider_class:
            raise ValueError(f"Unknown provider: {provider_name}")

        # 自动选择配置类
        config_class = provider_class.get_config_class()
        config = config_class(**kwargs)

        return provider_class(config)

# 使用
provider = ProviderFactory.create("openai")
# provider = ProviderFactory.create("qwen")
```

---

## 5. 实现细节与技术难点

### 5.1 Pydantic高级用法

#### 5.1.1 Validator的执行顺序

```python
class OpenAIConfig(ProviderConfig):
    api_key: Optional[str] = None

    @validator("api_key", pre=True, always=True)
    def load_api_key(cls, v):
        """validator执行顺序：

        1. pre=True: 在Pydantic验证之前执行
        2. always=True: 即使字段有值也执行
        3. 返回值会被Pydantic继续验证
        """
        if v is not None:
            return v
        return os.getenv("OPENAI_API_KEY")

    @root_validator(pre=False)
    def validate_config(cls, values):
        """root_validator在所有字段验证后执行"""
        api_key = values.get("api_key")
        if api_key is None:
            raise ValueError("API key required")
        return values
```

#### 5.1.2 Union类型的处理

```python
class Message(BaseModel):
    content: Union[str, List[MessageContent]]

    # Pydantic会自动尝试匹配类型
    msg1 = Message(role="user", content="Hello")  # str
    msg2 = Message(role="user", content=[...])    # List[MessageContent]
```

### 5.2 异步编程注意事项

#### 5.2.1 同步和异步的并存

```python
class BaseLLMProvider(ABC):
    # 同步方法
    @abstractmethod
    def chat(self, messages, **kwargs):
        pass

    # 异步方法
    @abstractmethod
    async def achat(self, messages, **kwargs):
        pass

# 使用时要注意
# ❌ 错误
async def main():
    response = provider.chat(messages)  # 同步调用会阻塞事件循环

# ✅ 正确
async def main():
    response = await provider.achat(messages)  # 使用异步版本
```

#### 5.2.2 异步流式迭代

```python
# 同步流式
for chunk in provider.stream(messages):
    print(chunk.get_content(), end='')

# 异步流式
async for chunk in provider.astream(messages):
    print(chunk.get_content(), end='')
```

### 5.3 类型注解的技巧

#### 5.3.1 泛型和协变

```python
from typing import Iterator, AsyncIterator

# Iterator表示同步迭代器
def stream(self, ...) -> Iterator[CompletionChunk]:
    for chunk in ...:
        yield chunk

# AsyncIterator表示异步迭代器
async def astream(self, ...) -> AsyncIterator[CompletionChunk]:
    async for chunk in ...:
        yield chunk
```

#### 5.3.2 可选参数的处理

```python
from typing import Optional, Any

def chat(
    self,
    messages: List[Message],
    model: Optional[str] = None,  # 可选的具体类型
    **kwargs: Any                 # 任意额外参数
) -> ChatCompletion:
    pass
```

---

## 6. 使用示例

### 6.1 基础使用

```python
from rookie_agent.llm import OpenAIConfig, Message, MessageRole

# 方式1：从环境变量读取（推荐）
# export OPENAI_API_KEY=sk-xxx
config = OpenAIConfig()

# 方式2：代码传参
config = OpenAIConfig(
    api_key="sk-xxx",
    model="gpt-4",
    temperature=0.8
)

# 创建Provider
from rookie_agent.llm.providers import OpenAIProvider

provider = OpenAIProvider(config)

# 构建消息
messages = [
    Message(role=MessageRole.SYSTEM, content="你是一个有帮助的助手"),
    Message(role=MessageRole.USER, content="什么是量子计算？")
]

# 调用
response = provider.chat(messages)
print(response.choices[0].message.content)
```

### 6.2 流式输出

```python
# 流式输出
print("AI: ", end='', flush=True)
for chunk in provider.stream(messages):
    content = chunk.get_content()
    if content:
        print(content, end='', flush=True)
print()  # 换行
```

### 6.3 错误处理

```python
from rookie_agent.llm import (
    RateLimitError,
    AuthenticationError,
    LLMError
)

def safe_chat(provider, messages, max_retries=3):
    """带重试的安全调用"""
    for attempt in range(max_retries):
        try:
            return provider.chat(messages)

        except RateLimitError as e:
            if attempt < max_retries - 1:
                wait = e.retry_after or (2 ** attempt)
                logger.warning(f"Rate limited, waiting {wait}s")
                time.sleep(wait)
            else:
                raise

        except AuthenticationError:
            raise RuntimeError(
                "Invalid API key. Please check OPENAI_API_KEY"
            )

        except LLMError as e:
            logger.error(f"LLM error: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                raise
```

### 6.4 Context Manager使用

```python
# 自动资源管理
with OpenAIProvider(config) as provider:
    response = provider.chat(messages)
    print(response.choices[0].message.content)
# 自动关闭连接

# 异步版本
async with OpenAIProvider(config) as provider:
    response = await provider.achat(messages)
    print(response.choices[0].message.content)
```

### 6.5 多模态使用（Vision）

```python
from rookie_agent.llm import MessageContent, ContentType

# 构建包含图片的消息
messages = [
    Message(
        role=MessageRole.USER,
        content=[
            MessageContent(
                type=ContentType.TEXT,
                text="这张图片里有什么？"
            ),
            MessageContent(
                type=ContentType.IMAGE_URL,
                image_url="https://example.com/image.jpg",
                detail="high"  # 高分辨率模式
            )
        ]
    )
]

# 使用支持视觉的模型
response = provider.chat(messages, model="gpt-4-vision-preview")
print(response.choices[0].message.content)
```

---

## 7. 常见问题

### Q1: 为什么要分这么多模块？

**A**: 单一职责原则。每个模块只做一件事，便于：
- **理解**：每个文件职责清晰
- **测试**：可以独立测试每个模块
- **维护**：修改一个模块不影响其他模块
- **复用**：类型定义可以在多处使用

### Q2: 配置优先级为什么这样设计？

**A**: 符合"最小惊讶原则"：
- **代码传参**优先级最高：开发者明确指定的值最重要
- **环境变量**次之：生产环境的配置
- **默认值**最低：合理的默认值

这样既方便开发（代码传参），也方便部署（环境变量）。

### Q3: 为什么同时提供同步和异步接口？

**A**:
- **简单场景**：同步接口更直观，适合脚本和简单应用
- **高性能场景**：异步接口支持并发，适合Web服务和高并发
- **灵活性**：让用户根据场景选择

### Q4: 异常设计为什么这么细？

**A**: 精确的错误处理：
- `AuthenticationError`: 提示用户检查API Key
- `RateLimitError`: 自动等待后重试
- `ServerError`: 记录日志并重试
- 如果只有一个`LLMError`，无法区分处理策略

### Q5: Pydantic的性能开销大吗？

**A**:
- **验证开销**：只在初始化时验证一次，之后无开销
- **序列化开销**：相比手动dict操作，开销微乎其微
- **收益远大于成本**：类型安全、自动验证、清晰的错误信息

---

## 8. 总结与延伸

### 8.1 核心设计思想回顾

1. **统一抽象**：
   - BaseLLMProvider定义统一接口
   - 所有Provider实现相同方法
   - 上层代码无感知Provider差异

2. **分层设计**：
   ```
   应用层 → Provider层 → HTTP层 → 网络层
   ```
   - 每层职责清晰
   - 下层为上层提供服务
   - 层与层之间松耦合

3. **配置灵活**：
   - 多种配置来源
   - 清晰的优先级
   - 自动验证和脱敏

4. **错误处理**：
   - 层次化异常体系
   - 精确的错误分类
   - 丰富的错误上下文

5. **类型安全**：
   - Pydantic验证
   - 完整的类型注解
   - IDE友好

### 8.2 学到了什么

1. **设计模式的实战应用**：
   - 适配器模式：统一不同API
   - 模板方法模式：标准化流程
   - 策略模式：灵活的错误处理
   - 工厂模式：统一创建接口

2. **Python高级特性**：
   - ABC抽象基类
   - Pydantic数据验证
   - Context Manager资源管理
   - 异步编程

3. **架构设计原则**：
   - 单一职责（SRP）
   - 开闭原则（OCP）
   - 依赖倒置（DIP）
   - 接口隔离（ISP）

### 8.3 下一步

完成基础架构后，我们将实现具体的Provider：

1. **Week 3: OpenAI Provider**
   - 实现chat/stream
   - Function Calling支持
   - Token计数
   - 完整测试

2. **Week 4: 兼容Provider**
   - Qwen Provider
   - DeepSeek Provider
   - Ollama Provider

3. **Week 4-5: Claude Provider + 工厂模式**
   - Claude适配
   - ProviderFactory
   - Provider注册机制

### 8.4 扩展阅读

- [Pydantic官方文档](https://docs.pydantic.dev/)
- [Python ABC模块](https://docs.python.org/3/library/abc.html)
- [OpenAI API文档](https://platform.openai.com/docs/api-reference)
- [设计模式：可复用面向对象软件的基础](https://en.wikipedia.org/wiki/Design_Patterns)

### 8.5 思考题

1. 如果要添加一个缓存层（缓存LLM响应），应该在哪个位置加入？
2. 如何实现Provider的A/B测试（同时调用两个Provider比较结果）？
3. 如果要支持多轮对话的上下文管理，应该如何设计？
4. 如何实现Provider的负载均衡（在多个API Key之间轮换）？

---

## 附录：完整代码结构

```
src/rookie_agent/llm/
├── __init__.py              # 模块导出
├── exceptions.py            # 异常体系
│   ├── LLMError             # 基础异常
│   ├── ConfigurationError   # 配置错误
│   ├── LLMAPIError          # API错误基类
│   │   ├── AuthenticationError  (401)
│   │   ├── PermissionError      (403)
│   │   ├── NotFoundError        (404)
│   │   ├── RateLimitError       (429)
│   │   └── ServerError          (5xx)
│   ├── TokenLimitError      # Token超限
│   ├── ContentFilterError   # 内容过滤
│   └── map_http_error_to_llm_error()  # 映射函数
│
├── types.py                 # 类型系统
│   ├── MessageRole          # 消息角色枚举
│   ├── ContentType          # 内容类型枚举
│   ├── FinishReason         # 结束原因枚举
│   ├── MessageContent       # 消息内容块
│   ├── Message              # 统一消息格式
│   ├── FunctionDefinition   # 函数定义
│   ├── ToolDefinition       # 工具定义
│   ├── ToolCall             # 工具调用
│   ├── CompletionUsage      # Token使用统计
│   ├── CompletionChoice     # 完成选择
│   ├── ChatCompletion       # 非流式响应
│   └── CompletionChunk      # 流式响应块
│
├── config.py                # 配置管理
│   ├── ProviderConfig       # 基础配置
│   ├── OpenAIConfig         # OpenAI配置
│   ├── QwenConfig           # Qwen配置
│   ├── DeepSeekConfig       # DeepSeek配置
│   ├── OllamaConfig         # Ollama配置
│   └── ClaudeConfig         # Claude配置
│
├── base.py                  # Provider基类
│   └── BaseLLMProvider      # 抽象基类
│       ├── __init__()       # 初始化
│       ├── _validate_config()  # 配置验证
│       ├── _setup_client()     # 客户端设置
│       ├── chat()              # 聊天补全
│       ├── achat()             # 异步聊天
│       ├── stream()            # 流式聊天
│       ├── astream()           # 异步流式
│       ├── embed()             # 向量生成
│       ├── aembed()            # 异步向量生成
│       ├── count_tokens()      # Token计数
│       ├── supports_*()        # 能力检查
│       └── close()/aclose()    # 资源清理
│
└── providers/               # 具体Provider实现（待开发）
    ├── openai.py
    ├── qwen.py
    ├── deepseek.py
    ├── ollama.py
    └── claude.py
```

---

**文档版本**: v1.0
**最后更新**: 2025-10-26
**反馈**: 如有问题，请在GitHub Issue中讨论
