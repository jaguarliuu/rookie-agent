"""LLM Provider implementations.

This package contains concrete implementations of LLM providers
for various services (Qwen, DeepSeek, OpenAI, Ollama, Claude).

Available Providers:
- QwenProvider: 阿里云通义千问（DashScope API）
- DeepSeekProvider: DeepSeek AI
- OpenAIProvider: OpenAI (TODO)
- OllamaProvider: Ollama本地部署 (TODO)
- ClaudeProvider: Anthropic Claude (TODO)
"""

from rookie_agent.llm.providers.qwen import QwenProvider
from rookie_agent.llm.providers.deepseek import DeepSeekProvider

__all__ = [
    "QwenProvider",
    "DeepSeekProvider",
]
