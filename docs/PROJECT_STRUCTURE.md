# 项目结构说明

## 总体目录结构

```
rookie-agent/
├── .github/                    # GitHub配置
│   ├── workflows/             # CI/CD工作流
│   │   ├── test.yml          # 测试工作流
│   │   ├── lint.yml          # 代码检查工作流
│   │   └── docs.yml          # 文档发布工作流
│   ├── ISSUE_TEMPLATE/       # Issue模板
│   └── PULL_REQUEST_TEMPLATE.md  # PR模板
│
├── docs/                       # 文档目录
│   ├── architecture/          # 架构设计文档
│   │   ├── 01-agent-overview.md
│   │   ├── 02-core-modules.md
│   │   ├── 03-llm-abstraction.md
│   │   ├── 04-tool-system.md
│   │   ├── 05-memory-design.md
│   │   ├── 06-rag-pipeline.md
│   │   ├── 07-planner-design.md
│   │   ├── 08-multi-agent.md
│   │   └── diagrams/         # 架构图
│   ├── tutorials/             # 教程文档
│   │   ├── 01-getting-started.md
│   │   ├── 02-llm-adapter.md
│   │   ├── 03-tool-system.md
│   │   ├── 04-memory.md
│   │   ├── 05-rag.md
│   │   ├── 06-planner.md
│   │   ├── 07-multi-agent.md
│   │   └── 08-observability.md
│   ├── api/                   # API文档
│   │   ├── core.md
│   │   ├── llm.md
│   │   ├── tools.md
│   │   ├── memory.md
│   │   └── rag.md
│   ├── course-design.pdf      # 课程设计文档
│   ├── DEVELOPMENT_ROADMAP.md # 开发路线图
│   ├── GIT_CONVENTIONS.md     # Git规范
│   ├── CODE_STYLE.md          # 代码规范
│   ├── DEVELOPMENT_GUIDE.md   # 开发指南
│   └── PROJECT_STRUCTURE.md   # 本文件
│
├── src/                        # 源代码目录
│   └── rookie_agent/          # 主包
│       ├── __init__.py        # 包初始化
│       ├── version.py         # 版本信息
│       │
│       ├── core/              # 核心模块
│       │   ├── __init__.py
│       │   ├── agent.py       # Agent基类
│       │   ├── interfaces.py  # 接口定义
│       │   ├── state.py       # 状态管理
│       │   ├── executor.py    # 执行器
│       │   └── exceptions.py  # 自定义异常
│       │
│       ├── llm/               # LLM模块
│       │   ├── __init__.py
│       │   ├── base.py        # LLM基类
│       │   ├── providers/     # LLM提供商实现
│       │   │   ├── __init__.py
│       │   │   ├── openai.py  # OpenAI实现
│       │   │   ├── azure.py   # Azure实现
│       │   │   ├── ollama.py  # Ollama本地模型
│       │   │   └── mock.py    # Mock实现(用于测试)
│       │   ├── prompt.py      # Prompt模板系统
│       │   ├── parser.py      # 输出解析器
│       │   ├── message.py     # 消息模型
│       │   └── streaming.py   # 流式输出处理
│       │
│       ├── tools/             # 工具系统
│       │   ├── __init__.py
│       │   ├── base.py        # 工具基类
│       │   ├── registry.py    # 工具注册器
│       │   ├── executor.py    # 工具执行器
│       │   ├── decorator.py   # 工具装饰器
│       │   ├── sandbox.py     # 安全沙箱
│       │   ├── builtin/       # 内置工具
│       │   │   ├── __init__.py
│       │   │   ├── calculator.py
│       │   │   ├── web_search.py
│       │   │   ├── file_ops.py
│       │   │   ├── code_executor.py
│       │   │   └── http_client.py
│       │   └── schemas.py     # 工具Schema定义
│       │
│       ├── memory/            # 记忆系统
│       │   ├── __init__.py
│       │   ├── base.py        # 记忆基类
│       │   ├── working.py     # 短期记忆(工作记忆)
│       │   ├── longterm.py    # 长期记忆
│       │   ├── storage/       # 存储后端
│       │   │   ├── __init__.py
│       │   │   ├── vector.py  # 向量存储
│       │   │   ├── sql.py     # SQL存储
│       │   │   └── redis.py   # Redis存储
│       │   ├── compression.py # 上下文压缩
│       │   └── retrieval.py   # 记忆检索
│       │
│       ├── rag/               # RAG系统
│       │   ├── __init__.py
│       │   ├── pipeline.py    # RAG流水线
│       │   ├── loader.py      # 文档加载器
│       │   ├── chunker.py     # 文本切片器
│       │   ├── embedder.py    # 嵌入模型
│       │   ├── retriever.py   # 检索器
│       │   ├── reranker.py    # 重排序器
│       │   ├── query_rewriter.py  # 查询重写
│       │   └── utils.py       # 工具函数
│       │
│       ├── planner/           # 规划器
│       │   ├── __init__.py
│       │   ├── base.py        # 规划器基类
│       │   ├── decomposer.py  # 任务分解器
│       │   ├── cot.py         # 思维链
│       │   ├── react.py       # ReAct模式
│       │   └── reflection.py  # 反思机制
│       │
│       ├── executor/          # 执行器
│       │   ├── __init__.py
│       │   ├── base.py        # 执行器基类
│       │   ├── sequential.py  # 顺序执行
│       │   ├── parallel.py    # 并行执行
│       │   └── retry.py       # 重试机制
│       │
│       ├── multi_agent/       # 多Agent协作
│       │   ├── __init__.py
│       │   ├── bus.py         # 消息总线
│       │   ├── roles.py       # 角色定义
│       │   ├── coordinator.py # 协调器
│       │   ├── workflow.py    # 工作流
│       │   └── patterns/      # 协作模式
│       │       ├── __init__.py
│       │       ├── sequential.py
│       │       ├── parallel.py
│       │       └── hierarchical.py
│       │
│       ├── observability/     # 可观测性
│       │   ├── __init__.py
│       │   ├── logger.py      # 日志系统
│       │   ├── tracer.py      # 追踪器
│       │   ├── metrics.py     # 指标收集
│       │   ├── events.py      # 事件系统
│       │   └── visualizer.py  # 可视化
│       │
│       ├── eval/              # 评测系统
│       │   ├── __init__.py
│       │   ├── harness.py     # 评测框架
│       │   ├── metrics.py     # 评测指标
│       │   ├── benchmarks/    # 基准测试
│       │   │   ├── __init__.py
│       │   │   ├── qa.py
│       │   │   ├── reasoning.py
│       │   │   └── tool_use.py
│       │   └── datasets/      # 测试数据集
│       │
│       ├── api/               # API接口
│       │   ├── __init__.py
│       │   ├── rest.py        # REST API
│       │   ├── websocket.py   # WebSocket
│       │   └── schemas.py     # API Schema
│       │
│       ├── cli/               # 命令行工具
│       │   ├── __init__.py
│       │   ├── main.py        # CLI入口
│       │   ├── commands/      # 命令定义
│       │   │   ├── __init__.py
│       │   │   ├── run.py
│       │   │   ├── eval.py
│       │   │   └── config.py
│       │   └── utils.py
│       │
│       ├── config/            # 配置系统
│       │   ├── __init__.py
│       │   ├── settings.py    # 配置管理
│       │   ├── loader.py      # 配置加载
│       │   └── defaults.py    # 默认配置
│       │
│       └── utils/             # 工具函数
│           ├── __init__.py
│           ├── file.py        # 文件操作
│           ├── text.py        # 文本处理
│           ├── async_utils.py # 异步工具
│           └── validators.py  # 验证器
│
├── tests/                      # 测试代码
│   ├── __init__.py
│   ├── conftest.py            # Pytest配置
│   │
│   ├── unit/                  # 单元测试
│   │   ├── __init__.py
│   │   ├── core/
│   │   │   ├── test_agent.py
│   │   │   └── test_state.py
│   │   ├── llm/
│   │   │   ├── test_base.py
│   │   │   ├── test_openai.py
│   │   │   └── test_prompt.py
│   │   ├── tools/
│   │   │   ├── test_registry.py
│   │   │   └── test_executor.py
│   │   ├── memory/
│   │   ├── rag/
│   │   └── ...
│   │
│   ├── integration/           # 集成测试
│   │   ├── __init__.py
│   │   ├── test_agent_with_tools.py
│   │   ├── test_rag_pipeline.py
│   │   └── test_multi_agent.py
│   │
│   ├── e2e/                   # 端到端测试
│   │   ├── __init__.py
│   │   ├── test_complete_workflow.py
│   │   └── test_api.py
│   │
│   ├── performance/           # 性能测试
│   │   ├── __init__.py
│   │   └── test_benchmarks.py
│   │
│   └── fixtures/              # 测试数据
│       ├── prompts/
│       ├── documents/
│       ├── configs/
│       └── responses/
│
├── examples/                   # 示例代码
│   ├── README.md
│   ├── 01_basic_chat.py       # 基础对话
│   ├── 02_tool_usage.py       # 工具使用
│   ├── 03_rag_qa.py          # RAG问答
│   ├── 04_planning.py        # 任务规划
│   ├── 05_multi_agent.py     # 多Agent协作
│   ├── 06_custom_tool.py     # 自定义工具
│   ├── 07_complete_app.py    # 完整应用
│   └── data/                 # 示例数据
│
├── configs/                    # 配置文件
│   ├── default.yaml          # 默认配置
│   ├── development.yaml      # 开发环境配置
│   ├── production.yaml       # 生产环境配置
│   └── logging.yaml          # 日志配置
│
├── scripts/                    # 工具脚本
│   ├── setup.sh              # 环境设置
│   ├── test.sh               # 测试脚本
│   ├── lint.sh               # 代码检查
│   ├── build.sh              # 构建脚本
│   └── deploy.sh             # 部署脚本
│
├── deployment/                 # 部署配置
│   ├── docker/
│   │   ├── Dockerfile
│   │   └── docker-compose.yml
│   ├── kubernetes/
│   │   ├── deployment.yaml
│   │   └── service.yaml
│   └── terraform/            # 基础设施代码
│
├── notebooks/                  # Jupyter笔记本
│   ├── 01_exploration.ipynb
│   ├── 02_experiments.ipynb
│   └── 03_analysis.ipynb
│
├── .github/                    # GitHub配置
├── .gitignore                 # Git忽略文件
├── .env.example               # 环境变量示例
├── .flake8                    # Flake8配置
├── .pre-commit-config.yaml    # Pre-commit配置
│
├── pyproject.toml             # 项目配置(Poetry/Black/isort等)
├── setup.py                   # 安装配置
├── requirements.txt           # 生产依赖
├── requirements-dev.txt       # 开发依赖
│
├── LICENSE                    # 许可证
├── README.md                  # 项目说明
├── CHANGELOG.md               # 变更日志
├── CONTRIBUTING.md            # 贡献指南
└── CODE_OF_CONDUCT.md         # 行为准则
```

---

## 核心模块说明

### 1. core/ - 核心模块

**职责**: 定义Agent的核心抽象和基础设施

**关键文件**:
- `agent.py`: Agent基类，定义Agent的基本行为和生命周期
- `interfaces.py`: 所有核心接口定义（如Runnable, Invokable等）
- `state.py`: Agent状态管理，包括状态存储和状态转换
- `executor.py`: 通用执行器，管理Agent的执行流程
- `exceptions.py`: 自定义异常类

**设计原则**:
- 高度抽象，面向接口编程
- 最小化依赖，只依赖Python标准库
- 清晰的生命周期管理

### 2. llm/ - LLM模块

**职责**: 提供统一的LLM访问接口

**关键文件**:
- `base.py`: LLM基类，定义统一接口
- `providers/`: 各厂商的具体实现
  - `openai.py`: OpenAI API
  - `azure.py`: Azure OpenAI
  - `ollama.py`: 本地模型
- `prompt.py`: Prompt模板引擎，支持变量替换和条件渲染
- `parser.py`: 输出解析器，支持JSON、XML等格式
- `streaming.py`: 流式输出处理

**设计模式**:
- 策略模式：不同的LLM提供商
- 模板方法：统一的调用流程
- 适配器模式：统一不同API的差异

### 3. tools/ - 工具系统

**职责**: 管理Agent可用的工具和函数调用

**关键文件**:
- `base.py`: 工具基类，定义工具接口
- `registry.py`: 工具注册中心，管理所有可用工具
- `executor.py`: 工具执行器，负责安全执行工具
- `decorator.py`: `@tool` 装饰器，简化工具定义
- `sandbox.py`: 安全沙箱，限制工具的执行权限
- `builtin/`: 内置工具集合

**设计模式**:
- 注册表模式：工具注册
- 命令模式：工具执行
- 装饰器模式：工具定义

### 4. memory/ - 记忆系统

**职责**: 管理Agent的短期和长期记忆

**关键文件**:
- `working.py`: 短期记忆，管理对话上下文
- `longterm.py`: 长期记忆，基于向量数据库
- `storage/`: 不同的存储后端实现
- `compression.py`: 上下文压缩算法
- `retrieval.py`: 记忆检索策略

**关键技术**:
- Token管理和压缩
- 向量相似度检索
- LRU缓存策略
- 记忆重要性评分

### 5. rag/ - RAG系统

**职责**: 实现检索增强生成

**关键文件**:
- `pipeline.py`: RAG主流水线
- `loader.py`: 多格式文档加载
- `chunker.py`: 智能文本切片
- `embedder.py`: Embedding生成
- `retriever.py`: 检索策略（向量+关键词）
- `reranker.py`: 重排序算法
- `query_rewriter.py`: 查询优化

**关键技术**:
- 混合检索（Dense + Sparse）
- 动态chunk策略
- 多路召回
- 上下文窗口优化

### 6. planner/ - 规划器

**职责**: 任务分解和执行规划

**关键文件**:
- `decomposer.py`: 任务分解器
- `cot.py`: Chain of Thought实现
- `react.py`: ReAct模式实现
- `reflection.py`: 自我反思机制

**设计理念**:
- 分层规划
- 动态调整
- 反思优化

### 7. multi_agent/ - 多Agent协作

**职责**: 实现多个Agent之间的协作

**关键文件**:
- `bus.py`: 消息总线，发布/订阅模式
- `roles.py`: Agent角色定义
- `coordinator.py`: 协调器，仲裁决策
- `workflow.py`: 工作流引擎
- `patterns/`: 不同的协作模式

**协作模式**:
- 顺序执行
- 并行执行
- 层级结构
- 竞争模式

### 8. observability/ - 可观测性

**职责**: 监控、追踪、日志和指标

**关键文件**:
- `logger.py`: 结构化日志系统
- `tracer.py`: 分布式追踪
- `metrics.py`: 指标收集（延迟、成本等）
- `events.py`: 事件系统
- `visualizer.py`: 执行轨迹可视化

**关键功能**:
- 完整的调用链追踪
- Token消耗统计
- 性能分析
- 异常监控

---

## 配置文件说明

### pyproject.toml

包含项目元数据和工具配置：

```toml
[tool.poetry]
name = "rookie-agent"
version = "0.1.0"
description = "A pedagogical AI Agent framework"

[tool.black]
line-length = 100

[tool.isort]
profile = "black"

[tool.mypy]
python_version = "3.10"
```

### requirements.txt

生产环境依赖：
```
openai>=1.0.0
pydantic>=2.0.0
langchain-core>=0.1.0
chromadb>=0.4.0
fastapi>=0.100.0
```

### requirements-dev.txt

开发环境额外依赖：
```
pytest>=7.0.0
pytest-cov>=4.0.0
black>=23.0.0
flake8>=6.0.0
mypy>=1.0.0
```

---

## 测试结构说明

### 测试组织原则

1. **镜像源码结构**: tests目录结构镜像src目录
2. **分层测试**: unit、integration、e2e分离
3. **Fixture复用**: 在conftest.py中定义共享fixtures
4. **测试命名**: `test_<模块>_<功能>_<场景>`

### 测试覆盖目标

- 核心模块: >90%
- 工具函数: >95%
- 整体项目: >80%

---

## 文档组织

### 文档类型

1. **设计文档** (`docs/architecture/`): 架构设计和技术决策
2. **教程文档** (`docs/tutorials/`): 分步教学内容
3. **API文档** (`docs/api/`): API参考
4. **开发文档** (`docs/`): 开发规范和指南

### 文档维护

- 代码变更时同步更新文档
- 每个PR必须包含相关文档更新
- 定期review文档准确性

---

## 版本管理

### 分支策略

- `main`: 稳定版本
- `develop`: 开发版本
- `feature/*`: 功能分支
- `release/*`: 发布分支
- `hotfix/*`: 热修复分支

### 版本号规则

遵循语义化版本 (Semantic Versioning):
- MAJOR.MINOR.PATCH
- 例如: 1.2.3

---

**最后更新**: 2025-10-25
**维护者**: Rookie Agent Team
