# 开发指南

## 目录

1. [开发环境设置](#开发环境设置)
2. [开发工作流](#开发工作流)
3. [测试规范](#测试规范)
4. [文档规范](#文档规范)
5. [性能优化指南](#性能优化指南)
6. [安全规范](#安全规范)
7. [常见问题](#常见问题)

---

## 开发环境设置

### 系统要求

- Python 3.10+
- Git 2.30+
- 8GB+ RAM
- 10GB+ 可用磁盘空间

### 环境安装步骤

#### 1. 克隆项目

```bash
git clone https://github.com/your-org/rookie-agent.git
cd rookie-agent
```

#### 2. 创建虚拟环境

```bash
# 使用venv
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate  # Windows

# 或使用conda
conda create -n rookie-agent python=3.10
conda activate rookie-agent
```

#### 3. 安装依赖

```bash
# 安装生产依赖
pip install -r requirements.txt

# 安装开发依赖
pip install -r requirements-dev.txt

# 或使用pip-tools
pip-sync requirements.txt requirements-dev.txt

# 或使用poetry
poetry install
```

#### 4. 安装开发工具

```bash
# 代码格式化工具
pip install black isort

# 代码检查工具
pip install flake8 mypy pylint

# 测试工具
pip install pytest pytest-cov pytest-mock pytest-asyncio

# 文档工具
pip install mkdocs mkdocs-material

# 预提交钩子
pip install pre-commit
pre-commit install
```

#### 5. 配置环境变量

创建 `.env` 文件：

```bash
# 复制模板
cp .env.example .env

# 编辑配置
# OPENAI_API_KEY=your-api-key
# AZURE_OPENAI_ENDPOINT=your-endpoint
# LOG_LEVEL=DEBUG
```

#### 6. 验证安装

```bash
# 运行测试
pytest tests/

# 检查代码风格
black --check src/
flake8 src/
mypy src/

# 运行示例
python examples/hello_agent.py
```

---

## 开发工作流

### 日常开发流程

#### 1. 开始新功能

```bash
# 更新develop分支
git checkout develop
git pull origin develop

# 创建功能分支
git checkout -b feature/your-feature-name

# 创建对应的测试文件
touch tests/test_your_feature.py
```

#### 2. TDD开发循环

遵循 **红-绿-重构** 循环：

```python
# 1. 红：先写测试（会失败）
# tests/test_tool_registry.py
def test_register_tool():
    registry = ToolRegistry()
    tool = MyTool()

    registry.register(tool)

    assert "my_tool" in registry.tools
    assert registry.get("my_tool") == tool

# 2. 绿：写最少的代码让测试通过
# src/tools/registry.py
class ToolRegistry:
    def __init__(self):
        self.tools = {}

    def register(self, tool):
        self.tools[tool.name] = tool

    def get(self, name):
        return self.tools.get(name)

# 3. 重构：优化代码，保持测试通过
class ToolRegistry:
    """工具注册中心"""

    def __init__(self) -> None:
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """注册工具"""
        if tool.name in self._tools:
            raise ValueError(f"Tool {tool.name} already registered")
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[Tool]:
        """获取工具"""
        return self._tools.get(name)
```

#### 3. 编写代码

```bash
# 实现功能
vim src/your_module.py

# 运行测试（频繁执行）
pytest tests/test_your_feature.py -v

# 检查代码质量
black src/
flake8 src/
mypy src/
```

#### 4. 提交代码

```bash
# 查看修改
git status
git diff

# 暂存文件
git add src/your_module.py tests/test_your_feature.py

# 提交（会触发pre-commit钩子）
git commit -m "feat(module): add new feature"

# 如果pre-commit失败，修复后再次提交
git add .
git commit -m "feat(module): add new feature"
```

#### 5. 推送并创建PR

```bash
# 推送分支
git push origin feature/your-feature-name

# 在GitHub/GitLab上创建Pull Request
# 填写PR模板，等待代码审查
```

### 代码审查流程

#### 作为PR作者

1. **自我审查**: 提交前先自己review一遍
2. **完整描述**: 填写完整的PR描述
3. **关联Issue**: 关联相关的Issue
4. **CI通过**: 确保所有CI检查通过
5. **及时回应**: 及时回应审查意见

#### 作为审查者

1. **及时审查**: 24小时内完成初次审查
2. **建设性反馈**: 提供具体的改进建议
3. **提问而非命令**: "这里是否可以...?" 而非 "你必须..."
4. **认可优点**: 指出好的实现方式

审查checklist：

- [ ] 代码功能正确
- [ ] 测试充分
- [ ] 文档完整
- [ ] 命名清晰
- [ ] 没有安全隐患
- [ ] 性能可接受
- [ ] 遵循项目规范

---

## 测试规范

### 测试层级

#### 1. 单元测试 (Unit Tests)

测试单个函数/类的行为：

```python
# tests/llm/test_prompt.py
import pytest
from rookie_agent.llm.prompt import PromptTemplate

def test_prompt_template_render():
    """测试Prompt模板渲染功能"""
    template = PromptTemplate("Hello, {name}!")

    result = template.render(name="Alice")

    assert result == "Hello, Alice!"

def test_prompt_template_missing_variable_raises_error():
    """测试缺少变量时抛出异常"""
    template = PromptTemplate("Hello, {name}!")

    with pytest.raises(KeyError):
        template.render()
```

#### 2. 集成测试 (Integration Tests)

测试多个组件协同工作：

```python
# tests/integration/test_agent_with_tools.py
import pytest
from rookie_agent.core.agent import Agent
from rookie_agent.llm import OpenAIProvider
from rookie_agent.tools import ToolRegistry, CalculatorTool

@pytest.mark.integration
def test_agent_can_use_calculator():
    """测试Agent能够使用计算器工具"""
    # Setup
    llm = OpenAIProvider(api_key="test-key")
    tools = ToolRegistry()
    tools.register(CalculatorTool())
    agent = Agent(llm=llm, tools=tools)

    # Execute
    result = agent.run("What is 123 * 456?")

    # Verify
    assert "56088" in result
```

#### 3. 端到端测试 (E2E Tests)

测试完整的用户场景：

```python
# tests/e2e/test_rag_pipeline.py
import pytest
from rookie_agent import Agent, RAGPipeline

@pytest.mark.e2e
@pytest.mark.slow
def test_complete_rag_workflow():
    """测试完整的RAG工作流"""
    # 1. 加载文档
    docs = load_documents("tests/fixtures/docs/")

    # 2. 构建RAG
    rag = RAGPipeline()
    rag.index(docs)

    # 3. 创建Agent
    agent = Agent(rag=rag)

    # 4. 查询
    answer = agent.ask("What is the main topic?")

    # 5. 验证
    assert answer is not None
    assert len(answer) > 0
```

### 测试组织

#### 目录结构

```
tests/
├── unit/              # 单元测试
│   ├── llm/
│   ├── tools/
│   ├── memory/
│   └── ...
├── integration/       # 集成测试
├── e2e/              # 端到端测试
├── fixtures/         # 测试数据
│   ├── prompts/
│   ├── docs/
│   └── configs/
└── conftest.py       # Pytest配置和fixtures
```

#### Fixtures

在 `conftest.py` 中定义共享fixtures：

```python
# tests/conftest.py
import pytest
from rookie_agent.llm import OpenAIProvider
from rookie_agent.tools import ToolRegistry

@pytest.fixture
def mock_llm():
    """Mock的LLM提供商"""
    return MockLLMProvider(responses=["test response"])

@pytest.fixture
def tool_registry():
    """工具注册中心fixture"""
    registry = ToolRegistry()
    # 注册一些测试工具
    return registry

@pytest.fixture
def temp_dir(tmp_path):
    """临时目录fixture"""
    return tmp_path
```

### 测试覆盖率

#### 目标

- 整体覆盖率: >80%
- 核心模块: >90%
- 工具函数: >95%

#### 运行覆盖率测试

```bash
# 生成覆盖率报告
pytest tests/ --cov=src --cov-report=html --cov-report=term

# 查看HTML报告
open htmlcov/index.html

# 检查未覆盖的行
pytest tests/ --cov=src --cov-report=term-missing
```

### Mock和Patch

#### 使用unittest.mock

```python
from unittest.mock import Mock, patch, MagicMock

def test_llm_provider_with_mock():
    """使用Mock测试LLM提供商"""
    # 创建Mock对象
    mock_client = Mock()
    mock_client.chat.completions.create.return_value = Mock(
        choices=[Mock(message=Mock(content="mocked response"))]
    )

    # 使用Mock
    provider = OpenAIProvider(client=mock_client)
    result = provider.generate("test")

    # 验证
    assert result == "mocked response"
    mock_client.chat.completions.create.assert_called_once()

@patch('rookie_agent.llm.providers.openai.OpenAI')
def test_provider_with_patch(mock_openai_class):
    """使用patch测试"""
    # 配置patch
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    # 测试
    provider = OpenAIProvider(api_key="test")
    # ...
```

#### 使用pytest-mock

```python
def test_with_pytest_mock(mocker):
    """使用pytest-mock"""
    # Mock对象
    mock_llm = mocker.Mock()
    mock_llm.generate.return_value = "response"

    # Patch
    mocker.patch(
        'rookie_agent.core.agent.get_llm',
        return_value=mock_llm
    )

    # 测试
    agent = Agent()
    result = agent.run("test")
    assert result == "response"
```

### 测试命令

```bash
# 运行所有测试
pytest

# 运行特定文件
pytest tests/unit/llm/test_provider.py

# 运行特定测试
pytest tests/unit/llm/test_provider.py::test_openai_provider

# 运行标记的测试
pytest -m "not slow"  # 跳过慢测试
pytest -m integration  # 只运行集成测试

# 并行运行
pytest -n auto  # 使用所有CPU核心

# 详细输出
pytest -v

# 显示print输出
pytest -s

# 失败时进入调试
pytest --pdb

# 只运行上次失败的测试
pytest --lf
```

---

## 文档规范

### 文档类型

#### 1. 代码文档 (Docstrings)

见 [代码规范](CODE_STYLE.md#文档字符串-docstrings)

#### 2. API文档

自动从docstrings生成：

```bash
# 使用sphinx
cd docs/
make html

# 使用mkdocs
mkdocs serve
```

#### 3. 教程文档

位于 `docs/tutorials/`：

- 快速开始
- 核心概念
- 使用指南
- 进阶主题

#### 4. 设计文档

位于 `docs/architecture/`：

- 架构设计
- 模块设计
- API设计
- 数据模型

### 编写文档

#### Markdown规范

```markdown
# 一级标题 - 文档标题（每个文件只有一个）

## 二级标题 - 主要章节

### 三级标题 - 子章节

#### 四级标题 - 细节

- 使用无序列表
- 列表项简洁明了

1. 有序列表
2. 按步骤说明

**重点内容**使用加粗

`代码片段`使用反引号

\`\`\`python
# 代码块
def hello():
    print("Hello, World!")
\`\`\`

> 引用或注意事项

| 表头1 | 表头2 |
|-------|-------|
| 内容1 | 内容2 |

[链接文本](URL)

![图片alt](图片URL)
```

### 文档更新流程

1. 代码改动时同步更新文档
2. 新功能必须有对应文档
3. 破坏性变更必须在CHANGELOG中说明
4. 定期review文档的准确性

---

## 性能优化指南

### 性能测试

#### 使用pytest-benchmark

```python
def test_performance(benchmark):
    """性能基准测试"""
    result = benchmark(expensive_function, arg1, arg2)
    assert result is not None

# 运行
pytest tests/performance/ --benchmark-only
```

#### 使用cProfile

```python
import cProfile
import pstats

def profile_function():
    profiler = cProfile.Profile()
    profiler.enable()

    # 运行代码
    expensive_function()

    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(20)
```

### 优化技巧

#### 1. 缓存

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def expensive_computation(n: int) -> int:
    """使用LRU缓存优化"""
    return fibonacci(n)
```

#### 2. 异步IO

```python
import asyncio

async def fetch_multiple(urls: List[str]) -> List[str]:
    """并发获取多个URL"""
    tasks = [fetch_url(url) for url in urls]
    return await asyncio.gather(*tasks)
```

#### 3. 批处理

```python
def process_in_batches(items: List[Item], batch_size: int = 100):
    """批量处理以提高效率"""
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        process_batch(batch)
```

#### 4. 懒加载

```python
class Agent:
    def __init__(self):
        self._llm = None

    @property
    def llm(self):
        """懒加载LLM"""
        if self._llm is None:
            self._llm = create_llm()
        return self._llm
```

---

## 安全规范

### 敏感信息处理

#### 1. 不要硬编码密钥

```python
# Bad ❌
API_KEY = "sk-1234567890abcdef"

# Good ✅
import os
API_KEY = os.getenv("OPENAI_API_KEY")
```

#### 2. 使用python-dotenv

```python
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY not set")
```

#### 3. .gitignore配置

```
# .gitignore
.env
.env.local
*.key
secrets/
credentials.json
```

### 输入验证

```python
from pydantic import BaseModel, validator

class UserInput(BaseModel):
    query: str
    max_length: int

    @validator('query')
    def validate_query(cls, v):
        if len(v) > 1000:
            raise ValueError("Query too long")
        if not v.strip():
            raise ValueError("Query cannot be empty")
        return v.strip()

    @validator('max_length')
    def validate_max_length(cls, v):
        if v < 1 or v > 4000:
            raise ValueError("Invalid max_length")
        return v
```

### 依赖安全

```bash
# 检查依赖漏洞
pip install safety
safety check

# 或使用pip-audit
pip install pip-audit
pip-audit
```

---

## 常见问题

### Q: 如何调试测试？

```bash
# 使用pdb
pytest --pdb

# 使用ipdb (更好的调试体验)
pip install ipdb
pytest --pdb --pdbcls=IPython.terminal.debugger:Pdb
```

### Q: 如何跳过某些测试？

```python
import pytest

@pytest.mark.skip(reason="Not implemented yet")
def test_future_feature():
    pass

@pytest.mark.skipif(sys.version_info < (3, 10), reason="Requires Python 3.10+")
def test_new_syntax():
    pass
```

### Q: 如何处理异步测试？

```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result == expected
```

### Q: 如何测试日志输出？

```python
def test_logging(caplog):
    """测试日志输出"""
    with caplog.at_level(logging.INFO):
        function_that_logs()

    assert "Expected log message" in caplog.text
```

### Q: 如何生成测试数据？

```python
# 使用faker
from faker import Faker
fake = Faker()

def test_with_fake_data():
    user_name = fake.name()
    email = fake.email()
    # ...

# 使用hypothesis
from hypothesis import given
import hypothesis.strategies as st

@given(st.integers(), st.integers())
def test_addition_commutative(a, b):
    assert a + b == b + a
```

---

## 开发工具推荐

### IDE配置

#### VS Code

推荐扩展：
- Python
- Pylance
- Black Formatter
- isort
- Test Explorer
- GitLens

#### PyCharm

配置：
- 启用Black作为代码格式化工具
- 配置pytest作为测试运行器
- 启用mypy类型检查

### 命令行工具

```bash
# 代码质量
pip install pylint bandit

# 文档生成
pip install sphinx mkdocs

# 性能分析
pip install py-spy memory_profiler

# 依赖管理
pip install pip-tools poetry
```

---

**最后更新**: 2025-10-25
**维护者**: Rookie Agent Team
