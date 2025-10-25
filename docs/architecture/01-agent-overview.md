# AI Agent 架构总览

## 文档信息

- **版本**: v0.1.0
- **作者**: Rookie Agent Team
- **日期**: 2025-10-25
- **状态**: Draft

---

## 1. 架构概述

### 1.1 设计哲学

Rookie Agent 遵循以下设计原则：

1. **模块化**: 每个模块职责单一，边界清晰
2. **可扩展**: 通过接口抽象，支持多种实现
3. **可观测**: 完整的日志、追踪和指标
4. **教学导向**: 代码清晰易懂，注重原理说明

### 1.2 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        User Interface                        │
│                    (CLI / API / SDK)                         │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│                      Agent Core                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Agent Execution Loop                     │  │
│  │  (Perceive → Think → Plan → Act → Observe)          │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────┬───────────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
┌────────▼────────┐  ┌───────▼────────┐  ┌───────▼────────┐
│   LLM Adapter   │  │  Tool System   │  │ Memory System  │
│                 │  │                │  │                │
│ - OpenAI       │  │ - Registry     │  │ - Working      │
│ - Azure        │  │ - Executor     │  │ - Long-term    │
│ - Local Model  │  │ - Sandbox      │  │ - RAG          │
└────────┬────────┘  └───────┬────────┘  └───────┬────────┘
         │                   │                    │
         └───────────────────┼────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│                  Infrastructure Layer                        │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │   HTTP   │  │  Logger  │  │  Tracer  │  │ Metrics  │  │
│  │  Client  │  │          │  │          │  │          │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. 核心模块

### 2.1 基础设施层 (Infrastructure)

**职责**: 提供底层通用能力

**组件**:
- **HTTP Client**: 统一的HTTP请求客户端
  - 支持同步/异步
  - SSE流式处理
  - 自动重试
  - 错误处理

- **Logger**: 结构化日志
  - 分级日志
  - 上下文信息
  - 日志格式化

- **Tracer**: 分布式追踪
  - 调用链追踪
  - 性能分析

- **Metrics**: 指标收集
  - 请求统计
  - 性能指标
  - 成本追踪

### 2.2 Agent核心层 (Agent Core)

**职责**: Agent的核心执行逻辑

**组件**:
- **Agent基类**: 定义Agent的基本行为
- **执行循环**: Perceive → Think → Plan → Act → Observe
- **状态管理**: Agent运行时状态
- **上下文管理**: 执行上下文传递

**设计模式**:
- 模板方法模式: 定义执行流程框架
- 策略模式: 不同的执行策略

### 2.3 LLM适配层 (LLM Adapter)

**职责**: 统一的LLM访问接口

**组件**:
- **LLM基类**: 定义统一接口
- **Provider实现**:
  - OpenAI Provider
  - Azure Provider
  - Ollama Provider (本地)
- **Prompt管理**: Prompt模板和组装
- **输出解析**: 结构化输出解析

**设计模式**:
- 适配器模式: 统一不同LLM API
- 工厂模式: 创建不同Provider

### 2.4 工具系统 (Tool System)

**职责**: 管理和执行工具

**组件**:
- **Tool基类**: 工具接口定义
- **Tool Registry**: 工具注册和发现
- **Tool Executor**: 工具执行引擎
- **Sandbox**: 安全执行环境

**设计模式**:
- 注册表模式: 工具管理
- 命令模式: 工具执行
- 装饰器模式: 工具定义

### 2.5 记忆系统 (Memory System)

**职责**: 管理Agent的记忆

**组件**:
- **Working Memory**: 短期工作记忆
  - 对话历史
  - 上下文窗口管理

- **Long-term Memory**: 长期记忆
  - 向量存储
  - 记忆检索

- **RAG Pipeline**: 检索增强
  - 文档加载
  - 向量化
  - 检索和重排序

**设计模式**:
- 策略模式: 不同的存储策略
- 代理模式: 延迟加载

### 2.6 规划执行层 (Planning & Execution)

**职责**: 任务分解和执行

**组件**:
- **Planner**: 任务规划器
  - 任务分解
  - 执行计划生成

- **Executor**: 执行器
  - 顺序执行
  - 并行执行

- **Reflection**: 反思机制
  - 执行评估
  - 计划调整

---

## 3. 核心接口定义

### 3.1 Runnable 接口

所有可执行组件的基础接口：

```python
from typing import TypeVar, Generic
from abc import ABC, abstractmethod

Input = TypeVar('Input')
Output = TypeVar('Output')

class Runnable(ABC, Generic[Input, Output]):
    """所有可执行组件的基础接口"""

    @abstractmethod
    def invoke(self, input: Input) -> Output:
        """同步执行"""
        pass

    @abstractmethod
    async def ainvoke(self, input: Input) -> Output:
        """异步执行"""
        pass
```

### 3.2 Streamable 接口

支持流式输出的接口：

```python
from typing import Iterator, AsyncIterator

class Streamable(Runnable[Input, Output]):
    """支持流式输出的接口"""

    @abstractmethod
    def stream(self, input: Input) -> Iterator[Output]:
        """同步流式执行"""
        pass

    @abstractmethod
    async def astream(self, input: Input) -> AsyncIterator[Output]:
        """异步流式执行"""
        pass
```

### 3.3 Configurable 接口

支持配置的接口：

```python
class Configurable(ABC):
    """支持配置的接口"""

    @abstractmethod
    def with_config(self, config: dict) -> 'Configurable':
        """应用配置"""
        pass
```

---

## 4. 数据流转

### 4.1 基本请求流程

```
User Input
    ↓
[Agent.invoke()]
    ↓
[Perceive] → 理解用户意图
    ↓
[Think] → 调用LLM思考
    ↓
    ├─→ [需要工具] → Tool System → 执行工具
    │       ↓
    │   [Observe] → 观察工具结果
    │       ↓
    │   [Think Again] → 继续思考
    │
    └─→ [无需工具] → 直接生成回复
    ↓
[返回结果]
```

### 4.2 流式输出流程

```
User Input
    ↓
[Agent.stream()]
    ↓
[LLM.stream()] → SSE连接
    ↓
[Chunk 1] → yield
[Chunk 2] → yield
[Chunk 3] → yield
    ...
[Chunk N] → yield
    ↓
[Complete]
```

---

## 5. HTTP客户端设计

### 5.1 为什么需要自己实现

1. **教学目的**: 理解HTTP通信原理
2. **灵活控制**: 完全掌控重试、超时等逻辑
3. **统一抽象**: 为所有LLM Provider提供统一基础

### 5.2 HTTP客户端架构

```
┌─────────────────────────────────────────┐
│         HTTP Client Interface            │
└──────────────┬──────────────────────────┘
               │
    ┌──────────┴──────────┐
    │                     │
┌───▼────────┐    ┌──────▼──────┐
│   Sync     │    │    Async    │
│  Client    │    │   Client    │
└───┬────────┘    └──────┬──────┘
    │                    │
    └──────────┬─────────┘
               │
    ┌──────────▼──────────┐
    │   Core Features     │
    │                     │
    │ - Request/Response  │
    │ - SSE Streaming     │
    │ - Retry Logic       │
    │ - Error Handling    │
    │ - Timeout Control   │
    │ - Logging/Tracing   │
    └─────────────────────┘
```

### 5.3 核心功能

**基础功能**:
- GET/POST/PUT/DELETE
- 请求头管理
- 请求体序列化
- 响应解析

**SSE流式处理**:
- SSE协议解析
- 流式数据yield
- 连接保持
- 异常恢复

**健壮性**:
- 自动重试（指数退避）
- 超时控制
- 错误分类
- 连接池管理

**可观测性**:
- 请求日志
- 性能追踪
- 错误监控

---

## 6. 设计原则

### 6.1 接口隔离原则 (ISP)

每个接口应该尽可能小和专注：

- `Runnable`: 只定义可执行
- `Streamable`: 只定义流式
- `Configurable`: 只定义配置

### 6.2 依赖倒置原则 (DIP)

高层模块不依赖低层模块，都依赖抽象：

- Agent依赖LLM接口，不依赖具体Provider
- Tool System依赖Tool接口，不依赖具体工具

### 6.3 开闭原则 (OCP)

对扩展开放，对修改封闭：

- 新增LLM Provider不需要修改Agent代码
- 新增Tool不需要修改Tool System代码

### 6.4 单一职责原则 (SRP)

每个类只有一个改变的理由：

- HTTP Client只负责HTTP通信
- Retry只负责重试逻辑
- Logger只负责日志记录

---

## 7. 技术选型

### 7.1 核心依赖

| 用途 | 库 | 原因 |
|------|-----|------|
| HTTP客户端 | httpx | 同时支持同步/异步，API统一 |
| 数据验证 | pydantic | 强大的类型验证和序列化 |
| 环境变量 | python-dotenv | 标准的.env文件支持 |
| Token计数 | tiktoken | OpenAI官方库 |

### 7.2 可选依赖

| 用途 | 库 | 原因 |
|------|-----|------|
| 向量数据库 | chromadb | 简单易用，适合学习 |
| 向量模型 | sentence-transformers | 本地embedding |
| API框架 | fastapi | 现代、快速、异步支持 |

---

## 8. 下一步计划

### Week 1 (当前)
- [x] 架构设计文档
- [ ] 核心接口定义
- [ ] HTTP客户端实现
- [ ] 基础重试机制
- [ ] 单元测试

### Week 2
- [ ] SSE流式处理
- [ ] 异步HTTP客户端
- [ ] 高级重试策略
- [ ] 日志和追踪
- [ ] 集成测试

---

## 9. 参考资料

### 设计模式
- [Design Patterns: Elements of Reusable Object-Oriented Software](https://en.wikipedia.org/wiki/Design_Patterns)
- [Python Design Patterns](https://refactoring.guru/design-patterns/python)

### Agent架构
- [LangChain Architecture](https://python.langchain.com/docs/expression_language/)
- [LangGraph Conceptual Guide](https://langchain-ai.github.io/langgraph/)
- [AutoGen Design](https://microsoft.github.io/autogen/)

### HTTP协议
- [HTTP/1.1 Specification](https://tools.ietf.org/html/rfc2616)
- [Server-Sent Events](https://html.spec.whatwg.org/multipage/server-sent-events.html)
- [httpx Documentation](https://www.python-httpx.org/)

---

**最后更新**: 2025-10-25
**文档状态**: Draft → Review → Approved
