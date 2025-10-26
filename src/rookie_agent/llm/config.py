"""Configuration management for LLM providers.

This module implements the flexible configuration system described in
the architecture document, supporting multiple configuration sources
with clear priority:

Priority (high to low):
1. Code parameters (runtime arguments)
2. Environment variables
3. Configuration file (future)
4. Default values

Security:
- API keys are read from environment by default
- Sensitive values are masked in logs
- Config validation happens at initialization
"""

import os
import logging
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict

from rookie_agent.llm.exceptions import ConfigurationError

logger = logging.getLogger(__name__)


class ProviderConfig(BaseModel):
    """Base configuration for all LLM providers.

    This base class defines common configuration parameters shared
    across all providers. Provider-specific configs inherit from this.

    Attributes:
        api_key: API authentication key
        api_base: Base URL for API endpoints
        model: Model name to use
        temperature: Sampling temperature (0-2)
        max_tokens: Maximum tokens in completion
        top_p: Nucleus sampling parameter
        timeout: Request timeout in seconds
        max_retries: Maximum retry attempts
        stream: Enable streaming responses
        extra_headers: Additional HTTP headers
        extra_body: Additional request parameters

    Configuration Priority:
        1. Constructor parameters (highest)
        2. Environment variables
        3. Default values (lowest)

    Examples:
        From environment variables:
        >>> # Set OPENAI_API_KEY in environment
        >>> config = OpenAIConfig()  # Reads from env

        Explicit parameters:
        >>> config = OpenAIConfig(
        ...     api_key="sk-xxx",
        ...     model="gpt-4-turbo",
        ...     temperature=0.9
        ... )

        Runtime override:
        >>> config = OpenAIConfig(model="gpt-4")
        >>> # Later, override for specific call
        >>> provider.chat(messages, model="gpt-3.5-turbo")
    """

    # API Authentication
    api_key: Optional[str] = Field(
        None,
        description="API key for authentication"
    )
    api_base: Optional[str] = Field(
        None,
        description="Base URL for API endpoints"
    )

    # Model Parameters
    model: str = Field(
        ...,
        description="Model name to use for completion"
    )
    temperature: float = Field(
        0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature (0=deterministic, 2=very creative)"
    )
    max_tokens: Optional[int] = Field(
        None,
        gt=0,
        description="Maximum tokens in completion (None=model default)"
    )
    top_p: float = Field(
        1.0,
        ge=0.0,
        le=1.0,
        description="Nucleus sampling: cumulative probability cutoff"
    )

    # Request Configuration
    timeout: float = Field(
        60.0,
        gt=0,
        description="Request timeout in seconds"
    )
    max_retries: int = Field(
        3,
        ge=0,
        le=10,
        description="Maximum number of retry attempts"
    )
    stream: bool = Field(
        False,
        description="Enable streaming responses"
    )

    # Advanced Options
    extra_headers: Optional[Dict[str, str]] = Field(
        None,
        description="Additional HTTP headers"
    )
    extra_body: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional request body parameters"
    )

    model_config = ConfigDict(
        validate_assignment=True,
        arbitrary_types_allowed=False,
        extra="forbid",
    )

    def __repr__(self) -> str:
        """String representation with masked API key.

        Security: API key is masked in logs and repr.
        """
        return self._repr_with_masked_key()

    def _repr_with_masked_key(self) -> str:
        """Generate repr with masked sensitive data."""
        fields = []
        for field_name, field_value in self.model_dump().items():
            if "key" in field_name.lower() or "secret" in field_name.lower():
                # Mask sensitive fields
                if field_value:
                    masked = f"{field_value[:7]}..." if len(field_value) > 7 else "***"
                    fields.append(f"{field_name}='{masked}'")
                else:
                    fields.append(f"{field_name}=None")
            else:
                fields.append(f"{field_name}={field_value!r}")

        return f"{self.__class__.__name__}({', '.join(fields)})"

    @model_validator(mode="after")
    def validate_config(cls, model):
        """Final validation of configuration.

        Raises:
            ConfigurationError: If configuration is invalid
        """
        api_key = getattr(model, "api_key", None)
        if (api_key is None or (isinstance(api_key, str) and api_key.strip() == "")) and not model.__class__._allow_none_api_key():
            raise ConfigurationError(
                f"API key is required for {model.__class__.__name__}. "
                f"Set it via environment variable or pass as parameter."
            )

        return model

    @classmethod
    def _allow_none_api_key(cls) -> bool:
        """Whether to allow None API key.

        Override in subclasses for providers that don't need API keys
        (e.g., Ollama local deployment).

        Returns:
            True if None API key is allowed, False otherwise
        """
        return False


class OpenAIConfig(ProviderConfig):
    """Configuration for OpenAI provider.

    Environment Variables:
        OPENAI_API_KEY: API key (required)
        OPENAI_API_BASE: Base URL (optional, default: official API)
        OPENAI_MODEL: Default model (optional)
        OPENAI_ORGANIZATION: Organization ID (optional)

    Examples:
        >>> # From environment
        >>> config = OpenAIConfig()

        >>> # Explicit config
        >>> config = OpenAIConfig(
        ...     api_key="sk-xxx",
        ...     model="gpt-4-turbo-preview",
        ...     temperature=0.8
        ... )
    """

    model: str = "gpt-4"
    api_base: Optional[str] = "https://api.openai.com/v1"

    # OpenAI-specific parameters
    frequency_penalty: float = Field(
        0.0,
        ge=-2.0,
        le=2.0,
        description="Frequency penalty (-2.0 to 2.0)"
    )
    presence_penalty: float = Field(
        0.0,
        ge=-2.0,
        le=2.0,
        description="Presence penalty (-2.0 to 2.0)"
    )
    seed: Optional[int] = Field(
        None,
        description="Seed for deterministic sampling"
    )
    response_format: Optional[Dict[str, str]] = Field(
        None,
        description="Response format (e.g., {\"type\": \"json_object\"})"
    )
    organization: Optional[str] = Field(
        None,
        description="OpenAI organization ID"
    )

    @field_validator("api_key", mode="before")
    def load_api_key(cls, v):
        """Load API key from environment if not provided."""
        if v not in (None, ""):
            return v
        return os.getenv("OPENAI_API_KEY")

    @field_validator("api_base", mode="before")
    def load_api_base(cls, v):
        """Load API base from environment if not provided."""
        if v not in (None, ""):
            return v
        return os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")

    @field_validator("organization", mode="before")
    def load_organization(cls, v):
        """Load organization from environment if not provided."""
        if v not in (None, ""):
            return v
        return os.getenv("OPENAI_ORGANIZATION")


class QwenConfig(ProviderConfig):
    """Configuration for Qwen (通义千问) provider.

    Qwen uses DashScope API with OpenAI-compatible endpoints.

    Environment Variables:
        DASHSCOPE_API_KEY: API key (required)
        QWEN_MODEL: Default model (optional)
        QWEN_API_BASE: Base URL (optional)

    Examples:
        >>> config = QwenConfig()  # From environment
        >>> config = QwenConfig(
        ...     api_key="sk-xxx",
        ...     model="qwen-max",
        ...     enable_search=True
        ... )
    """

    model: str = "qwen-max"
    api_base: Optional[str] = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    # Qwen-specific parameters
    enable_search: bool = Field(
        False,
        description="Enable internet search capability"
    )
    repetition_penalty: Optional[float] = Field(
        None,
        ge=0.0,
        description="Repetition penalty"
    )

    @model_validator(mode="before")
    def populate_from_env(cls, data):
        """Populate missing fields from environment before validation."""
        if isinstance(data, dict):
            if data.get("api_key") is None:
                data["api_key"] = os.getenv("DASHSCOPE_API_KEY") or os.getenv("QWEN_API_KEY")
            if data.get("api_base") is None:
                data["api_base"] = os.getenv("QWEN_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        return data

    @field_validator("api_key", mode="before")
    def load_api_key(cls, v):
        """Load API key from environment if not provided."""
        if v is None:
            return os.getenv("DASHSCOPE_API_KEY") or os.getenv("QWEN_API_KEY")
        return v

    @field_validator("api_base", mode="before")
    def load_api_base(cls, v):
        """Load API base from environment if not provided."""
        if v not in (None, ""):
            return v
        return os.getenv("QWEN_API_BASE",
                        "https://dashscope.aliyuncs.com/compatible-mode/v1")


class DeepSeekConfig(ProviderConfig):
    """Configuration for DeepSeek provider.

    DeepSeek provides OpenAI-compatible API.

    Environment Variables:
        DEEPSEEK_API_KEY: API key (required)
        DEEPSEEK_MODEL: Default model (optional)
        DEEPSEEK_API_BASE: Base URL (optional)

    Examples:
        >>> config = DeepSeekConfig()
        >>> config = DeepSeekConfig(
        ...     api_key="sk-xxx",
        ...     model="deepseek-chat"
        ... )
    """

    model: str = "deepseek-chat"
    api_base: Optional[str] = "https://api.deepseek.com/v1"

    # DeepSeek-specific parameters
    frequency_penalty: float = Field(
        0.0,
        ge=-2.0,
        le=2.0,
        description="Frequency penalty"
    )
    presence_penalty: float = Field(
        0.0,
        ge=-2.0,
        le=2.0,
        description="Presence penalty"
    )

    @model_validator(mode="before")
    def populate_from_env(cls, data):
        """Populate missing fields from environment before validation."""
        if isinstance(data, dict):
            if data.get("api_key") is None:
                data["api_key"] = os.getenv("DEEPSEEK_API_KEY")
            if data.get("api_base") is None:
                data["api_base"] = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1")
        return data

    @field_validator("api_key", mode="before")
    def load_api_key(cls, v):
        """Load API key from environment if not provided."""
        if v is None:
            return os.getenv("DEEPSEEK_API_KEY")
        return v

    @field_validator("api_base", mode="before")
    def load_api_base(cls, v):
        """Load API base from environment if not provided."""
        if v not in (None, ""):
            return v
        return os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1")


class OllamaConfig(ProviderConfig):
    """Configuration for Ollama local deployment.

    Ollama provides OpenAI-compatible API for local models.
    No API key required for local deployment.

    Environment Variables:
        OLLAMA_BASE_URL: Base URL (default: http://localhost:11434)
        OLLAMA_MODEL: Default model (optional)

    Examples:
        >>> config = OllamaConfig(model="llama2")
        >>> config = OllamaConfig(
        ...     model="mistral",
        ...     api_base="http://custom-host:11434"
        ... )
    """

    model: str = "llama2"
    api_base: Optional[str] = "http://localhost:11434/v1"

    # Ollama-specific parameters
    num_predict: Optional[int] = Field(
        None,
        description="Maximum number of tokens to predict"
    )
    num_ctx: Optional[int] = Field(
        None,
        description="Context window size"
    )

    @field_validator("api_base", mode="before")
    def load_api_base(cls, v):
        """Load API base from environment if not provided."""
        if v not in (None, ""):
            return v
        base = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        # Ensure /v1 suffix for OpenAI compatibility
        if not base.endswith("/v1"):
            base = f"{base}/v1"
        return base

    @classmethod
    def _allow_none_api_key(cls) -> bool:
        """Ollama doesn't require API key for local deployment."""
        return True


class ClaudeConfig(ProviderConfig):
    """Configuration for Anthropic Claude provider.

    Claude has a different API format from OpenAI, requiring
    special adaptation in the provider layer.

    Environment Variables:
        ANTHROPIC_API_KEY: API key (required)
        CLAUDE_MODEL: Default model (optional)
        ANTHROPIC_API_BASE: Base URL (optional)

    Examples:
        >>> config = ClaudeConfig()
        >>> config = ClaudeConfig(
        ...     api_key="sk-ant-xxx",
        ...     model="claude-3-opus-20240229"
        ... )
    """

    model: str = "claude-3-sonnet-20240229"
    api_base: Optional[str] = "https://api.anthropic.com"

    # Claude-specific parameters
    anthropic_version: str = Field(
        "2023-06-01",
        description="Anthropic API version"
    )
    max_tokens: int = Field(
        4096,
        gt=0,
        description="Maximum tokens to generate (required for Claude)"
    )

    @field_validator("api_key", mode="before")
    def load_api_key(cls, v):
        """Load API key from environment if not provided."""
        if v not in (None, ""):
            return v
        return os.getenv("ANTHROPIC_API_KEY") or os.getenv("CLAUDE_API_KEY")

    @field_validator("api_base", mode="before")
    def load_api_base(cls, v):
        """Load API base from environment if not provided."""
        if v not in (None, ""):
            return v
        return os.getenv("ANTHROPIC_API_BASE", "https://api.anthropic.com")
