# 03-SSE机制深度解析：从原理到接入

SSE（Server-Sent Events）是一种服务端主动向客户端推送文本事件的机制，适合日志、进度、LLM流式输出等实时场景。本文结合本仓库 `src/rookie_agent/http/streaming.py` 的实现，带你从原理到实践，深入浅出掌握 SSE 的解析与接入方式。

---

## 核心概念

- SSE通过长连接（HTTP）持续向客户端发送文本事件，每个事件由若干“字段行”组成，字段名与值用冒号分隔。
- 事件以“空行”结尾。典型字段：`data`（主要载荷）、`event`（事件类型）、`id`（事件ID）、`retry`（建议重连间隔）。
- 客户端逐行读取并解析为事件对象，按需消费。

示例事件：
```
id: 42
event: message
data: hello

```

OpenAI风格的 SSE 流：
```
data: {"choices": [{"delta": {"content": "你"}}]}

data: {"choices": [{"delta": {"content": "好"}}]}

data: [DONE]

```

---

## 代码结构速览（streaming.py）

- `SSEEvent`：表示一个事件，属性包含 `data/event/id/retry`，`is_done` 便捷判断是否为结束标记（如 `[DONE]`）。
- `SSEParser`：逐行解析器，处理字段聚合、空行触发输出、注释行（以 `:` 开头）忽略、`retry` 数值转换等。
- `SSEStream`：同步流包装器，消费 `response.iter_lines()`，产出解析后的 `SSEEvent`；遇到 `is_done` 时停止并关闭响应。
- `AsyncSSEStream`：异步流包装器，消费 `response.aiter_lines()`，其余逻辑与同步版本一致。

关键兼容性处理：
- 规范一致性：仅移除字段冒号后的“最多一个空格”（`data:  leading` → `" leading"`）。
- 容忍字节行：支持 `bytes` 行自动按 UTF-8 解码，错误忽略（保证不同服务端实现均可解析）。

---

## 解析流程与规范细节

- 行分类：
  - 空行 → 结束当前事件并输出。
  - 注释行（以 `:` 开头）→ 忽略。
  - 字段行（形如 `name: value`）→ 解析并附加到事件。
- 字段处理：
  - 仅移除冒号后的一个空格，其余空格保留（遵循规范）。
  - `retry` 字段尝试转为整数，失败则忽略该字段。
  - `data` 可多行，拼接时保留顺序与换行。
- 结束信号：
  - 常见用法是事件 `data` 为 `[DONE]` 表示流结束；`SSEStream/AsyncSSEStream` 在遇到此事件后停止迭代并关闭响应。
- 尾部flush：
  - 输入末尾即使没有空行，也会flush残留事件，避免数据丢失。

---

## 同步接入示例（requests）

```python
import requests
from src.rookie_agent.http.streaming import SSEStream

url = "https://example.com/sse"
with requests.get(url, stream=True) as resp:
    for event in SSEStream(resp):
        if event.is_done:
            break
        # 处理事件载荷（JSON字符串等）
        print(event.data)
```

要点：
- 使用 `stream=True` 保持连接，逐行消费 `iter_lines()`。
- `SSEStream` 会在迭代结束时调用 `response.close()`，无需手动释放。

---

## 异步接入示例（httpx）

```python
import httpx
from src.rookie_agent.http.streaming import AsyncSSEStream

async def consume_sse():
    async with httpx.AsyncClient() as client:
        async with client.stream("GET", "https://example.com/sse") as resp:
            async for event in AsyncSSEStream(resp):
                if event.is_done:
                    break
                print(event.data)
```

要点：
- 使用 `client.stream(...)` 获取响应并消费 `aiter_lines()`。
- `AsyncSSEStream` 在结束时调用 `response.aclose()`，资源自动释放。

---

## 健壮性与错误处理

- 字节与编码：自动以 UTF-8 解码字节行并忽略错误，保障解析不中断。
- 非法行：没有冒号的行被忽略；日志记录便于定位问题。
- 结束策略：收到 `[DONE]` 即停止，避免多余的拉取与解析。
- 与重试结合：
  - SSE属于长连接流式场景，连接建立失败或中途断开适合使用 `retry_on_exception/async_retry_on_exception` 在“建立或重连阶段”进行重试。
  - 重试不要包裹整个事件迭代过程，以免造成复杂状态恢复；推荐在连接初始化、或断开后重新连接的边界使用重试。

---

## 最佳实践

- 明确结束条件：服务端定义统一的结束事件（如 `[DONE]`）。
- 事件格式规范：遵守“仅移除一个空格”的细节，避免客户端解析差异。
- 负载格式约定：`data` 统一采用 JSON 字符串，客户端按需反序列化。
- 监控与日志：记录非法行、解析失败、重连次数，有助定位问题。
- 资源管理：使用 `with/async with`，让包装器负责关闭响应，避免泄漏。

---

## 常见问题（FAQ）

- 为什么只移除一个空格？
  - 遵循SSE规范，冒号后的一个空格是分隔符；多余空格被视为值的一部分。
- 流中出现 `bytes` 行怎么办？
  - 已支持自动UTF-8解码并忽略错误；若服务端非UTF-8，建议统一编码或在客户端自定义解码策略。
- 如何与重试配合？
  - 在连接建立或重连阶段使用重试；事件消费过程不建议整体重试。

---

## 小结

本实现提供了同步与异步两种SSE流包装器，并严格遵循规范（冒号后仅移除一个空格、注释与空行处理、结束信号、尾部flush），同时提升兼容性（字节行解码容忍）。结合重试机制与完善的资源管理，你可以在日志、进度、LLM流式输出等场景中稳定地使用 SSE。