"""Integration tests for Qwen Provider.

这些测试会实际调用Qwen API，需要配置有效的API key。

使用方法：
1. 复制.env.example为.env
2. 在.env中填入你的DASHSCOPE_API_KEY
3. 运行测试：pytest tests/integration/llm/test_qwen_integration.py -v

注意：这些测试会消耗实际的API配额
"""

import os
import pytest
from dotenv import load_dotenv

from rookie_agent.llm.providers.qwen import QwenProvider
from rookie_agent.llm.types import Message, MessageRole
from rookie_agent.llm.exceptions import AuthenticationError


# 加载环境变量
load_dotenv()


def has_qwen_api_key() -> bool:
    """检查是否配置了Qwen API key."""
    return bool(os.getenv("DASHSCOPE_API_KEY"))


# 如果没有API key，跳过所有测试
pytestmark = pytest.mark.skipif(
    not has_qwen_api_key(),
    reason="需要配置DASHSCOPE_API_KEY环境变量才能运行Qwen集成测试"
)


class TestQwenIntegration:
    """Qwen Provider集成测试."""

    def test_simple_chat(self):
        """测试基础对话功能."""
        provider = QwenProvider()

        messages = [
            Message(role=MessageRole.USER, content="你好，请用一句话介绍你自己")
        ]

        response = provider.chat(messages)

        # 验证响应格式
        assert response is not None
        assert len(response.choices) > 0
        assert response.choices[0].message.content
        assert response.choices[0].message.role == MessageRole.ASSISTANT

        # 验证token使用情况
        assert response.usage.prompt_tokens > 0
        assert response.usage.completion_tokens > 0
        assert response.usage.total_tokens > 0

        print(f"\n=== Qwen Chat Response ===")
        print(f"Model: {response.model}")
        print(f"Content: {response.choices[0].message.content}")
        print(f"Tokens: {response.usage.total_tokens}")
        print(f"Finish Reason: {response.choices[0].finish_reason}")

    def test_chat_with_system_message(self):
        """测试带系统提示的对话."""
        provider = QwenProvider()

        messages = [
            Message(
                role=MessageRole.SYSTEM,
                content="你是一个专业的Python编程助手，只回答Python相关问题。"
            ),
            Message(
                role=MessageRole.USER,
                content="什么是列表推导式？"
            )
        ]

        response = provider.chat(messages)

        assert response.choices[0].message.content
        # 检查响应中是否包含Python相关内容
        content = response.choices[0].message.content.lower()
        assert any(keyword in content for keyword in ["python", "列表", "推导", "list"])

        print(f"\n=== Qwen System Message Response ===")
        print(f"Content: {response.choices[0].message.content}")

    def test_chat_with_temperature(self):
        """测试温度参数控制."""
        provider = QwenProvider(temperature=0.1)

        messages = [
            Message(role=MessageRole.USER, content="1+1等于几？")
        ]

        # 低温度应该产生稳定、确定的回答
        response1 = provider.chat(messages)
        response2 = provider.chat(messages)

        # 两次回答应该相似（因为温度很低）
        assert response1.choices[0].message.content
        assert response2.choices[0].message.content
        # 都应该包含"2"
        assert "2" in response1.choices[0].message.content
        assert "2" in response2.choices[0].message.content

        print(f"\n=== Qwen Temperature Test ===")
        print(f"Response 1: {response1.choices[0].message.content}")
        print(f"Response 2: {response2.choices[0].message.content}")

    def test_chat_with_max_tokens(self):
        """测试最大token限制."""
        provider = QwenProvider()

        messages = [
            Message(
                role=MessageRole.USER,
                content="请详细解释Python的装饰器机制"
            )
        ]

        # 限制回复长度
        response = provider.chat(messages, max_tokens=50)

        assert response.choices[0].message.content
        # 应该因为达到token限制而停止（某些服务可能不返回usage或返回null）
        if response.usage and response.usage.completion_tokens is not None:
            assert response.usage.completion_tokens <= 60  # 允许一些误差

        print(f"\n=== Qwen Max Tokens Test ===")
        print(f"Completion Tokens: {getattr(response.usage, 'completion_tokens', None)}")
        print(f"Content: {response.choices[0].message.content}")

    def test_streaming_chat(self):
        """测试流式对话."""
        provider = QwenProvider()

        messages = [
            Message(
                role=MessageRole.USER,
                content="请数从1到5，每个数字单独一行"
            )
        ]

        # 收集流式响应
        chunks = []
        full_content = ""

        for chunk in provider.stream(messages):
            chunks.append(chunk)
            content = chunk.get_content()
            if content:
                full_content += content
                print(content, end='', flush=True)

        print()  # 换行

        # 验证
        assert len(chunks) > 0
        assert full_content
        # 应该包含数字
        assert any(str(i) in full_content for i in range(1, 6))

        print(f"\n=== Qwen Streaming Test ===")
        print(f"Total Chunks: {len(chunks)}")
        print(f"Full Content: {full_content}")

    def test_streaming_incremental(self):
        """测试流式响应的增量特性."""
        provider = QwenProvider()

        messages = [
            Message(role=MessageRole.USER, content="说'你好世界'")
        ]

        chunks_with_content = []
        for chunk in provider.stream(messages):
            content = chunk.get_content()
            if content:
                chunks_with_content.append(content)

        # 应该有多个增量块
        assert len(chunks_with_content) > 0

        # 拼接应该得到完整响应
        full_response = ''.join(chunks_with_content)
        assert full_response

        print(f"\n=== Qwen Streaming Incremental ===")
        print(f"Chunks: {chunks_with_content}")
        print(f"Full: {full_response}")

    def test_multi_turn_conversation(self):
        """测试多轮对话."""
        provider = QwenProvider()

        # 第一轮
        messages = [
            Message(role=MessageRole.USER, content="我叫小明")
        ]
        response1 = provider.chat(messages)

        # 第二轮：继续对话
        messages.append(Message(
            role=MessageRole.ASSISTANT,
            content=response1.choices[0].message.content
        ))
        messages.append(Message(
            role=MessageRole.USER,
            content="我叫什么名字？"
        ))

        response2 = provider.chat(messages)

        # 应该记住上下文
        assert response2.choices[0].message.content
        content = response2.choices[0].message.content
        assert "小明" in content or "你" in content

        print(f"\n=== Qwen Multi-turn Conversation ===")
        print(f"Turn 1: {response1.choices[0].message.content}")
        print(f"Turn 2: {response2.choices[0].message.content}")

    def test_enable_search(self):
        """测试联网搜索功能."""
        provider = QwenProvider()

        messages = [
            Message(
                role=MessageRole.USER,
                content="今天是几号？现在几点？"
            )
        ]

        # 启用搜索
        response = provider.chat(messages, enable_search=True)

        assert response.choices[0].message.content
        # 应该包含实时信息（具体内容取决于实际时间）

        print(f"\n=== Qwen Search Enabled ===")
        print(f"Content: {response.choices[0].message.content}")

    def test_model_selection(self):
        """测试不同模型的选择."""
        # 测试qwen-turbo（快速模型）
        provider_turbo = QwenProvider(model="qwen-turbo")

        messages = [
            Message(role=MessageRole.USER, content="你好")
        ]

        response = provider_turbo.chat(messages)

        assert response.model == "qwen-turbo"
        assert response.choices[0].message.content

        print(f"\n=== Qwen Model Selection ===")
        print(f"Model: {response.model}")
        print(f"Content: {response.choices[0].message.content}")

    def test_context_manager(self):
        """测试上下文管理器用法."""
        with QwenProvider() as provider:
            messages = [
                Message(role=MessageRole.USER, content="你好")
            ]

            response = provider.chat(messages)

            assert response.choices[0].message.content

        # 客户端应该已关闭
        assert provider._client._client.is_closed

    def test_invalid_api_key(self):
        """测试无效API key的错误处理."""
        provider = QwenProvider(api_key="invalid-key-12345")

        messages = [
            Message(role=MessageRole.USER, content="测试")
        ]

        # 应该抛出认证错误
        with pytest.raises(Exception):  # 可能是AuthenticationError或其他HTTP错误
            provider.chat(messages)

    @pytest.mark.skipif(
        not os.getenv("QWEN_ENABLE_EXPENSIVE_TESTS"),
        reason="昂贵的测试，需要设置QWEN_ENABLE_EXPENSIVE_TESTS=1才运行"
    )
    def test_long_context(self):
        """测试长上下文处理（可选测试，因为会消耗较多token）."""
        provider = QwenProvider(model="qwen-max-longcontext")

        # 创建一个较长的上下文
        long_text = "这是测试文本。" * 100

        messages = [
            Message(
                role=MessageRole.USER,
                content=f"请总结以下文本：\n\n{long_text}"
            )
        ]

        response = provider.chat(messages)

        assert response.choices[0].message.content
        # 应该能够处理并总结

        print(f"\n=== Qwen Long Context ===")
        print(f"Input Tokens: {response.usage.prompt_tokens}")
        print(f"Output Tokens: {response.usage.completion_tokens}")


if __name__ == "__main__":
    # 允许直接运行此文件进行测试
    pytest.main([__file__, "-v", "-s"])
