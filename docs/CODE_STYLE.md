# Python 代码规范

## 概述

本项目遵循 [PEP 8](https://peps.python.org/pep-0008/) Python代码风格指南，并在此基础上制定了一些额外的规范。

---

## 代码格式化工具

### 必须使用的工具

1. **Black** - 代码格式化
   ```bash
   black src/ tests/
   ```

2. **isort** - import排序
   ```bash
   isort src/ tests/
   ```

3. **flake8** - 代码检查
   ```bash
   flake8 src/ tests/
   ```

4. **mypy** - 类型检查
   ```bash
   mypy src/
   ```

### 工具配置

在 `pyproject.toml` 中配置：

```toml
[tool.black]
line-length = 100
target-version = ['py310']
include = '\.pyi?$'

[tool.isort]
profile = "black"
line_length = 100
multi_line_output = 3
include_trailing_comma = true

[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

在 `.flake8` 中配置：

```ini
[flake8]
max-line-length = 100
extend-ignore = E203, W503
exclude = .git,__pycache__,build,dist,.venv
```

---

## 命名规范

### 1. 模块和包

- 使用小写字母
- 单词之间用下划线分隔
- 简短且描述性强

```python
# Good ✅
llm_provider.py
tool_registry.py
memory_manager.py

# Bad ❌
LLMProvider.py
toolRegistry.py
mem.py
```

### 2. 类名

- 使用 CapWords (大驼峰) 命名
- 名词或名词短语
- 清晰表达类的职责

```python
# Good ✅
class OpenAIProvider:
    pass

class ToolRegistry:
    pass

class MemoryManager:
    pass

# Bad ❌
class openai_provider:  # 应该用大驼峰
    pass

class Tool_Registry:  # 不应该有下划线
    pass

class MM:  # 太简短，不清晰
    pass
```

### 3. 函数和方法

- 使用小写字母
- 单词之间用下划线分隔
- 动词或动词短语
- 清晰表达函数的动作

```python
# Good ✅
def get_provider():
    pass

def register_tool():
    pass

def execute_task():
    pass

# Bad ❌
def GetProvider():  # 应该用小写
    pass

def registertool():  # 缺少下划线
    pass

def do():  # 太模糊
    pass
```

### 4. 变量名

- 使用小写字母
- 单词之间用下划线分隔
- 描述性强，避免单字母（除循环变量）

```python
# Good ✅
user_name = "Alice"
max_retries = 3
is_valid = True
tool_list = []

# Bad ❌
UserName = "Alice"  # 应该用小写
maxretries = 3  # 缺少下划线
x = True  # 不清晰
t = []  # 太简短
```

### 5. 常量

- 全大写字母
- 单词之间用下划线分隔
- 通常定义在模块级别

```python
# Good ✅
MAX_RETRY_COUNT = 3
DEFAULT_TIMEOUT = 30
API_BASE_URL = "https://api.example.com"

# Bad ❌
max_retry_count = 3  # 应该全大写
DefaultTimeout = 30  # 应该全大写加下划线
```

### 6. 私有属性和方法

- 单下划线前缀：内部使用，但可以访问
- 双下划线前缀：强私有，触发名称改编

```python
class MyClass:
    def __init__(self):
        self.public_attr = "public"
        self._internal_attr = "internal"
        self.__private_attr = "private"

    def public_method(self):
        pass

    def _internal_method(self):
        """内部使用，但子类可以访问"""
        pass

    def __private_method(self):
        """强私有，触发名称改编"""
        pass
```

---

## 类型注解

### 强制要求

所有公共API必须有类型注解：

```python
from typing import List, Dict, Optional, Union, Any

# Good ✅
def process_messages(
    messages: List[Dict[str, str]],
    max_tokens: int = 100,
    temperature: Optional[float] = None
) -> Dict[str, Any]:
    """Process messages and return result.

    Args:
        messages: List of message dictionaries
        max_tokens: Maximum number of tokens
        temperature: Sampling temperature

    Returns:
        Processing result dictionary
    """
    result: Dict[str, Any] = {}
    return result

# Bad ❌
def process_messages(messages, max_tokens=100, temperature=None):
    result = {}
    return result
```

### 复杂类型

使用 `typing` 模块的高级类型：

```python
from typing import (
    List, Dict, Set, Tuple,
    Optional, Union, Any,
    Callable, TypeVar, Generic,
    Protocol, Literal
)

# 回调函数
Callback = Callable[[str], None]

# 泛型
T = TypeVar('T')

class Container(Generic[T]):
    def __init__(self, value: T) -> None:
        self.value = value

    def get(self) -> T:
        return self.value

# 字面量类型
Mode = Literal["train", "eval", "inference"]

# Protocol (结构化子类型)
class Runnable(Protocol):
    def run(self) -> None:
        ...
```

### Python 3.10+ 新语法

如果使用Python 3.10+，可以使用新的类型联合语法：

```python
# Python 3.10+
def process(value: int | str | None) -> dict[str, any]:
    pass

# Python 3.9-
from typing import Union, Dict, Any, Optional

def process(value: Union[int, str, None]) -> Dict[str, Any]:
    pass
```

---

## 文档字符串 (Docstrings)

### 格式

使用 Google风格 的docstring：

```python
def complex_function(
    arg1: str,
    arg2: List[int],
    arg3: Optional[float] = None
) -> Dict[str, Any]:
    """一行简短描述（以句号结束）。

    可选的详细描述，解释函数的行为、算法、
    注意事项等。可以多行。

    Args:
        arg1: 第一个参数的描述
        arg2: 第二个参数的描述
        arg3: 第三个参数的描述。默认为None

    Returns:
        返回值的描述，说明字典中包含哪些键值

    Raises:
        ValueError: 当arg1为空时抛出
        RuntimeError: 当处理失败时抛出

    Examples:
        >>> result = complex_function("test", [1, 2, 3])
        >>> print(result['status'])
        success

    Note:
        这里可以添加额外的注意事项
    """
    if not arg1:
        raise ValueError("arg1 cannot be empty")

    return {"status": "success", "data": arg2}
```

### 类的文档字符串

```python
class ToolRegistry:
    """工具注册中心，管理所有可用的工具。

    ToolRegistry维护一个工具映射表，提供注册、
    查找、调用工具的功能。所有工具必须实现Tool接口。

    Attributes:
        tools: 工具名称到工具实例的映射
        max_tools: 最大允许注册的工具数量

    Examples:
        >>> registry = ToolRegistry()
        >>> registry.register(my_tool)
        >>> tool = registry.get("my_tool")
    """

    def __init__(self, max_tools: int = 100):
        """初始化工具注册中心。

        Args:
            max_tools: 最大工具数量限制
        """
        self.tools: Dict[str, Tool] = {}
        self.max_tools = max_tools
```

### 模块级文档字符串

```python
"""LLM Provider抽象层。

本模块定义了LLM提供商的统一接口，以及各个具体
提供商的实现。支持OpenAI、Azure、本地模型等。

主要类:
    - BaseLLMProvider: 所有LLM提供商的基类
    - OpenAIProvider: OpenAI API的实现
    - AzureProvider: Azure OpenAI的实现

使用示例:
    >>> from rookie_agent.llm.providers import OpenAIProvider
    >>> provider = OpenAIProvider(api_key="sk-...")
    >>> response = provider.generate("Hello, world!")
"""

from abc import ABC, abstractmethod
# ...
```

---

## 代码组织

### 导入顺序

按照以下顺序组织import，每组之间空一行：

1. 标准库
2. 第三方库
3. 本地应用/库

```python
# 标准库
import os
import sys
from typing import List, Dict, Optional
from pathlib import Path

# 第三方库
import numpy as np
from pydantic import BaseModel
from langchain.schema import BaseMessage

# 本地应用
from rookie_agent.core.base import Agent
from rookie_agent.llm.provider import BaseLLMProvider
from rookie_agent.tools import ToolRegistry
```

### 类内部组织

按照以下顺序组织类成员：

```python
class MyClass:
    """类文档字符串"""

    # 1. 类变量
    class_var: str = "value"

    # 2. __init__
    def __init__(self, arg: str):
        self.instance_var = arg

    # 3. 类方法
    @classmethod
    def from_config(cls, config: dict):
        return cls(config["arg"])

    # 4. 静态方法
    @staticmethod
    def helper_function():
        pass

    # 5. 属性
    @property
    def value(self) -> str:
        return self.instance_var

    # 6. 公共方法
    def public_method(self):
        pass

    # 7. 内部方法
    def _internal_method(self):
        pass

    # 8. 私有方法
    def __private_method(self):
        pass

    # 9. 魔法方法（除__init__外）
    def __str__(self) -> str:
        return f"MyClass({self.instance_var})"

    def __repr__(self) -> str:
        return f"MyClass(arg={self.instance_var!r})"
```

---

## 最佳实践

### 1. 函数长度

- 单个函数不超过50行
- 如果超过，考虑拆分成多个小函数
- 每个函数只做一件事

```python
# Good ✅
def process_data(data: List[dict]) -> List[dict]:
    """处理数据的主函数"""
    validated = _validate_data(data)
    normalized = _normalize_data(validated)
    transformed = _transform_data(normalized)
    return transformed

def _validate_data(data: List[dict]) -> List[dict]:
    """验证数据有效性"""
    return [d for d in data if d.get("valid")]

def _normalize_data(data: List[dict]) -> List[dict]:
    """标准化数据格式"""
    return [_normalize_item(d) for d in data]

def _transform_data(data: List[dict]) -> List[dict]:
    """转换数据结构"""
    return [_transform_item(d) for d in data]

# Bad ❌
def process_data(data):
    """一个超长的函数，做了太多事情"""
    # 100+ lines of code...
```

### 2. 使用上下文管理器

```python
# Good ✅
with open("file.txt", "r") as f:
    content = f.read()

# Bad ❌
f = open("file.txt", "r")
content = f.read()
f.close()
```

### 3. 列表推导式 vs 循环

简单情况使用列表推导式，复杂情况使用循环：

```python
# Good ✅ - 简单转换
squares = [x**2 for x in range(10)]

# Good ✅ - 复杂逻辑使用循环
results = []
for item in items:
    if item.is_valid():
        processed = item.process()
        if processed:
            results.append(processed)

# Bad ❌ - 过度复杂的推导式
results = [
    item.process()
    for item in items
    if item.is_valid() and item.process() is not None
]  # process()被调用了两次！
```

### 4. 异常处理

```python
# Good ✅
def divide(a: float, b: float) -> float:
    """除法运算"""
    try:
        return a / b
    except ZeroDivisionError as e:
        logger.error(f"Division by zero: {e}")
        raise ValueError("Divisor cannot be zero") from e
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

# Bad ❌
def divide(a, b):
    try:
        return a / b
    except:  # 不要使用裸except
        pass  # 不要静默错误
```

### 5. 使用Enum代替魔法值

```python
from enum import Enum

# Good ✅
class Status(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

def check_status(status: Status) -> bool:
    return status == Status.COMPLETED

# Bad ❌
def check_status(status: str) -> bool:
    return status == "completed"  # 魔法字符串
```

### 6. 使用dataclass

```python
from dataclasses import dataclass, field
from typing import List

# Good ✅
@dataclass
class Config:
    """配置类"""
    name: str
    max_retries: int = 3
    timeout: float = 30.0
    tags: List[str] = field(default_factory=list)

# Bad ❌
class Config:
    def __init__(self, name, max_retries=3, timeout=30.0, tags=None):
        self.name = name
        self.max_retries = max_retries
        self.timeout = timeout
        self.tags = tags or []
```

### 7. 使用f-string

```python
# Good ✅
name = "Alice"
age = 30
message = f"Hello, {name}! You are {age} years old."

# Acceptable
message = f"Hello, {name}! " \
          f"You are {age} years old."

# Bad ❌
message = "Hello, " + name + "! You are " + str(age) + " years old."
message = "Hello, {}! You are {} years old.".format(name, age)
```

### 8. 提前返回

```python
# Good ✅
def process(value: Optional[str]) -> str:
    if value is None:
        return ""

    if not value.strip():
        return ""

    if len(value) > 100:
        return value[:100]

    return value.upper()

# Bad ❌
def process(value):
    if value is not None:
        if value.strip():
            if len(value) <= 100:
                result = value.upper()
            else:
                result = value[:100]
        else:
            result = ""
    else:
        result = ""
    return result
```

### 9. 避免可变默认参数

```python
# Good ✅
def append_to_list(item: str, target: Optional[List[str]] = None) -> List[str]:
    if target is None:
        target = []
    target.append(item)
    return target

# Bad ❌
def append_to_list(item: str, target: List[str] = []) -> List[str]:
    target.append(item)  # 危险！会修改默认参数
    return target
```

### 10. 使用pathlib处理路径

```python
from pathlib import Path

# Good ✅
config_path = Path("configs") / "default.yaml"
if config_path.exists():
    content = config_path.read_text()

# Bad ❌
import os
config_path = os.path.join("configs", "default.yaml")
if os.path.exists(config_path):
    with open(config_path) as f:
        content = f.read()
```

---

## 注释规范

### 1. 什么时候写注释

- ✅ 解释"为什么"这样做（Why）
- ✅ 说明复杂算法的思路
- ✅ 标注TODO、FIXME、HACK等
- ❌ 不要重复代码已经说明的内容（What）

```python
# Good ✅
# 使用二分查找以提高大数据集的性能
def find_item(items: List[int], target: int) -> int:
    # TODO: 考虑使用插值查找进一步优化
    left, right = 0, len(items) - 1
    ...

# Bad ❌
# 设置变量x为10
x = 10  # 这个注释毫无意义
```

### 2. 注释标签

```python
# TODO: 待实现的功能
# FIXME: 需要修复的bug
# HACK: 临时解决方案，需要重构
# NOTE: 重要说明
# WARNING: 警告信息
# OPTIMIZE: 性能优化点
```

---

## 测试代码规范

### 测试函数命名

```python
# Good ✅
def test_tool_registry_register_new_tool():
    """测试注册新工具的功能"""
    pass

def test_tool_registry_register_duplicate_tool_raises_error():
    """测试重复注册工具时抛出异常"""
    pass

# Bad ❌
def test1():
    pass

def test_register():  # 不够具体
    pass
```

### 测试结构

使用AAA模式（Arrange-Act-Assert）：

```python
def test_openai_provider_generate():
    """测试OpenAI提供商的文本生成功能"""
    # Arrange - 准备测试数据
    provider = OpenAIProvider(api_key="test-key")
    prompt = "Hello, world!"

    # Act - 执行测试操作
    result = provider.generate(prompt)

    # Assert - 验证结果
    assert result is not None
    assert isinstance(result, str)
    assert len(result) > 0
```

---

## 代码审查检查清单

在提交代码前，确保：

- [ ] 代码通过 `black` 格式化
- [ ] 代码通过 `isort` 排序
- [ ] 代码通过 `flake8` 检查
- [ ] 代码通过 `mypy` 类型检查
- [ ] 所有公共函数都有类型注解
- [ ] 所有公共API都有文档字符串
- [ ] 复杂逻辑有必要的注释
- [ ] 没有遗留的print语句（使用logger）
- [ ] 没有遗留的调试代码
- [ ] 测试覆盖率达标

---

**最后更新**: 2025-10-25
**维护者**: Rookie Agent Team
