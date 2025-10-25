# Rookie Agent 开发路线图

## 项目概述

Rookie Agent 是一个从零自研的教学型 AI Agent 框架，旨在帮助开发者深入理解 AI Agent 的核心原理和架构设计。

## 开发阶段规划

### Phase 0: 项目初始化 (Week 1)
**目标**: 完成项目基础设施搭建

- [x] 项目结构设计
- [ ] 开发环境配置
- [ ] 依赖管理（requirements.txt / pyproject.toml）
- [ ] 代码规范工具配置（black, flake8, mypy）
- [ ] Git工作流配置
- [ ] CI/CD基础配置
- [ ] 文档框架搭建

**交付物**:
- 可运行的项目骨架
- 完整的开发规范文档
- 基础的测试框架

---

### Phase 1: AI Agent 架构认知 (Week 2)
**对应课程**: 第一章

**目标**: 建立Agent系统的整体架构认知

**任务清单**:
- [ ] 研究主流框架（LangChain, LangGraph, CrewAI, AutoGen）
- [ ] 绘制框架核心架构图
- [ ] 定义核心模块接口
- [ ] 编写架构设计文档
- [ ] 设计Agent执行循环（Event Loop）

**交付物**:
- `docs/architecture/01-agent-overview.md`: Agent架构总览
- `docs/architecture/02-core-modules.md`: 核心模块设计
- `src/core/agent.py`: Agent基类定义
- `src/core/interfaces.py`: 核心接口定义

**技术要点**:
- Agent的四大支柱：思考、记忆、行动、感知
- 状态管理机制
- 模块间通信协议

---

### Phase 2: LLM 接入与抽象层 (Week 3-4)
**对应课程**: 第二章

**目标**: 实现统一的LLM抽象接口

**任务清单**:
- [ ] 设计LLM Provider抽象接口
- [ ] 实现OpenAI适配器
- [ ] 实现本地模型适配器（Ollama）
- [ ] Prompt模板系统
- [ ] 消息格式统一抽象
- [ ] 流式输出支持
- [ ] 结构化输出解析（JSON Schema, Pydantic）
- [ ] 错误恢复机制
- [ ] Token计数与限制

**交付物**:
- `src/llm/base.py`: LLM基类
- `src/llm/providers/`: 各厂商适配器
- `src/llm/prompt.py`: Prompt模板引擎
- `src/llm/parser.py`: 输出解析器
- `tests/llm/`: 完整单元测试

**技术要点**:
- 适配器模式
- 流式响应处理
- 异常重试策略
- Token预算管理

---

### Phase 3: 工具调用系统 (Week 5-6)
**对应课程**: 第三章

**目标**: 实现Agent的"行动"能力

**任务清单**:
- [ ] Function Calling协议实现
- [ ] 工具注册与发现机制
- [ ] 参数验证系统（JSON Schema / Pydantic）
- [ ] 工具执行引擎
- [ ] 工具调用反馈循环
- [ ] 安全沙箱机制
- [ ] 白名单与权限控制
- [ ] 调用日志与追踪
- [ ] 错误处理与重试

**交付物**:
- `src/tools/base.py`: 工具基类
- `src/tools/registry.py`: 工具注册器
- `src/tools/executor.py`: 工具执行器
- `src/tools/builtin/`: 内置工具集
- `src/tools/sandbox.py`: 安全沙箱

**技术要点**:
- 装饰器模式注册工具
- OpenAPI规范映射
- 异步执行支持
- 超时与资源限制

---

### Phase 4: 记忆系统 (Week 7-8)
**对应课程**: 第四章

**目标**: 实现短期与长期记忆

**任务清单**:
- [ ] 短期记忆（Working Memory）
  - [ ] 对话上下文管理
  - [ ] Token预算控制
  - [ ] 上下文压缩策略
- [ ] 长期记忆（Long-term Memory）
  - [ ] 向量数据库集成（Chroma/FAISS）
  - [ ] 记忆索引与检索
  - [ ] 记忆摘要生成
- [ ] 记忆写回机制
- [ ] 记忆遗忘与清理策略
- [ ] 记忆重要性评分

**交付物**:
- `src/memory/base.py`: 记忆基类
- `src/memory/working.py`: 短期记忆
- `src/memory/longterm.py`: 长期记忆
- `src/memory/storage/`: 存储后端

**技术要点**:
- 滑动窗口算法
- 向量相似度检索
- LRU缓存策略
- 记忆重要性算法

---

### Phase 5: RAG 检索增强系统 (Week 9-10)
**对应课程**: 第五章

**目标**: 实现知识库问答能力

**任务清单**:
- [ ] 文档加载与解析
- [ ] 文本切片策略
- [ ] Embedding生成与缓存
- [ ] 向量数据库索引
- [ ] 检索算法实现
- [ ] Query重写
- [ ] Rerank重排序
- [ ] 上下文优化
- [ ] 来源引用与可解释性
- [ ] 幻觉检测机制

**交付物**:
- `src/rag/loader.py`: 文档加载器
- `src/rag/chunker.py`: 文本切片器
- `src/rag/retriever.py`: 检索器
- `src/rag/reranker.py`: 重排序器
- `src/rag/pipeline.py`: RAG流水线

**技术要点**:
- 混合检索（向量+关键词）
- 动态chunk大小
- 多路召回策略
- 答案可信度评估

---

### Phase 6: 计划与执行模块 (Week 11-12)
**对应课程**: 第六章

**目标**: 实现任务规划与执行能力

**任务清单**:
- [ ] 思维链（CoT）实现
- [ ] 任务分解算法
- [ ] Planner模块设计
- [ ] Executor执行引擎
- [ ] 执行状态管理
- [ ] 反思机制（Self-Reflection）
- [ ] 错误恢复与回滚
- [ ] 计划调整策略

**交付物**:
- `src/planner/base.py`: 规划器基类
- `src/planner/decomposer.py`: 任务分解器
- `src/executor/base.py`: 执行器基类
- `src/executor/reflection.py`: 反思模块

**技术要点**:
- ReAct模式
- 分层任务分解
- 执行轨迹记录
- 自我批评机制

---

### Phase 7: 多Agent协作 (Week 13-14)
**对应课程**: 第七章

**目标**: 实现多Agent协同工作

**任务清单**:
- [ ] 消息总线设计
- [ ] 发布/订阅机制
- [ ] 黑板架构实现
- [ ] Agent角色定义
- [ ] 任务分工策略
- [ ] 仲裁机制
- [ ] 团队工作流
- [ ] 协作模式（顺序/并行/竞争）

**交付物**:
- `src/multi_agent/bus.py`: 消息总线
- `src/multi_agent/roles.py`: 角色定义
- `src/multi_agent/coordinator.py`: 协调器
- `src/multi_agent/workflow.py`: 工作流引擎

**技术要点**:
- 异步消息传递
- 共享状态管理
- 冲突解决策略
- 任务依赖图

---

### Phase 8: 可观测性与评测 (Week 15-16)
**对应课程**: 第八章

**目标**: 建立完整的监控与评测体系

**任务清单**:
- [ ] 结构化日志系统
- [ ] 事件追踪机制
- [ ] 指标收集（成功率、延迟、成本）
- [ ] Token消耗统计
- [ ] 执行轨迹可视化
- [ ] 评测集构建
- [ ] 自动化评测框架
- [ ] 性能基准测试

**交付物**:
- `src/observability/logger.py`: 日志系统
- `src/observability/tracer.py`: 追踪器
- `src/observability/metrics.py`: 指标收集
- `src/eval/harness.py`: 评测框架
- `src/eval/benchmarks/`: 基准测试集

**技术要点**:
- 分布式追踪
- 指标聚合
- 可视化方案
- A/B测试框架

---

### Phase 9: 工程化与部署 (Week 17-18)
**对应课程**: 第九章

**目标**: 让框架具备生产级能力

**任务清单**:
- [ ] 配置管理系统
- [ ] 插件化架构
- [ ] RESTful API
- [ ] WebSocket支持
- [ ] CLI工具
- [ ] SDK封装
- [ ] 持久化方案（Redis/SQLite）
- [ ] 调用缓存
- [ ] 安全加固
- [ ] 成本控制
- [ ] Docker化
- [ ] 部署文档

**交付物**:
- `src/api/rest.py`: REST API
- `src/api/websocket.py`: WebSocket服务
- `src/cli/`: CLI工具
- `src/config/`: 配置系统
- `deployment/`: 部署配置

**技术要点**:
- FastAPI框架
- 异步编程
- 容器化部署
- 限流与熔断

---

### Phase 10: 总结与优化 (Week 19-20)
**对应课程**: 第十章

**目标**: 完善文档，优化性能

**任务清单**:
- [ ] 完整API文档
- [ ] 使用教程编写
- [ ] 最佳实践总结
- [ ] 性能优化
- [ ] 代码重构
- [ ] 与主流框架对比分析
- [ ] 未来扩展方向规划
- [ ] 示例应用开发

**交付物**:
- 完整的技术文档
- 多个示例应用
- 性能测试报告
- 框架对比分析报告

---

## 开发原则

### 1. 测试驱动开发（TDD）
- 每个模块必须有对应的单元测试
- 测试覆盖率目标：>80%
- 关键路径必须有集成测试

### 2. 文档优先
- 每个模块开发前先编写设计文档
- 代码注释要清晰完整
- 保持README和API文档同步更新

### 3. 增量开发
- 每个Phase独立可运行
- 小步快跑，频繁集成
- 每周至少一次可演示的进展

### 4. 代码质量
- 严格遵守Python代码规范（PEP8）
- 使用类型注解（Type Hints）
- 定期进行代码审查

### 5. 教学导向
- 代码要清晰易懂，优先可读性
- 每个关键设计点要有注释说明
- 提供丰富的示例代码

---

## 里程碑

| 里程碑 | 时间节点 | 交付内容 |
|--------|----------|----------|
| M1: MVP | Week 6 | 基础Agent + LLM + Tool系统 |
| M2: 记忆增强 | Week 10 | 完整的记忆和RAG系统 |
| M3: 智能规划 | Week 14 | 规划执行和多Agent协作 |
| M4: 生产就绪 | Week 18 | 完整的工程化方案 |
| M5: 正式发布 | Week 20 | 1.0版本发布 |

---

## 风险与应对

### 技术风险
- **风险**: LLM API限流或费用超支
  - **应对**: 实现请求缓存，使用本地模型fallback

- **风险**: 性能瓶颈
  - **应对**: 早期进行性能测试，及时优化关键路径

### 进度风险
- **风险**: 功能范围蔓延
  - **应对**: 严格控制每个Phase的范围，延后非核心功能

- **风险**: 技术难点攻克时间过长
  - **应对**: 预留缓冲时间，及时调整优先级

---

## 成功指标

### 功能指标
- ✅ 支持至少3种LLM提供商
- ✅ 内置至少20个常用工具
- ✅ 支持多Agent协作（至少3种模式）
- ✅ 完整的RAG实现
- ✅ 可观测性覆盖所有核心模块

### 质量指标
- ✅ 单元测试覆盖率 >80%
- ✅ 核心API响应时间 <2s
- ✅ 成功率 >95%
- ✅ 文档完整度 100%

### 教学指标
- ✅ 每个模块都有详细的设计文档
- ✅ 提供至少5个完整示例应用
- ✅ 代码注释覆盖率 >60%

---

## 参考资源

### 开源框架
- [LangChain](https://github.com/langchain-ai/langchain)
- [LangGraph](https://github.com/langchain-ai/langgraph)
- [CrewAI](https://github.com/joaomdmoura/crewAI)
- [AutoGen](https://github.com/microsoft/autogen)

### 学习资料
- [Prompt Engineering Guide](https://www.promptingguide.ai/)
- [LLM Agent Papers](https://github.com/Paitesanshi/LLM-Agent-Survey)
- [Building LLM Applications](https://www.deeplearning.ai/)

---

**最后更新**: 2025-10-25
**维护者**: Rookie Agent Team
