# HTTP 客户端封装详解：从零到一的实战指南

## 文档信息

- **作者**: Rookie Agent Team
- **日期**: 2025-10-25
- **难度**: ⭐⭐⭐ (中级)
- **预计学习时间**: 60分钟
- **前置知识**: Python基础、HTTP协议基础、面向对象编程

---

## 目录

1. [为什么要自己封装HTTP客户端？](#1-为什么要自己封装http客户端)
2. [整体设计思路](#2-整体设计思路)
3. [核心模块详解](#3-核心模块详解)
4. [实现过程拆解](#4-实现过程拆解)
5. [设计技巧和最佳实践](#5-设计技巧和最佳实践)
6. [使用示例](#6-使用示例)
7. [常见问题](#7-常见问题)
8. [总结与延伸](#8-总结与延伸)

---

## 1. 为什么要自己封装HTTP客户端？

### 1.1 问题背景

在开发AI Agent框架时，我们需要频繁与各种LLM API交互：

```python
# OpenAI API
response = requests.post(
    "https://api.openai.com/v1/chat/completions",
    headers={"Authorization": f"Bearer {api_key}"},
    json={"model": "gpt-4", "messages": [...]},
)

# Azure OpenAI API
response = requests.post(
    "https://{endpoint}.openai.azure.com/openai/deployments/{model}/...",
    headers={"api-key": api_key},
    json={...},
)

# Anthropic API
response = requests.post(
    "https://api.anthropic.com/v1/messages",
    headers={"x-api-key": api_key},
    json={...},
)
```

**问题来了**：

1. 每个API都要重复写请求头、错误处理
2. 网络不稳定时需要手动重试
3. 超时处理逻辑分散在各处
4. 流式响应（SSE）处理复杂
5. 调试时缺少统一的日志

### 1.2 为什么不用LangChain？

你可能会问：LangChain不是已经封装好了吗？

**是的，但是**：

1. **教学目的**：我们要理解底层原理，而不是黑盒使用
2. **灵活性**：我们需要完全掌控重试、超时等逻辑
3. **轻量级**：LangChain依赖多，我们只需要HTTP功能
4. **定制化**：可以为我们的框架定制特殊需求

### 1.3 我们的目标

封装一个：
- ✅ **健壮的**：自动重试、错误处理、超时控制
- ✅ **易用的**：清晰的API、完整的类型提示
- ✅ **可观测的**：详细的日志、请求追踪
- ✅ **高性能的**：连接池、异步支持
- ✅ **教学友好的**：代码清晰、注释详细

---

## 2. 整体设计思路

### 2.1 架构设计

我们的HTTP模块采用分层设计：

```
┌─────────────────────────────────────────────────┐
│            高层应用（LLM Providers）             │
└────────────────┬────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────┐
│          HTTP Client (HTTPClient)               │
│  ┌──────────────────────────────────────────┐  │
│  │  - get(), post(), put(), delete()        │  │
│  │  - Header管理                            │  │
│  │  - Context Manager                       │  │
│  └──────────────────────────────────────────┘  │
└────────────────┬────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────┐
│             Retry Mechanism                     │
│  ┌──────────────────────────────────────────┐  │
│  │  - 指数退避                              │  │
│  │  - Jitter（抖动）                        │  │
│  │  - 选择性重试                            │  │
│  └──────────────────────────────────────────┘  │
└────────────────┬────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────┐
│         Error Handling Layer                    │
│  ┌──────────────────────────────────────────┐  │
│  │  - HTTPTimeoutError                      │  │
│  │  - HTTPConnectionError                   │  │
│  │  - HTTPStatusError                       │  │
│  └──────────────────────────────────────────┘  │
└────────────────┬────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────┐
│           httpx (底层HTTP库)                     │
└─────────────────────────────────────────────────┘
```

### 2.2 核心设计原则

#### 原则1: 单一职责（SRP）

每个类只做一件事：

```python
# ❌ Bad: 一个类做太多事
class HTTPClient:
    def request(self):
        # 发请求
        # 重试逻辑
        # 日志记录
        # 指标收集
        pass

# ✅ Good: 职责分离
class HTTPClient:
    """只负责HTTP请求"""
    def request(self): pass

class RetryConfig:
    """只负责重试配置"""
    def calculate_delay(self): pass

class Logger:
    """只负责日志"""
    def log(self): pass
```

#### 原则2: 依赖倒置（DIP）

依赖抽象而非具体实现：

```python
from abc import ABC, abstractmethod

# 定义抽象接口
class BaseHTTPClient(ABC):
    @abstractmethod
    def request(self, method, url, **kwargs):
        pass

# 具体实现依赖接口
class HTTPClient(BaseHTTPClient):
    def request(self, method, url, **kwargs):
        # 实现细节
        pass
```

#### 原则3: 开闭原则（OCP）

对扩展开放，对修改封闭：

```python
# 可以通过配置扩展行为，而不修改代码
client = HTTPClient(
    timeout=30.0,
    max_retries=3,
    retry_on=(ConnectionError, TimeoutError),  # 可配置
)
```

---

## 3. 核心模块详解

### 3.1 异常体系设计

**为什么需要自定义异常？**

1. **清晰的错误分类**：让调用者知道具体哪里出错了
2. **统一的错误处理**：可以在一个地方catch所有HTTP错误
3. **丰富的上下文信息**：携带状态码、响应体等信息

**实现思路**：

```python
# 基础异常
class HTTPError(RookieAgentError):
    """所有HTTP错误的基类"""
    def __init__(self, message, status_code=None, response_body=None):
        super().__init__(message)
        self.status_code = status_code        # 保存状态码
        self.response_body = response_body    # 保存响应体

# 具体异常 - 按错误类型分类
class HTTPTimeoutError(HTTPError):
    """超时错误 - 网络慢或服务无响应"""
    pass

class HTTPConnectionError(HTTPError):
    """连接错误 - 网络不通或DNS解析失败"""
    pass

class HTTPStatusError(HTTPError):
    """状态错误 - 服务返回4xx/5xx"""
    pass
```

**使用方式**：

```python
try:
    response = client.get(url)
except HTTPTimeoutError:
    # 超时了，可能需要增加超时时间
    logger.warning("Request timed out, retrying...")
except HTTPConnectionError:
    # 连接失败，可能网络有问题
    logger.error("Network issue detected")
except HTTPStatusError as e:
    # HTTP错误，检查状态码决定如何处理
    if e.status_code == 429:  # Too Many Requests
        logger.warning("Rate limited, backing off...")
```

### 3.2 重试机制设计

重试是HTTP客户端最重要的功能之一。我们来深入理解它。

#### 3.2.1 为什么需要重试？

网络请求是不可靠的：

```
请求1: ──X── (连接超时)
请求2: ──X── (DNS解析失败)
请求3: ──✓── (成功！)
```

**常见的临时性错误**：
- 网络抖动
- 服务器短暂过载
- DNS解析临时失败
- 负载均衡器切换

#### 3.2.2 核心概念：指数退避（Exponential Backoff）

**问题**：如果立即重试，可能会：
- 加重服务器负担
- 导致"惊群效应"（所有客户端同时重试）

**解决方案**：逐渐增加重试间隔

```python
def calculate_delay(attempt: int) -> float:
    """
    attempt 0: delay = 1.0 * (2^0) = 1.0s
    attempt 1: delay = 1.0 * (2^1) = 2.0s
    attempt 2: delay = 1.0 * (2^2) = 4.0s
    attempt 3: delay = 1.0 * (2^3) = 8.0s
    """
    return base_delay * (exponential_base ** attempt)
```

**时间线示例**：

```
请求1 (0s)    ──X── 失败
              ⏱ 等待 1s
请求2 (1s)    ──X── 失败
              ⏱ 等待 2s
请求3 (3s)    ──X── 失败
              ⏱ 等待 4s
请求4 (7s)    ──✓── 成功！
```

#### 3.2.3 Jitter（抖动）的妙用

**问题**：如果1000个客户端同时失败，它们会同时重试吗？

```
时间轴: 0s      1s      2s      3s
客户端1: X──────┐
客户端2: X──────┤
客户端3: X──────┤  所有在1s时同时重试！
  ...           │  （惊群效应）
客户端N: X──────┘
```

**解决方案**：加入随机抖动

```python
def calculate_delay_with_jitter(attempt: int) -> float:
    base_delay = 1.0 * (2 ** attempt)
    # 在 50%-100% 之间随机
    jitter = random.uniform(0.5, 1.0)
    return base_delay * jitter
```

**效果**：

```
时间轴: 0s      1s      2s      3s
客户端1: X──────┐
客户端2: X────────┐
客户端3: X─────────┐  分散在不同时间重试
  ...             │  （避免惊群）
客户端N: X───────────┐
```

#### 3.2.4 选择性重试

不是所有错误都应该重试！

```python
class RetryConfig:
    def __init__(
        self,
        retry_on=(ConnectionError, TimeoutError),  # 只重试这些错误
    ):
        self.retry_on = retry_on

    def should_retry(self, exception):
        # ✅ 网络错误 -> 重试
        if isinstance(exception, ConnectionError):
            return True

        # ✅ 超时 -> 重试
        if isinstance(exception, TimeoutError):
            return True

        # ❌ 认证错误 -> 不重试（重试也没用）
        if isinstance(exception, AuthenticationError):
            return False

        # ❌ 参数错误 -> 不重试（代码问题）
        if isinstance(exception, ValueError):
            return False
```

**重试决策树**：

```
异常发生
    │
    ├─ 是网络/超时错误？
    │   ├─ 是 → 还有重试次数？
    │   │   ├─ 是 → 计算延迟 → 等待 → 重试
    │   │   └─ 否 → 抛出 RetryExhaustedError
    │   └─ 否 → 直接抛出原始异常
```

#### 3.2.5 完整实现剖析

```python
@retry_on_exception(
    max_attempts=3,      # 最多尝试3次
    base_delay=1.0,      # 基础延迟1秒
    exponential_base=2.0,# 指数基数2
    jitter=True,         # 启用抖动
    retry_on=(HTTPConnectionError, HTTPTimeoutError),  # 只重试这些
)
def request(self, method, url, **kwargs):
    """
    执行流程：

    1. 尝试1 (attempt=0)
       ├─ 成功 → 返回结果 ✓
       └─ 失败 → 检查是否可重试
           ├─ 不可重试 → 抛出异常 ✗
           └─ 可重试 → 计算延迟
               └─ 延迟 = 1.0 * (2^0) * random(0.5-1.0) = 0.5-1.0s

    2. 尝试2 (attempt=1)
       ├─ 成功 → 返回结果 ✓
       └─ 失败 → 检查是否可重试
           └─ 延迟 = 1.0 * (2^1) * random(0.5-1.0) = 1.0-2.0s

    3. 尝试3 (attempt=2) - 最后一次
       ├─ 成功 → 返回结果 ✓
       └─ 失败 → 抛出 RetryExhaustedError ✗
    """
    try:
        response = self._client.request(method, url, **kwargs)
        return response
    except Exception as e:
        # 重试装饰器会捕获并处理
        raise
```

### 3.3 HTTP客户端设计

#### 3.3.1 为什么选择httpx？

对比主流HTTP库：

| 特性 | requests | httpx | aiohttp |
|------|----------|-------|---------|
| 同步支持 | ✅ | ✅ | ❌ |
| 异步支持 | ❌ | ✅ | ✅ |
| HTTP/2 | ❌ | ✅ | ✅ |
| API一致性 | - | 同步/异步API一致 | 不一致 |
| 类型提示 | 部分 | 完整 | 部分 |

**选择httpx的原因**：
1. 同时支持同步和异步（API一致）
2. 完整的类型提示
3. 更现代的设计
4. 支持HTTP/2

#### 3.3.2 核心功能实现

**1. Header管理**

```python
class HTTPClient:
    def __init__(self, default_headers=None):
        self.default_headers = default_headers or {}

    def _merge_headers(self, headers):
        """合并默认header和请求header

        设计要点：
        1. 不修改原始字典（immutable）
        2. 请求header优先级更高（覆盖默认header）
        """
        merged = self.default_headers.copy()  # 复制，不修改原始
        if headers:
            merged.update(headers)  # 请求header覆盖默认header
        return merged
```

**使用示例**：

```python
# 设置默认header（所有请求都带上）
client = HTTPClient(default_headers={
    "User-Agent": "RookieAgent/1.0",
    "Accept": "application/json",
})

# 单次请求可以覆盖或添加header
response = client.get(
    url,
    headers={"Authorization": "Bearer token"}  # 添加认证
)

# 最终发送的header:
# {
#     "User-Agent": "RookieAgent/1.0",      # 默认
#     "Accept": "application/json",          # 默认
#     "Authorization": "Bearer token"        # 请求特定
# }
```

**2. 错误转换**

```python
def _handle_httpx_error(self, error, url):
    """将httpx异常转换为我们的异常

    为什么要转换？
    1. 统一错误体系
    2. 添加更多上下文信息
    3. 简化调用者的错误处理
    """
    if isinstance(error, httpx.TimeoutException):
        # 添加更多信息
        raise HTTPTimeoutError(
            f"Request to {url} timed out after {self.timeout}s"
        ) from error  # 保留原始异常链

    elif isinstance(error, httpx.ConnectError):
        raise HTTPConnectionError(
            f"Failed to connect to {url}"
        ) from error

    # ... 其他错误类型
```

**3. Context Manager（上下文管理器）**

```python
class HTTPClient:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()  # 自动清理资源

    def close(self):
        """关闭连接池，释放资源"""
        self._client.close()
```

**为什么需要Context Manager？**

```python
# ❌ Bad: 容易忘记关闭
client = HTTPClient()
response = client.get(url)
# 忘记调用 client.close() ！
# 连接池不会释放，可能导致资源泄漏

# ✅ Good: 自动清理
with HTTPClient() as client:
    response = client.get(url)
# 自动调用 client.close()
```

---

## 4. 实现过程拆解

让我们一步步实现一个简化版的HTTP客户端，理解整个过程。

### Step 1: 最简单的封装

```python
import httpx

class SimpleHTTPClient:
    """最简单的封装 - 只是包装了httpx"""

    def __init__(self):
        self._client = httpx.Client()

    def get(self, url):
        return self._client.get(url)

    def close(self):
        self._client.close()
```

**问题**：
- ❌ 没有错误处理
- ❌ 没有重试
- ❌ 没有超时控制

### Step 2: 添加超时控制

```python
class HTTPClientWithTimeout:
    def __init__(self, timeout=30.0):
        self.timeout = timeout
        self._client = httpx.Client(timeout=timeout)

    def get(self, url):
        try:
            return self._client.get(url)
        except httpx.TimeoutException:
            raise HTTPTimeoutError(f"Request timed out after {self.timeout}s")
```

**改进**：
- ✅ 可配置超时
- ✅ 统一的超时错误

### Step 3: 添加基础重试

```python
import time

class HTTPClientWithRetry:
    def __init__(self, timeout=30.0, max_retries=3):
        self.timeout = timeout
        self.max_retries = max_retries
        self._client = httpx.Client(timeout=timeout)

    def get(self, url):
        last_error = None

        for attempt in range(self.max_retries):
            try:
                return self._client.get(url)
            except httpx.TimeoutException as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    # 简单重试，延迟1秒
                    time.sleep(1.0)
                    continue

        # 所有重试都失败了
        raise HTTPTimeoutError(
            f"Failed after {self.max_retries} attempts"
        ) from last_error
```

**改进**：
- ✅ 有重试机制
- ❌ 但是延迟固定（应该用指数退避）

### Step 4: 添加指数退避

```python
class HTTPClientWithBackoff:
    def __init__(self, timeout=30.0, max_retries=3):
        self.timeout = timeout
        self.max_retries = max_retries
        self._client = httpx.Client(timeout=timeout)

    def _calculate_delay(self, attempt):
        """指数退避：1s, 2s, 4s, 8s..."""
        return 1.0 * (2 ** attempt)

    def get(self, url):
        for attempt in range(self.max_retries):
            try:
                return self._client.get(url)
            except httpx.TimeoutException as e:
                if attempt < self.max_retries - 1:
                    delay = self._calculate_delay(attempt)
                    print(f"Retry {attempt + 1} after {delay}s...")
                    time.sleep(delay)
                else:
                    raise HTTPTimeoutError(
                        f"Failed after {self.max_retries} attempts"
                    ) from e
```

**改进**：
- ✅ 使用指数退避
- ❌ 但是代码逻辑混乱（重试逻辑和请求逻辑混在一起）

### Step 5: 使用装饰器分离关注点

```python
from functools import wraps

def retry_on_error(max_attempts=3):
    """重试装饰器 - 分离重试逻辑"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except httpx.TimeoutException:
                    if attempt < max_attempts - 1:
                        delay = 1.0 * (2 ** attempt)
                        time.sleep(delay)
                    else:
                        raise
        return wrapper
    return decorator

class HTTPClientClean:
    def __init__(self, timeout=30.0):
        self._client = httpx.Client(timeout=timeout)

    @retry_on_error(max_attempts=3)  # 重试逻辑通过装饰器分离
    def get(self, url):
        """请求逻辑很干净"""
        try:
            return self._client.get(url)
        except httpx.TimeoutException as e:
            raise HTTPTimeoutError("Request timed out") from e
```

**改进**：
- ✅ 关注点分离（请求 vs 重试）
- ✅ 代码更清晰
- ✅ 可复用装饰器

### Step 6: 完整的生产级实现

这就是我们最终的实现！结合了所有最佳实践。

```python
# 完整代码见 src/rookie_agent/http/client.py
```

---

## 5. 设计技巧和最佳实践

### 5.1 类型安全

**为什么需要类型注解？**

```python
# ❌ Bad: 没有类型提示
def get(self, url, params=None, headers=None):
    pass

# ✅ Good: 完整的类型提示
def get(
    self,
    url: str,
    params: Optional[QueryParams] = None,
    headers: Optional[Headers] = None,
) -> httpx.Response:
    pass
```

**好处**：
1. IDE自动补全
2. 编译时发现错误
3. 更好的文档

**类型别名让代码更清晰**：

```python
# 定义类型别名
Headers = Dict[str, str]
QueryParams = Dict[str, Union[str, int, float, bool]]
JSONData = Dict[str, Any]

# 使用
def post(
    self,
    url: str,
    json: Optional[JSONData] = None,  # 一眼就知道是JSON数据
    headers: Optional[Headers] = None,  # 一眼就知道是Header
) -> httpx.Response:
    pass
```

### 5.2 Enum优于字符串

```python
# ❌ Bad: 魔法字符串
client.request("GET", url)  # 容易拼错
client.request("get", url)  # 大小写不一致
client.request("GTE", url)  # 拼写错误

# ✅ Good: 使用Enum
from enum import Enum

class HTTPMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"

client.request(HTTPMethod.GET, url)  # IDE会提示，不会拼错
```

### 5.3 异常链（Exception Chaining）

```python
# ❌ Bad: 丢失了原始错误信息
try:
    response = httpx.get(url)
except httpx.TimeoutException:
    raise HTTPTimeoutError("Timeout!")  # 原始异常丢失了

# ✅ Good: 保留异常链
try:
    response = httpx.get(url)
except httpx.TimeoutException as e:
    raise HTTPTimeoutError("Timeout!") from e  # 保留原始异常
```

**查看异常链**：

```python
try:
    client.get(url)
except HTTPTimeoutError as e:
    print(f"Our error: {e}")
    print(f"Original error: {e.__cause__}")  # 可以追溯到httpx的原始错误
```

### 5.4 不可变配置（Immutable Configuration）

```python
# ❌ Bad: 可变的默认参数
def __init__(self, default_headers={}):  # 危险！
    self.default_headers = default_headers

# 所有实例会共享同一个字典！
client1 = HTTPClient()
client1.default_headers["X-Custom"] = "value"

client2 = HTTPClient()
print(client2.default_headers)  # 居然有 "X-Custom"！

# ✅ Good: 使用None作为默认值
def __init__(self, default_headers=None):
    self.default_headers = default_headers or {}  # 每次创建新字典
```

### 5.5 日志记录的艺术

```python
import logging

logger = logging.getLogger(__name__)

def request(self, method, url, **kwargs):
    # 请求前：记录请求信息
    logger.debug(f"Making {method} request to {url}")

    try:
        response = self._client.request(method, url, **kwargs)

        # 成功：记录响应信息
        logger.debug(
            f"{method} {url} -> {response.status_code} "
            f"({len(response.content)} bytes)"
        )

        return response

    except Exception as e:
        # 失败：记录错误
        logger.error(f"{method} {url} failed: {str(e)}")
        raise
```

**日志级别使用建议**：

```python
logger.debug("详细的调试信息")  # 开发时使用
logger.info("重要的业务信息")   # 生产环境
logger.warning("警告信息")      # 需要注意
logger.error("错误信息")        # 出错了
```

---

## 6. 使用示例

### 6.1 基础使用

```python
from rookie_agent.http import HTTPClient

# 创建客户端
with HTTPClient(timeout=30.0) as client:
    # GET请求
    response = client.get("https://api.example.com/users")
    users = response.json()

    # POST请求
    response = client.post(
        "https://api.example.com/users",
        json={"name": "Alice", "age": 30}
    )
    new_user = response.json()

    # 带查询参数
    response = client.get(
        "https://api.example.com/search",
        params={"q": "python", "limit": 10}
    )

    # 自定义header
    response = client.get(
        "https://api.example.com/data",
        headers={"Authorization": "Bearer token"}
    )
```

### 6.2 调用OpenAI API

```python
from rookie_agent.http import HTTPClient

class OpenAIClient:
    def __init__(self, api_key):
        self.client = HTTPClient(
            base_url="https://api.openai.com/v1",
            default_headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=60.0,
        )

    def chat_completion(self, messages, model="gpt-4"):
        response = self.client.post(
            "/chat/completions",
            json={
                "model": model,
                "messages": messages,
            }
        )
        return response.json()

# 使用
openai = OpenAIClient(api_key="sk-...")
result = openai.chat_completion([
    {"role": "user", "content": "Hello!"}
])
print(result['choices'][0]['message']['content'])
```

### 6.3 异步使用

```python
import asyncio
from rookie_agent.http import AsyncHTTPClient

async def fetch_users():
    async with AsyncHTTPClient() as client:
        response = await client.get("https://api.example.com/users")
        return response.json()

# 并发请求
async def fetch_multiple():
    async with AsyncHTTPClient() as client:
        # 同时发起多个请求
        tasks = [
            client.get("https://api.example.com/users/1"),
            client.get("https://api.example.com/users/2"),
            client.get("https://api.example.com/users/3"),
        ]
        responses = await asyncio.gather(*tasks)
        return [r.json() for r in responses]

# 运行
users = asyncio.run(fetch_users())
multiple_users = asyncio.run(fetch_multiple())
```

### 6.4 错误处理示例

```python
from rookie_agent.http import (
    HTTPClient,
    HTTPTimeoutError,
    HTTPConnectionError,
    HTTPStatusError,
)

def safe_request(url):
    with HTTPClient(timeout=10.0) as client:
        try:
            return client.get(url)

        except HTTPTimeoutError:
            # 超时：可能需要增加超时时间或者服务有问题
            logger.warning(f"Request to {url} timed out")
            return None

        except HTTPConnectionError:
            # 连接失败：检查网络或URL
            logger.error(f"Cannot connect to {url}")
            return None

        except HTTPStatusError as e:
            # HTTP错误：根据状态码处理
            if e.status_code == 429:  # Rate limit
                logger.warning("Rate limited, need to back off")
                return None
            elif e.status_code >= 500:  # Server error
                logger.error(f"Server error: {e.status_code}")
                return None
            else:
                raise  # 其他错误向上抛出
```

---

## 7. 常见问题

### Q1: 为什么不直接用requests？

**A**: requests很好，但：
1. 不支持异步（在高并发场景性能差）
2. 不支持HTTP/2
3. httpx的API更现代，类型提示更完整

### Q2: 重试次数设置多少合适？

**A**: 取决于场景：
- API调用：3次通常够了
- 关键业务：可以5次
- 非关键：1-2次即可

**过多重试的问题**：
- 增加延迟
- 可能加重服务器负担
- 用户等待时间过长

### Q3: 超时时间怎么设置？

**A**:
```python
# 快速API（查询）
client = HTTPClient(timeout=5.0)

# 普通API
client = HTTPClient(timeout=30.0)

# 慢速API（如文件上传、LLM生成）
client = HTTPClient(timeout=60.0)

# 长轮询
client = HTTPClient(timeout=300.0)
```

### Q4: 什么时候用同步，什么时候用异步？

**同步（HTTPClient）**：
- 简单脚本
- 请求不多
- 不需要高并发

**异步（AsyncHTTPClient）**：
- 需要并发请求多个API
- 构建异步应用（FastAPI）
- 性能要求高

### Q5: 如何调试HTTP请求？

```python
import logging

# 启用详细日志
logging.basicConfig(level=logging.DEBUG)

# 或者只启用http模块的日志
logging.getLogger('rookie_agent.http').setLevel(logging.DEBUG)
```

---

## 8. 总结与延伸

### 8.1 我们学到了什么

1. **设计原则**
   - 单一职责：每个类只做一件事
   - 开闭原则：配置而非修改
   - 依赖倒置：依赖抽象而非实现

2. **重要概念**
   - 指数退避：逐渐增加重试间隔
   - Jitter：防止惊群效应
   - 异常链：保留错误上下文
   - Context Manager：自动资源管理

3. **最佳实践**
   - 完整的类型注解
   - 清晰的错误分类
   - 详细的日志记录
   - 充分的代码注释

### 8.2 下一步学习

1. **Week 2内容预告**：
   - SSE（Server-Sent Events）流式处理
   - 高级重试策略（熔断、限流）
   - 请求追踪和性能分析

2. **扩展阅读**：
   - [httpx官方文档](https://www.python-httpx.org/)
   - [HTTP协议详解](https://developer.mozilla.org/en-US/docs/Web/HTTP)
   - [重试策略最佳实践](https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/)

3. **实践建议**：
   - 尝试修改重试参数，观察行为变化
   - 添加自定义的异常类型
   - 实现请求缓存功能
   - 添加请求/响应的拦截器

### 8.3 思考题

1. 如果要实现请求缓存，应该在哪个层次加入？
2. 如何实现请求的超时重试，但响应慢不重试？
3. 如何统计每个API的平均响应时间？
4. 如何实现请求的rate limiting？

---

## 附录：完整代码结构

```
src/rookie_agent/http/
├── __init__.py           # 导出公共API
├── client.py             # HTTP客户端实现
├── retry.py              # 重试机制
├── exceptions.py         # 异常定义
└── types.py              # 类型定义

tests/unit/http/
├── test_client.py        # 客户端测试
├── test_retry.py         # 重试测试
└── test_types.py         # 类型测试（可选）
```

---

**文档版本**: v1.0
**最后更新**: 2025-10-25
**反馈**: 如有问题，请在GitHub Issue中讨论
