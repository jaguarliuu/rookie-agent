# Rookie Agent

<div align="center">

**从零自研的教学型 AI Agent 框架**

[![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

[快速开始](#快速开始) • [文档](#文档) • [示例](#示例) • [贡献](#贡献)

</div>

---

## 项目简介

Rookie Agent 是一个**从零自研**的教学型 AI Agent 框架，旨在帮助开发者深入理解 AI Agent 的核心原理和架构设计。

与 LangChain、CrewAI 等现成框架不同，本项目通过**手写每一行核心代码**的方式，带你彻底掌握：

- 🧠 **Agent 架构设计**: 深入理解思考、记忆、行动、感知四大核心模块
- 🔧 **工具调用系统**: 掌握 Function Calling 的底层机制
- 💾 **记忆管理**: 实现短期记忆和长期记忆的完整方案
- 📚 **RAG 系统**: 从文档加载到检索优化的全流程实现
- 🤝 **多 Agent 协作**: 构建消息总线和协调机制
- 📊 **可观测性**: 建立完整的监控和评测体系

### 为什么选择 Rookie Agent？

| 特性 | Rookie Agent | 其他框架 |
|------|--------------|----------|
| **学习目的** | ✅ 教学导向，每行代码都可以理解 | ❌ 生产导向，复杂度高 |
| **可定制性** | ✅ 完全可控，随意修改 | ⚠️ 受限于框架设计 |
| **原理理解** | ✅ 从第一性原理出发 | ❌ 黑盒使用 |
| **代码质量** | ✅ 清晰注释，教学示例丰富 | ⚠️ 工程化为主 |

---

## 核心特性

### 🎯 模块化设计

```
┌─────────────────────────────────────────────┐
│              Rookie Agent                    │
├─────────────────────────────────────────────┤
│  LLM Adapter  │  Tool System  │  Memory     │
├─────────────────────────────────────────────┤
│  RAG Pipeline │  Planner      │  Executor   │
├─────────────────────────────────────────────┤
│  Multi-Agent  │  Observability│  API/CLI    │
└─────────────────────────────────────────────┘
```

### 📦 主要模块

- **LLM Adapter**: 统一的 LLM 接口，支持 OpenAI、Azure、本地模型
- **Tool System**: 强大的工具注册和调用系统，支持自定义工具
- **Memory**: 短期记忆（对话上下文）+ 长期记忆（向量数据库）
- **RAG**: 完整的检索增强生成流水线
- **Planner**: 任务分解、规划和执行
- **Multi-Agent**: 多 Agent 协作和通信机制
- **Observability**: 日志追踪、指标收集、性能评测

---

## 快速开始

### 安装

```bash
# 克隆项目
git clone https://github.com/your-org/rookie-agent.git
cd rookie-agent

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或 .venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 配置

创建 `.env` 文件：

```bash
OPENAI_API_KEY=your-api-key-here
LOG_LEVEL=INFO
```

### Hello World

```python
from rookie_agent import Agent
from rookie_agent.llm import OpenAIProvider

# 创建LLM提供商
llm = OpenAIProvider()

# 创建Agent
agent = Agent(llm=llm)

# 运行
response = agent.run("你好，请介绍一下自己")
print(response)
```

### 使用工具

```python
from rookie_agent import Agent
from rookie_agent.llm import OpenAIProvider
from rookie_agent.tools import ToolRegistry, CalculatorTool, WebSearchTool

# 创建工具注册表
tools = ToolRegistry()
tools.register(CalculatorTool())
tools.register(WebSearchTool())

# 创建带工具的Agent
agent = Agent(llm=OpenAIProvider(), tools=tools)

# Agent可以自动选择和使用工具
response = agent.run("北京今天的天气怎么样？顺便帮我计算一下25*4")
print(response)
```

### RAG 应用

```python
from rookie_agent import Agent
from rookie_agent.rag import RAGPipeline

# 加载文档
docs = ["doc1.txt", "doc2.pdf", "doc3.md"]

# 创建RAG管道
rag = RAGPipeline()
rag.index(docs)

# 创建RAG Agent
agent = Agent(rag=rag)

# 基于文档问答
answer = agent.ask("文档中提到的核心概念是什么？")
print(answer)
```

---

## 项目结构

```
rookie-agent/
├── src/                    # 源代码
│   ├── core/              # 核心模块
│   │   ├── agent.py       # Agent基类
│   │   ├── interfaces.py  # 接口定义
│   │   └── state.py       # 状态管理
│   ├── llm/               # LLM模块
│   │   ├── base.py        # LLM基类
│   │   ├── providers/     # 各厂商实现
│   │   ├── prompt.py      # Prompt模板
│   │   └── parser.py      # 输出解析
│   ├── tools/             # 工具系统
│   │   ├── base.py        # 工具基类
│   │   ├── registry.py    # 工具注册
│   │   ├── executor.py    # 工具执行
│   │   └── builtin/       # 内置工具
│   ├── memory/            # 记忆系统
│   │   ├── working.py     # 短期记忆
│   │   └── longterm.py    # 长期记忆
│   ├── rag/               # RAG系统
│   │   ├── loader.py      # 文档加载
│   │   ├── chunker.py     # 文本切片
│   │   ├── retriever.py   # 检索器
│   │   └── reranker.py    # 重排序
│   ├── planner/           # 规划器
│   ├── executor/          # 执行器
│   ├── multi_agent/       # 多Agent
│   ├── observability/     # 可观测性
│   └── api/               # API接口
├── tests/                 # 测试代码
│   ├── unit/             # 单元测试
│   ├── integration/      # 集成测试
│   └── e2e/              # 端到端测试
├── docs/                  # 文档
│   ├── architecture/     # 架构设计
│   ├── tutorials/        # 教程
│   └── api/              # API文档
├── examples/              # 示例代码
├── configs/               # 配置文件
├── scripts/               # 工具脚本
└── README.md
```

详细的项目结构说明见 [项目结构文档](docs/PROJECT_STRUCTURE.md)

---

## 文档

### 快速入门

- [安装指南](docs/installation.md)
- [5分钟快速开始](docs/quickstart.md)
- [核心概念](docs/concepts.md)

### 教程

- [第一章：AI Agent 架构认知](docs/tutorials/01-architecture.md)
- [第二章：LLM 接入与抽象](docs/tutorials/02-llm-adapter.md)
- [第三章：工具调用系统](docs/tutorials/03-tool-system.md)
- [第四章：记忆系统](docs/tutorials/04-memory.md)
- [第五章：RAG 系统](docs/tutorials/05-rag.md)
- [第六章：规划与执行](docs/tutorials/06-planner.md)
- [第七章：多 Agent 协作](docs/tutorials/07-multi-agent.md)
- [第八章：可观测性](docs/tutorials/08-observability.md)

### 开发指南

- [开发环境设置](docs/DEVELOPMENT_GUIDE.md#开发环境设置)
- [代码规范](docs/CODE_STYLE.md)
- [Git 提交规范](docs/GIT_CONVENTIONS.md)
- [测试指南](docs/DEVELOPMENT_GUIDE.md#测试规范)

### API 文档

- [API 参考](https://rookie-agent.readthedocs.io/)
- [核心 API](docs/api/core.md)
- [LLM API](docs/api/llm.md)
- [工具 API](docs/api/tools.md)

---

## 示例

查看 `examples/` 目录获取更多示例：

- [基础对话](examples/01_basic_chat.py)
- [工具使用](examples/02_tool_usage.py)
- [RAG问答](examples/03_rag_qa.py)
- [任务规划](examples/04_planning.py)
- [多Agent协作](examples/05_multi_agent.py)
- [自定义工具](examples/06_custom_tool.py)
- [完整应用](examples/07_complete_app.py)

---

## 开发路线图

查看 [开发路线图](docs/DEVELOPMENT_ROADMAP.md) 了解详细的开发计划。

### 当前进度

- [x] Phase 0: 项目初始化
- [ ] Phase 1: AI Agent 架构认知
- [ ] Phase 2: LLM 接入与抽象层
- [ ] Phase 3: 工具调用系统
- [ ] Phase 4: 记忆系统
- [ ] Phase 5: RAG 系统
- [ ] Phase 6: 规划与执行
- [ ] Phase 7: 多 Agent 协作
- [ ] Phase 8: 可观测性
- [ ] Phase 9: 工程化与部署
- [ ] Phase 10: 总结与优化

### 里程碑

- [ ] M1: MVP (基础Agent + LLM + Tool)
- [ ] M2: 记忆增强 (Memory + RAG)
- [ ] M3: 智能规划 (Planner + Multi-Agent)
- [ ] M4: 生产就绪 (工程化)
- [ ] M5: 1.0 正式发布

---

## 贡献

我们欢迎所有形式的贡献！

### 如何贡献

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'feat: add some feature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 贡献指南

- [贡献指南](CONTRIBUTING.md)
- [行为准则](CODE_OF_CONDUCT.md)
- [开发指南](docs/DEVELOPMENT_GUIDE.md)

### 贡献者

感谢所有贡献者！

<a href="https://github.com/your-org/rookie-agent/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=your-org/rookie-agent" />
</a>

---

## 常见问题

### Q: Rookie Agent 和 LangChain 有什么区别？

A: Rookie Agent 是教学导向的框架，代码简洁清晰，适合学习 Agent 原理。LangChain 是生产级框架，功能全面但复杂度高。如果你想深入理解 Agent 的工作原理，选择 Rookie Agent；如果你要快速搭建生产应用，可以选择 LangChain。

### Q: 可以用于生产环境吗？

A: 本项目主要用于教学和学习，不建议直接用于生产环境。但你可以基于本项目的理念和设计，开发自己的生产级框架。

### Q: 支持哪些 LLM？

A: 目前支持：
- OpenAI (GPT-3.5, GPT-4)
- Azure OpenAI
- 本地模型 (通过 Ollama)

计划支持：
- Anthropic Claude
- Google Gemini
- 更多开源模型

### Q: 如何添加自定义工具？

A: 很简单！继承 `Tool` 基类并实现 `execute` 方法即可。详见[自定义工具教程](docs/tutorials/custom-tools.md)。

---

## 许可证

本项目采用 [MIT](LICENSE) 许可证。

---

## 致谢

本项目受到以下开源项目的启发：

- [LangChain](https://github.com/langchain-ai/langchain)
- [LangGraph](https://github.com/langchain-ai/langgraph)
- [CrewAI](https://github.com/joaomdmoura/crewAI)
- [AutoGen](https://github.com/microsoft/autogen)

感谢所有开源贡献者的辛勤付出！

---

## 联系我们

- **Issues**: [GitHub Issues](https://github.com/your-org/rookie-agent/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/rookie-agent/discussions)
- **Email**: rookie-agent@example.com

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给我们一个 Star！⭐**

Made with ❤️ by Rookie Agent Team

</div>
