# Retry机制深度解析：从基础到高级

## 目录
1. [什么是重试机制](#什么是重试机制)
2. [为什么需要重试](#为什么需要重试)
3. [重试的挑战](#重试的挑战)
4. [Python高级语法详解](#python高级语法详解)
5. [重试算法深入理解](#重试算法深入理解)
6. [代码逐行解析](#代码逐行解析)
7. [实战示例](#实战示例)
8. [最佳实践](#最佳实践)

---

## 什么是重试机制

### 基础概念

重试机制（Retry Mechanism）是一种容错技术，当某个操作失败时，系统会自动重新尝试执行这个操作，直到成功或达到最大重试次数。

想象一下这些生活场景：
- 📞 打电话时对方占线，你会过一会儿再打
- 🚪 敲门没人应答，你会等一下再敲
- 🌐 网页加载失败，你会刷新重试

在编程中，重试机制解决的是类似的问题：

```python
# 没有重试的代码 - 脆弱
def fetch_data():
    response = requests.get("https://api.example.com/data")
    return response.json()  # 如果网络出错，程序就崩溃了

# 有重试的代码 - 健壮
@retry_on_exception(max_attempts=3)
def fetch_data():
    response = requests.get("https://api.example.com/data")
    return response.json()  # 失败了会自动重试，更可靠
```

---

## 为什么需要重试

### 1. 网络不稳定
互联网环境复杂多变：
- 网络延迟波动
- 临时连接中断
- DNS解析失败
- 服务器临时过载

### 2. 分布式系统的特点
现代应用通常是分布式的：
- 微服务之间的调用
- 数据库连接池耗尽
- 第三方API限流
- 负载均衡器故障

### 3. 提高用户体验
- 避免用户看到错误页面
- 减少手动重试的需要
- 提高系统可用性

### 4. 成本效益
- 自动重试比人工干预成本更低
- 减少客服工单
- 提高系统整体稳定性

---

## 重试的挑战

### 1. 重试风暴（Thundering Herd）
```
时间轴：
0s: 100个请求同时失败
1s: 100个请求同时重试 → 服务器压力更大
2s: 100个请求再次同时重试 → 雪崩效应
```

**解决方案：抖动（Jitter）**
```python
# 不好的做法：所有请求同时重试
delay = 2 ** attempt  # 1s, 2s, 4s, 8s...

# 好的做法：添加随机抖动
delay = (2 ** attempt) * (0.5 + random.random() * 0.5)
# 结果：0.5s-1.5s, 1s-3s, 2s-6s, 4s-12s...
```

### 2. 无限重试
某些错误不应该重试：
- 认证失败（401）
- 权限不足（403）
- 资源不存在（404）
- 参数错误（400）

### 3. 重试成本
- 增加系统负载
- 延长响应时间
- 消耗更多资源

---

## Python高级语法详解

我们的retry代码使用了很多高级Python语法，让我们逐一深入理解。

### 1. 装饰器（Decorator）基础

#### 什么是装饰器？
装饰器是Python的一个强大特性，它允许我们在不修改原函数代码的情况下，给函数添加新功能。

```python
# 最简单的装饰器
def my_decorator(func):
    def wrapper():
        print("在函数执行前做点什么")
        result = func()
        print("在函数执行后做点什么")
        return result
    return wrapper

# 使用装饰器
@my_decorator
def say_hello():
    print("Hello!")

# 等价于：
# say_hello = my_decorator(say_hello)
```

#### 装饰器的执行过程
```python
# 1. Python解释器看到@my_decorator
# 2. 调用my_decorator(say_hello)
# 3. 返回wrapper函数
# 4. 将wrapper赋值给say_hello

# 现在say_hello实际上是wrapper函数
say_hello()
# 输出：
# 在函数执行前做点什么
# Hello!
# 在函数执行后做点什么
```

### 2. 装饰器工厂（Decorator Factory）

我们的retry装饰器是一个装饰器工厂，因为它需要接受参数：

```python
# 这是装饰器工厂的模式
def retry_on_exception(max_attempts=3):  # 外层函数：接受配置参数
    def decorator(func):                 # 中层函数：真正的装饰器
        def wrapper(*args, **kwargs):    # 内层函数：替换原函数
            # 重试逻辑在这里
            pass
        return wrapper
    return decorator

# 使用时的执行过程：
@retry_on_exception(max_attempts=5)
def my_function():
    pass

# 等价于：
# decorator = retry_on_exception(max_attempts=5)  # 返回decorator函数
# my_function = decorator(my_function)            # 返回wrapper函数
```

#### 三层函数的作用
```python
def retry_on_exception(max_attempts=3):    # 第1层：保存配置参数
    config = RetryConfig(max_attempts=max_attempts)
    
    def decorator(func):                   # 第2层：接收被装饰的函数
        def wrapper(*args, **kwargs):      # 第3层：实际执行的函数
            # 这里可以访问：
            # - config (来自第1层)
            # - func (来自第2层)  
            # - args, kwargs (来自第3层)
            for attempt in range(config.max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception:
                    # 重试逻辑
                    pass
        return wrapper
    return decorator
```

### 3. 闭包（Closure）

闭包是装饰器工作的核心机制：

```python
def outer_function(x):
    # 外层函数的变量
    outer_var = x
    
    def inner_function(y):
        # 内层函数可以访问外层函数的变量
        return outer_var + y  # 这就是闭包！
    
    return inner_function

# 创建闭包
add_10 = outer_function(10)
print(add_10(5))  # 输出：15

# 即使outer_function已经执行完毕，
# inner_function仍然"记住"了outer_var的值
```

#### 闭包在retry中的应用
```python
def retry_on_exception(max_attempts=3):
    config = RetryConfig(max_attempts=max_attempts)  # 外层变量
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # wrapper函数形成闭包，可以访问：
            # - config（来自外层作用域）
            # - func（来自外层作用域）
            for attempt in range(config.max_attempts):  # 使用闭包变量
                try:
                    return func(*args, **kwargs)         # 使用闭包变量
                except Exception as e:
                    # 重试逻辑...
                    pass
        return wrapper
    return decorator
```

### 4. @wraps装饰器的重要性

#### 问题：装饰器会"隐藏"原函数信息
```python
def simple_decorator(func):
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

@simple_decorator
def my_function():
    """这是我的函数"""
    pass

print(my_function.__name__)  # 输出：wrapper（不是my_function！）
print(my_function.__doc__)   # 输出：None（文档字符串丢失！）
```

#### 解决方案：使用@wraps
```python
from functools import wraps

def better_decorator(func):
    @wraps(func)  # 这一行很重要！
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

@better_decorator
def my_function():
    """这是我的函数"""
    pass

print(my_function.__name__)  # 输出：my_function ✓
print(my_function.__doc__)   # 输出：这是我的函数 ✓
```

#### @wraps的工作原理
```python
# @wraps(func) 等价于：
wrapper.__name__ = func.__name__
wrapper.__doc__ = func.__doc__
wrapper.__module__ = func.__module__
wrapper.__qualname__ = func.__qualname__
wrapper.__annotations__ = func.__annotations__
wrapper.__wrapped__ = func  # 保存原函数引用
```

### 5. 类型注解（Type Hints）

我们的代码大量使用了类型注解，让我们理解每一个：

#### 基础类型注解
```python
def simple_function(name: str, age: int) -> str:
    return f"{name} is {age} years old"

# name: str     - 参数name应该是字符串类型
# age: int      - 参数age应该是整数类型  
# -> str        - 函数返回值应该是字符串类型
```

#### 复杂类型注解
```python
from typing import Callable, Type, Tuple, Optional, Any

# Callable - 可调用对象（函数）
def decorator(func: Callable) -> Callable:
    # func是一个函数，返回值也是一个函数
    pass

# 更精确的Callable注解
def decorator(func: Callable[[int, str], bool]) -> Callable:
    # func接受(int, str)参数，返回bool
    pass

# Type - 类型对象
def handle_exception(exc_type: Type[Exception]) -> None:
    # exc_type是一个异常类（不是异常实例）
    pass

# Tuple - 元组，指定每个元素的类型
retry_on: Tuple[Type[Exception], ...] = (ValueError, TypeError)
# 这是一个元组，包含异常类型，...表示可变长度

# Optional - 可选类型（可以是None）
last_exception: Optional[Exception] = None
# 等价于：Union[Exception, None]

# Any - 任意类型
def wrapper(*args: Any, **kwargs: Any) -> Any:
    # 参数和返回值可以是任意类型
    pass
```

### 6. 异步编程（Async/Await）

#### 同步vs异步的区别
```python
# 同步版本 - 阻塞式
def sync_function():
    time.sleep(1)  # 阻塞1秒，什么都不能做
    return "done"

# 异步版本 - 非阻塞式  
async def async_function():
    await asyncio.sleep(1)  # 让出控制权，可以做其他事
    return "done"
```

#### 异步装饰器的特殊性
```python
# 错误的异步装饰器定义
async def wrong_async_decorator(func):  # ❌ 这是错的！
    async def wrapper(*args, **kwargs):
        return await func(*args, **kwargs)
    return wrapper

# 正确的异步装饰器定义
def correct_async_decorator(func):      # ✓ 外层是普通函数
    async def wrapper(*args, **kwargs): # ✓ 内层是异步函数
        return await func(*args, **kwargs)
    return wrapper
```

#### 为什么外层不能是async？
```python
# 如果外层是async，使用时会出问题：
@wrong_async_decorator  # 这里Python期望得到一个函数
async def my_async_func():
    pass

# 但wrong_async_decorator是async函数，不能直接调用
# Python会报错：TypeError: 'coroutine' object is not callable
```

---

## 重试算法深入理解

### 1. 指数退避（Exponential Backoff）

#### 基本概念
指数退避是一种逐渐增加等待时间的策略：

```
尝试次数    等待时间
   1    →    1秒
   2    →    2秒  
   3    →    4秒
   4    →    8秒
   5    →   16秒
```

#### 数学公式
```python
delay = base_delay * (exponential_base ** attempt)

# 例如：base_delay=1, exponential_base=2
# attempt=0: delay = 1 * (2^0) = 1 * 1 = 1秒
# attempt=1: delay = 1 * (2^1) = 1 * 2 = 2秒  
# attempt=2: delay = 1 * (2^2) = 1 * 4 = 4秒
```

#### 为什么使用指数退避？
```python
# 线性退避的问题
delays = [1, 2, 3, 4, 5]  # 增长太慢，可能无法避开高峰

# 指数退避的优势  
delays = [1, 2, 4, 8, 16]  # 快速拉开间隔，避开拥堵
```

#### 代码实现详解
```python
def calculate_delay(self, attempt: int) -> float:
    # 第1步：计算基础指数退避
    delay = self.base_delay * (self.exponential_base ** attempt)
    
    # 第2步：限制最大延迟（防止等待时间过长）
    delay = min(delay, self.max_delay)
    
    # 第3步：添加抖动（防止重试风暴）
    if self.jitter:
        delay = delay * (0.5 + random.random() * 0.5)
    
    return delay
```

### 2. 抖动（Jitter）

#### 问题：重试风暴
```
场景：100个客户端同时访问服务器
12:00:00 - 服务器故障，100个请求失败
12:00:01 - 100个请求同时重试 → 服务器压力翻倍
12:00:02 - 100个请求再次同时重试 → 雪崩效应
```

#### 解决方案：随机抖动
```python
# 没有抖动：所有客户端同时重试
delay = 2 ** attempt  # 1, 2, 4, 8...

# 有抖动：重试时间分散
delay = delay * (0.5 + random.random() * 0.5)

# 结果对比：
# 原始：1秒, 2秒, 4秒, 8秒
# 抖动：0.5-1.5秒, 1-3秒, 2-6秒, 4-12秒
```

#### 抖动算法详解
```python
# 我们使用的抖动公式
jitter_factor = 0.5 + random.random() * 0.5

# 分解：
# random.random()        → 0.0 到 1.0 的随机数
# random.random() * 0.5  → 0.0 到 0.5 的随机数  
# 0.5 + (上面的结果)      → 0.5 到 1.0 的随机数

# 效果：
# 最小延迟 = delay * 0.5  (减少50%)
# 最大延迟 = delay * 1.0  (保持原样)
# 平均延迟 = delay * 0.75 (减少25%)
```

#### 可视化抖动效果
```
无抖动的重试时间线：
客户端A: |--1s--|--2s--|--4s--|
客户端B: |--1s--|--2s--|--4s--|  
客户端C: |--1s--|--2s--|--4s--|
         ↑      ↑      ↑
      同时重试 同时重试 同时重试

有抖动的重试时间线：
客户端A: |--0.8s--|--1.5s--|--3.2s--|
客户端B: |--1.2s--|--2.8s--|--5.1s--|
客户端C: |--0.6s--|--2.1s--|--4.7s--|
         ↑        ↑        ↑
      分散重试   分散重试   分散重试
```

### 3. 选择性重试

#### 不是所有错误都应该重试
```python
# 应该重试的错误（临时性）
- ConnectionError      # 网络连接问题
- TimeoutError        # 超时
- 500 Internal Server Error  # 服务器内部错误
- 502 Bad Gateway     # 网关错误
- 503 Service Unavailable   # 服务不可用

# 不应该重试的错误（永久性）
- 400 Bad Request     # 请求参数错误
- 401 Unauthorized    # 认证失败
- 403 Forbidden       # 权限不足  
- 404 Not Found       # 资源不存在
```

#### 代码实现
```python
def should_retry(self, exception: Exception) -> bool:
    """检查异常是否应该重试"""
    return isinstance(exception, self.retry_on)

# 使用示例
@retry_on_exception(
    max_attempts=3,
    retry_on=(ConnectionError, TimeoutError)  # 只重试这些异常
)
def fetch_data():
    # 如果发生ValueError，不会重试，直接抛出
    # 如果发生ConnectionError，会重试
    pass
```

---

## 代码逐行解析

现在让我们逐行分析retry.py的核心代码：

### RetryConfig类解析

```python
class RetryConfig:
    """配置类 - 封装所有重试相关的配置"""
    
    def __init__(
        self,
        max_attempts: int = 3,                    # 最大重试次数
        base_delay: float = 1.0,                  # 基础延迟时间
        max_delay: float = 60.0,                  # 最大延迟时间
        exponential_base: float = 2.0,            # 指数底数
        jitter: bool = True,                      # 是否启用抖动
        retry_on: Tuple[Type[Exception], ...] = (Exception,),  # 重试的异常类型
    ) -> None:
```

**设计思想：单一职责原则**
- 这个类只负责管理配置，不处理重试逻辑
- 所有配置项都有合理的默认值
- 类型注解清晰表明每个参数的期望类型

### 延迟计算方法

```python
def calculate_delay(self, attempt: int) -> float:
    # 第1步：指数退避计算
    delay = self.base_delay * (self.exponential_base ** attempt)
    
    # 第2步：限制最大延迟
    delay = min(delay, self.max_delay)
    
    # 第3步：添加随机抖动
    if self.jitter:
        delay = delay * (0.5 + random.random() * 0.5)
    
    return delay
```

**逐步分析：**
1. `self.exponential_base ** attempt`：计算指数值
2. `min(delay, self.max_delay)`：防止延迟时间过长
3. `0.5 + random.random() * 0.5`：生成0.5-1.0的随机因子

### 同步重试装饰器

```python
def retry_on_exception(
    max_attempts: int = 3,
    # ... 其他参数
) -> Callable:
    # 第1层：创建配置对象
    config = RetryConfig(
        max_attempts=max_attempts,
        # ... 其他配置
    )
    
    # 第2层：装饰器函数
    def decorator(func: Callable) -> Callable:
        
        # 第3层：包装函数
        @wraps(func)  # 保持原函数元数据
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception: Optional[Exception] = None
            
            # 重试循环
            for attempt in range(config.max_attempts):
                try:
                    # 尝试执行原函数
                    return func(*args, **kwargs)
                    
                except Exception as e:
                    last_exception = e
                    
                    # 检查是否应该重试
                    if not config.should_retry(e):
                        logger.debug(f"不重试 {func.__name__} - 异常类型不匹配")
                        raise  # 直接抛出异常
                    
                    # 检查是否还有重试机会
                    if attempt >= config.max_attempts - 1:
                        logger.warning(f"重试耗尽 {func.__name__}")
                        break  # 跳出循环，抛出RetryExhaustedError
                    
                    # 计算延迟并等待
                    delay = config.calculate_delay(attempt)
                    logger.info(f"重试 {attempt + 1}/{config.max_attempts}")
                    time.sleep(delay)
            
            # 所有重试都失败了
            raise RetryExhaustedError(
                f"重试{config.max_attempts}次后失败",
                attempts=config.max_attempts,
                last_exception=last_exception or Exception("未知错误"),
            )
        
        return wrapper
    return decorator
```

**关键点解析：**

1. **三层函数结构**：
   - 外层：接收配置参数
   - 中层：接收被装饰的函数
   - 内层：实际执行的包装函数

2. **异常处理逻辑**：
   ```python
   # 流程图：
   执行函数 → 成功？ → 返回结果
       ↓         
     失败
       ↓
   应该重试？ → 否 → 直接抛出异常
       ↓
      是
       ↓  
   还有重试次数？ → 否 → 抛出RetryExhaustedError
       ↓
      是
       ↓
   等待延迟时间 → 继续下次重试
   ```

3. **@wraps的作用**：
   ```python
   # 没有@wraps
   print(wrapper.__name__)  # 输出：wrapper
   
   # 有@wraps  
   print(wrapper.__name__)  # 输出：原函数名
   ```

### 异步重试装饰器

```python
def async_retry_on_exception(
    # ... 参数同同步版本
) -> Callable:
    import asyncio  # 导入异步库
    
    config = RetryConfig(...)  # 创建配置
    
    def decorator(func: Callable) -> Callable:  # 注意：这里是普通函数
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:  # 这里是异步函数
            last_exception: Optional[Exception] = None
            
            for attempt in range(config.max_attempts):
                try:
                    return await func(*args, **kwargs)  # 使用await调用
                except Exception as e:
                    # ... 异常处理逻辑相同
                    
                    # 关键区别：使用异步睡眠
                    await asyncio.sleep(delay)  # 而不是time.sleep(delay)
            
            raise RetryExhaustedError(...)
        
        return wrapper
    return decorator
```

**异步版本的关键区别：**

1. **装饰器定义**：
   ```python
   # 错误：外层函数不能是async
   async def async_retry_on_exception(...):  # ❌
   
   # 正确：外层是普通函数，内层是async
   def async_retry_on_exception(...):        # ✓
       async def wrapper(...):               # ✓
   ```

2. **函数调用**：
   ```python
   # 同步版本
   return func(*args, **kwargs)
   
   # 异步版本  
   return await func(*args, **kwargs)
   ```

3. **睡眠函数**：
   ```python
   # 同步版本
   time.sleep(delay)
   
   # 异步版本
   await asyncio.sleep(delay)
   ```

---

## 实战示例

### 示例1：HTTP请求重试

```python
import requests
from rookie_agent.http.retry import retry_on_exception

@retry_on_exception(
    max_attempts=3,
    base_delay=1.0,
    retry_on=(requests.ConnectionError, requests.Timeout)
)
def fetch_user_data(user_id: int):
    """获取用户数据，网络错误时自动重试"""
    response = requests.get(f"https://api.example.com/users/{user_id}")
    response.raise_for_status()  # 4xx, 5xx会抛出异常
    return response.json()

# 使用示例
try:
    user = fetch_user_data(123)
    print(f"用户名：{user['name']}")
except RetryExhaustedError as e:
    print(f"获取用户数据失败：{e}")
    print(f"重试了{e.attempts}次")
    print(f"最后的错误：{e.last_exception}")
```

### 示例2：数据库操作重试

```python
import sqlite3
from rookie_agent.http.retry import retry_on_exception

@retry_on_exception(
    max_attempts=5,
    base_delay=0.1,
    max_delay=2.0,
    retry_on=(sqlite3.OperationalError,)  # 只重试操作错误
)
def save_user(name: str, email: str):
    """保存用户，数据库锁定时自动重试"""
    conn = sqlite3.connect('users.db')
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (name, email) VALUES (?, ?)",
            (name, email)
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()

# 使用示例
user_id = save_user("张三", "zhangsan@example.com")
print(f"用户保存成功，ID：{user_id}")
```

### 示例3：异步API调用

```python
import aiohttp
from rookie_agent.http.retry import async_retry_on_exception

@async_retry_on_exception(
    max_attempts=3,
    base_delay=0.5,
    exponential_base=1.5,  # 较温和的指数增长
    retry_on=(aiohttp.ClientError,)
)
async def fetch_weather(city: str):
    """异步获取天气数据"""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.weather.com/{city}") as response:
            response.raise_for_status()
            return await response.json()

# 使用示例
import asyncio

async def main():
    try:
        weather = await fetch_weather("北京")
        print(f"北京天气：{weather['temperature']}°C")
    except RetryExhaustedError as e:
        print(f"获取天气失败：{e}")

asyncio.run(main())
```

### 示例4：自定义重试条件

```python
from rookie_agent.http.retry import retry_on_exception
import requests

# 自定义异常类
class RateLimitError(Exception):
    pass

class ServerBusyError(Exception):
    pass

def check_response(response):
    """检查响应并抛出相应异常"""
    if response.status_code == 429:  # Too Many Requests
        raise RateLimitError("API调用频率过高")
    elif response.status_code >= 500:  # Server Error
        raise ServerBusyError("服务器繁忙")
    response.raise_for_status()

@retry_on_exception(
    max_attempts=5,
    base_delay=2.0,
    max_delay=30.0,
    # 只重试服务器繁忙，不重试频率限制
    retry_on=(ServerBusyError, requests.ConnectionError)
)
def call_api(endpoint: str):
    """调用API，智能重试"""
    response = requests.get(f"https://api.example.com/{endpoint}")
    check_response(response)
    return response.json()

# 使用示例
try:
    data = call_api("data")
    print("API调用成功")
except RateLimitError:
    print("API调用频率过高，请稍后再试")
except RetryExhaustedError as e:
    print(f"API调用失败，已重试{e.attempts}次")
```

---

## 最佳实践

### 1. 选择合适的重试参数

```python
# 网络请求：中等重试强度
@retry_on_exception(
    max_attempts=3,
    base_delay=1.0,
    max_delay=10.0,
    exponential_base=2.0
)

# 数据库操作：快速重试
@retry_on_exception(
    max_attempts=5,
    base_delay=0.1,
    max_delay=2.0,
    exponential_base=1.5
)

# 外部API：保守重试
@retry_on_exception(
    max_attempts=2,
    base_delay=2.0,
    max_delay=30.0,
    exponential_base=3.0
)
```

### 2. 合理设置重试异常

```python
# ✓ 好的做法：明确指定要重试的异常
@retry_on_exception(
    retry_on=(ConnectionError, TimeoutError, requests.HTTPError)
)

# ❌ 不好的做法：重试所有异常
@retry_on_exception(
    retry_on=(Exception,)  # 太宽泛了
)
```

### 3. 添加详细日志

```python
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@retry_on_exception(max_attempts=3)
def risky_operation():
    logger.info("开始执行风险操作")
    # ... 操作代码
    logger.info("操作成功完成")

# retry装饰器会自动记录重试日志：
# INFO: 重试 1/3 for risky_operation after 1.23s - Error: Connection failed
# INFO: 重试 2/3 for risky_operation after 2.45s - Error: Connection failed  
# WARNING: 重试耗尽 risky_operation after 3 attempts
```

### 4. 监控和告警

```python
from rookie_agent.http.retry import RetryExhaustedError
import time

def monitor_retry_failures(func):
    """监控重试失败的装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            return func(*args, **kwargs)
        except RetryExhaustedError as e:
            duration = time.time() - start_time
            
            # 发送告警
            send_alert(
                message=f"函数{func.__name__}重试失败",
                attempts=e.attempts,
                duration=duration,
                last_error=str(e.last_exception)
            )
            raise
    return wrapper

@monitor_retry_failures
@retry_on_exception(max_attempts=3)
def critical_operation():
    # 关键操作
    pass
```

### 5. 测试重试逻辑

```python
import pytest
from unittest.mock import Mock, patch
from rookie_agent.http.retry import retry_on_exception, RetryExhaustedError

def test_retry_success_on_second_attempt():
    """测试第二次重试成功"""
    mock_func = Mock()
    mock_func.side_effect = [ConnectionError("网络错误"), "成功"]
    
    @retry_on_exception(max_attempts=3, base_delay=0.01)  # 快速测试
    def test_func():
        return mock_func()
    
    result = test_func()
    
    assert result == "成功"
    assert mock_func.call_count == 2  # 调用了2次

def test_retry_exhausted():
    """测试重试耗尽"""
    mock_func = Mock()
    mock_func.side_effect = ConnectionError("持续网络错误")
    
    @retry_on_exception(max_attempts=2, base_delay=0.01)
    def test_func():
        return mock_func()
    
    with pytest.raises(RetryExhaustedError) as exc_info:
        test_func()
    
    assert exc_info.value.attempts == 2
    assert isinstance(exc_info.value.last_exception, ConnectionError)

def test_no_retry_on_wrong_exception():
    """测试不应重试的异常"""
    @retry_on_exception(
        max_attempts=3,
        retry_on=(ConnectionError,)  # 只重试连接错误
    )
    def test_func():
        raise ValueError("参数错误")  # 不在重试列表中
    
    with pytest.raises(ValueError):  # 直接抛出，不重试
        test_func()
```

---

## 总结

通过这份详细的解析，我们深入理解了retry机制的方方面面：

### 核心概念回顾
1. **重试机制**：自动重新执行失败的操作
2. **指数退避**：逐渐增加重试间隔
3. **抖动**：添加随机性避免重试风暴
4. **选择性重试**：只重试特定类型的错误

### Python高级语法
1. **装饰器工厂**：三层函数结构
2. **闭包**：内层函数访问外层变量
3. **@wraps**：保持函数元数据
4. **类型注解**：提高代码可读性
5. **异步编程**：非阻塞式重试

### 实践要点
1. 合理设置重试参数
2. 明确指定重试异常类型
3. 添加详细日志记录
4. 实施监控和告警
5. 编写完整的测试用例

retry机制是构建健壮分布式系统的基础组件，掌握其原理和实现对于Python开发者来说非常重要。希望这份解析能帮助你深入理解并正确使用重试机制！