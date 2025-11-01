# LLM Provider 集成测试

本目录包含Rookie Agent LLM Provider的集成测试。这些测试会实际调用LLM API，因此需要配置有效的API密钥。

## 前置准备

### 1. 安装依赖

确保安装了所有必需的依赖：

```bash
pip install -e ".[dev]"
```

如果需要单独安装python-dotenv：

```bash
pip install python-dotenv
```

### 2. 配置API密钥

#### 方法1：使用.env文件（推荐）

1. 复制环境变量模板：

```bash
cp .env.example .env
```

2. 编辑`.env`文件，填入你的API密钥：

```bash
# Qwen (通义千问)
DASHSCOPE_API_KEY=sk-your-qwen-api-key-here

# DeepSeek
DEEPSEEK_API_KEY=sk-your-deepseek-api-key-here
```

**注意：`.env`文件已被gitignore，不会被提交到Git仓库**

#### 方法2：直接设置环境变量

在运行测试前设置环境变量：

**Linux/macOS:**
```bash
export DASHSCOPE_API_KEY=sk-your-qwen-api-key-here
export DEEPSEEK_API_KEY=sk-your-deepseek-api-key-here
```

**Windows (PowerShell):**
```powershell
$env:DASHSCOPE_API_KEY="sk-your-qwen-api-key-here"
$env:DEEPSEEK_API_KEY="sk-your-deepseek-api-key-here"
```

**Windows (CMD):**
```cmd
set DASHSCOPE_API_KEY=sk-your-qwen-api-key-here
set DEEPSEEK_API_KEY=sk-your-deepseek-api-key-here
```

### 3. 获取API密钥

#### Qwen (通义千问)

1. 访问 [DashScope控制台](https://dashscope.console.aliyun.com/apiKey)
2. 登录或注册阿里云账号
3. 创建API Key
4. 复制密钥到`.env`文件

#### DeepSeek

1. 访问 [DeepSeek Platform](https://platform.deepseek.com/api_keys)
2. 注册账号
3. 创建API Key
4. 复制密钥到`.env`文件

## 运行测试

### 运行所有集成测试

```bash
pytest tests/integration/llm -v -s
```

### 运行特定Provider的测试

**Qwen测试：**
```bash
pytest tests/integration/llm/test_qwen_integration.py -v -s
```

**DeepSeek测试：**
```bash
pytest tests/integration/llm/test_deepseek_integration.py -v -s
```

### 运行特定测试用例

```bash
# 测试Qwen基础对话
pytest tests/integration/llm/test_qwen_integration.py::TestQwenIntegration::test_simple_chat -v -s

# 测试DeepSeek流式响应
pytest tests/integration/llm/test_deepseek_integration.py::TestDeepSeekIntegration::test_streaming_chat -v -s
```

### 跳过没有API key的测试

如果没有配置某个Provider的API key，对应的测试会被自动跳过：

```
tests/integration/llm/test_qwen_integration.py SKIPPED (需要配置DASHSCOPE_API_KEY...)
```

### 运行昂贵的测试

某些测试会消耗较多token，默认被跳过。如需运行，设置相应的环境变量：

```bash
# 运行Qwen的长上下文测试
export QWEN_ENABLE_EXPENSIVE_TESTS=1
pytest tests/integration/llm/test_qwen_integration.py::TestQwenIntegration::test_long_context -v -s

# 运行DeepSeek的复杂代码任务测试
export DEEPSEEK_ENABLE_EXPENSIVE_TESTS=1
pytest tests/integration/llm/test_deepseek_integration.py::TestDeepSeekIntegration::test_complex_code_task -v -s
```

## 测试覆盖范围

### Qwen Provider测试

- ✅ 基础对话功能
- ✅ 系统消息支持
- ✅ 温度参数控制
- ✅ Max tokens限制
- ✅ 流式响应
- ✅ 增量流式内容
- ✅ 多轮对话
- ✅ 联网搜索功能
- ✅ 模型选择
- ✅ 上下文管理器
- ✅ 无效API key错误处理
- ⚠️ 长上下文处理（可选测试）

### DeepSeek Provider测试

- ✅ 基础对话功能
- ✅ 系统消息支持
- ✅ 温度参数控制
- ✅ 代码生成能力
- ✅ 流式响应
- ✅ 流式代码生成
- ✅ 多轮对话
- ✅ 频率/存在惩罚参数
- ✅ 模型选择
- ✅ 代码推理能力
- ✅ 上下文管理器
- ✅ 无效API key错误处理
- ✅ Max tokens限制
- ⚠️ 复杂代码任务（可选测试）

## 注意事项

### API配额消耗

⚠️ **这些测试会实际调用LLM API，消耗你的API配额！**

- 每个测试用例都会产生API调用
- 建议在测试前检查账户余额
- 可以使用`-k`参数只运行特定测试来节省配额

### 速率限制

如果遇到速率限制错误（429），可以：

1. 等待一段时间后重试
2. 减少并发测试数量
3. 升级API账户的速率限制

### 网络问题

如果测试失败且显示连接错误：

1. 检查网络连接
2. 检查是否需要代理
3. 检查API服务状态

## 故障排除

### 测试被跳过

**问题：** 所有测试都显示SKIPPED

**解决：**
- 确认`.env`文件存在且包含正确的API key
- 确认环境变量已正确设置
- 运行 `python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('DASHSCOPE_API_KEY'))"` 检查

### 认证失败

**问题：** 测试失败，显示401 Unauthorized

**解决：**
- 检查API key是否正确
- 检查API key是否已过期
- 尝试重新生成API key

### 导入错误

**问题：** ModuleNotFoundError: No module named 'dotenv'

**解决：**
```bash
pip install python-dotenv
```

### 连接超时

**问题：** 测试超时失败

**解决：**
- 检查网络连接
- 增加超时时间：在Provider初始化时传入 `timeout=120`
- 检查防火墙设置

## 开发建议

### 添加新测试

1. 在相应的测试文件中添加测试方法
2. 使用描述性的方法名（`test_功能描述`）
3. 添加详细的文档字符串
4. 使用`print`语句输出重要信息（配合`-s`参数）

### 最佳实践

```python
def test_new_feature(self):
    """测试新功能的描述."""
    provider = QwenProvider()  # 或 DeepSeekProvider()

    messages = [
        Message(role=MessageRole.USER, content="测试内容")
    ]

    response = provider.chat(messages)

    # 验证响应
    assert response.choices[0].message.content

    # 打印调试信息
    print(f"\n=== Test Output ===")
    print(f"Response: {response.choices[0].message.content}")
```

## 相关文档

- [LLM基础架构深度解析](../../../docs/tutorials/03-LLM基础架构深度解析.md)
- [LLM Provider设计文档](../../../docs/architecture/02-llm-provider-design.md)
- [Qwen文档](https://help.aliyun.com/zh/dashscope/)
- [DeepSeek文档](https://platform.deepseek.com/docs)
