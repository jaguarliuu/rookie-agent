"""Type definitions for LLM interactions.

This module defines the unified message format and response types
used across all LLM providers, ensuring a consistent API surface.

Key Types:
- Message: Unified message format with multimodal support
- ChatCompletion: Non-streaming completion response
- CompletionChunk: Streaming chunk response
- FunctionDefinition/ToolDefinition: Function calling schemas
"""

from enum import Enum
from typing import List, Optional, Union, Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict


# ==================== Enumerations ====================


class MessageRole(str, Enum):
    """Message role in conversation.

    Defines who sent the message in the conversation flow.
    """

    SYSTEM = "system"  # System instructions/prompts
    USER = "user"  # User input
    ASSISTANT = "assistant"  # AI assistant response
    FUNCTION = "function"  # Function call result (OpenAI legacy)
    TOOL = "tool"  # Tool call result (OpenAI new format)


class ContentType(str, Enum):
    """Content type for multimodal messages.

    Supports different types of content in messages (text, images, etc.).
    """

    TEXT = "text"  # Plain text content
    IMAGE_URL = "image_url"  # Image from URL
    IMAGE_BASE64 = "image_base64"  # Base64-encoded image


class FinishReason(str, Enum):
    """Reason why generation finished.

    Indicates why the model stopped generating tokens.
    """

    STOP = "stop"  # Natural stop point (e.g., end of sentence)
    LENGTH = "length"  # Max tokens reached
    TOOL_CALLS = "tool_calls"  # Model wants to call a tool
    CONTENT_FILTER = "content_filter"  # Content filtered
    FUNCTION_CALL = "function_call"  # Model wants to call a function (legacy)


# ==================== Message Content ====================


class MessageContent(BaseModel):
    """Content block for multimodal messages.

    Supports text and image content types for vision-enabled models.

    Examples:
        Text content:
        >>> content = MessageContent(type=ContentType.TEXT, text="Hello")

        Image from URL:
        >>> content = MessageContent(
        ...     type=ContentType.IMAGE_URL,
        ...     image_url="https://example.com/image.jpg"
        ... )

        Image from Base64:
        >>> content = MessageContent(
        ...     type=ContentType.IMAGE_BASE64,
        ...     image_base64="iVBORw0KG..."
        ... )
    """

    type: ContentType
    text: Optional[str] = None
    image_url: Optional[str] = None
    image_base64: Optional[str] = None
    detail: Optional[Literal["auto", "low", "high"]] = "auto"  # Image detail level

    @model_validator(mode='after')
    def validate_content_fields(self) -> 'MessageContent':
        """Ensure required fields are present based on content type."""
        if self.type == ContentType.TEXT and not self.text:
            raise ValueError("text is required for TEXT content type")
        if self.type == ContentType.IMAGE_URL and not self.image_url:
            raise ValueError("image_url is required for IMAGE_URL content type")
        if self.type == ContentType.IMAGE_BASE64 and not self.image_base64:
            raise ValueError("image_base64 is required for IMAGE_BASE64 content type")
        return self


# ==================== Messages ====================


class Message(BaseModel):
    """Unified message format across all providers.

    Represents a single message in the conversation, supporting both
    simple text content and multimodal content (text + images).

    Attributes:
        role: Who sent this message (system/user/assistant/tool)
        content: Message content (string or list of content blocks)
        name: Optional name of the sender
        function_call: Legacy function call format (OpenAI)
        tool_calls: New tool calls format (OpenAI)

    Examples:
        Simple text message:
        >>> msg = Message(role=MessageRole.USER, content="Hello!")

        System message:
        >>> msg = Message(
        ...     role=MessageRole.SYSTEM,
        ...     content="You are a helpful assistant."
        ... )

        Multimodal message (text + image):
        >>> msg = Message(
        ...     role=MessageRole.USER,
        ...     content=[
        ...         MessageContent(type=ContentType.TEXT, text="What's in this image?"),
        ...         MessageContent(type=ContentType.IMAGE_URL, image_url="https://...")
        ...     ]
        ... )

        Tool response message:
        >>> msg = Message(
        ...     role=MessageRole.TOOL,
        ...     content="Weather is sunny, 25°C",
        ...     name="get_weather"
        ... )
    """

    role: MessageRole
    content: Union[str, List[MessageContent]]
    name: Optional[str] = None
    function_call: Optional[Dict[str, Any]] = None  # Legacy OpenAI format
    tool_calls: Optional[List[Dict[str, Any]]] = None  # New OpenAI format

    model_config = ConfigDict(use_enum_values=True)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for API calls.

        Returns:
            Dictionary representation suitable for API requests
        """
        result: Dict[str, Any] = {"role": self.role}

        # Handle content
        if isinstance(self.content, str):
            result["content"] = self.content
        else:
            result["content"] = [
                {
                    "type": c.type.value,
                    **({"text": c.text} if c.text else {}),
                    **({"image_url": {"url": c.image_url, "detail": c.detail}}
                       if c.image_url else {}),
                    # Base64 images need data URI format
                    **({"image_url": {"url": f"data:image/jpeg;base64,{c.image_base64}",
                                      "detail": c.detail}}
                       if c.image_base64 else {}),
                }
                for c in self.content
            ]

        # Optional fields
        if self.name:
            result["name"] = self.name
        if self.function_call:
            result["function_call"] = self.function_call
        if self.tool_calls:
            result["tool_calls"] = self.tool_calls

        return result

    @property
    def is_multimodal(self) -> bool:
        """Check if message contains multimodal content."""
        return isinstance(self.content, list)

    @property
    def has_images(self) -> bool:
        """Check if message contains images."""
        if not self.is_multimodal:
            return False
        return any(
            c.type in (ContentType.IMAGE_URL, ContentType.IMAGE_BASE64)
            for c in self.content  # type: ignore
        )


# ==================== Function/Tool Calling ====================


class FunctionDefinition(BaseModel):
    """Function definition for function calling.

    Defines a function that the model can call, including its
    parameters schema in JSON Schema format.

    Examples:
        >>> func = FunctionDefinition(
        ...     name="get_weather",
        ...     description="Get current weather for a city",
        ...     parameters={
        ...         "type": "object",
        ...         "properties": {
        ...             "city": {"type": "string", "description": "City name"},
        ...             "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}
        ...         },
        ...         "required": ["city"]
        ...     }
        ... )
    """

    name: str = Field(..., description="Function name")
    description: str = Field(..., description="Function description")
    parameters: Dict[str, Any] = Field(
        ...,
        description="Function parameters in JSON Schema format"
    )


class ToolDefinition(BaseModel):
    """Tool definition for tool calling.

    Wraps a function definition in the tool format expected by APIs.

    Examples:
        >>> tool = ToolDefinition(
        ...     type="function",
        ...     function=FunctionDefinition(
        ...         name="search",
        ...         description="Search the web",
        ...         parameters={"type": "object", "properties": {...}}
        ...     )
        ... )
    """

    type: Literal["function"] = "function"
    function: FunctionDefinition


class ToolCall(BaseModel):
    """Tool call request from the model.

    Represents a tool that the model wants to call.

    Attributes:
        id: Unique identifier for this tool call
        type: Type of tool (always "function" currently)
        function: Function call details (name and arguments)

    Examples:
        >>> call = ToolCall(
        ...     id="call_abc123",
        ...     type="function",
        ...     function={"name": "get_weather", "arguments": '{"city": "Beijing"}'}
        ... )
    """

    id: str
    type: Literal["function"] = "function"
    function: Dict[str, str]  # {"name": str, "arguments": str}


# ==================== Completion Responses ====================


class CompletionUsage(BaseModel):
    """Token usage information.

    Tracks the number of tokens used in the completion.

    Attributes:
        prompt_tokens: Tokens in the input prompt
        completion_tokens: Tokens in the generated completion
        total_tokens: Total tokens used (prompt + completion)
    """

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class CompletionChoice(BaseModel):
    """A single completion choice.

    Represents one possible completion from the model.

    Attributes:
        index: Index of this choice
        message: The generated message
        finish_reason: Why generation stopped
    """

    index: int
    message: Message
    finish_reason: Optional[FinishReason] = None

    model_config = ConfigDict(use_enum_values=True)


class ChatCompletion(BaseModel):
    """Non-streaming chat completion response.

    The unified response format for non-streaming completions.

    Attributes:
        id: Unique completion ID
        object: Object type (always "chat.completion")
        created: Unix timestamp of creation
        model: Model used for generation
        choices: List of completion choices
        usage: Token usage information

    Examples:
        >>> completion = ChatCompletion(
        ...     id="chatcmpl-123",
        ...     object="chat.completion",
        ...     created=1677858242,
        ...     model="gpt-4",
        ...     choices=[
        ...         CompletionChoice(
        ...             index=0,
        ...             message=Message(role=MessageRole.ASSISTANT, content="Hello!"),
        ...             finish_reason=FinishReason.STOP
        ...         )
        ...     ],
        ...     usage=CompletionUsage(
        ...         prompt_tokens=10,
        ...         completion_tokens=5,
        ...         total_tokens=15
        ...     )
        ... )
    """

    id: str
    object: Literal["chat.completion"] = "chat.completion"
    created: int
    model: str
    choices: List[CompletionChoice]
    usage: CompletionUsage


class CompletionChunk(BaseModel):
    """Streaming completion chunk.

    Represents a single chunk in a streaming response.

    Attributes:
        id: Unique completion ID (same across all chunks)
        object: Object type (always "chat.completion.chunk")
        created: Unix timestamp
        model: Model used
        choices: List of delta choices (partial content)

    Examples:
        >>> chunk = CompletionChunk(
        ...     id="chatcmpl-123",
        ...     object="chat.completion.chunk",
        ...     created=1677858242,
        ...     model="gpt-4",
        ...     choices=[
        ...         {
        ...             "index": 0,
        ...             "delta": {"role": "assistant", "content": "Hello"},
        ...             "finish_reason": None
        ...         }
        ...     ]
        ... )
    """

    id: str
    object: Literal["chat.completion.chunk"] = "chat.completion.chunk"
    created: int
    model: str
    choices: List[Dict[str, Any]]  # Delta format: {"index", "delta", "finish_reason"}

    @property
    def is_done(self) -> bool:
        """Check if this is the final chunk.

        Returns:
            True if any choice has a finish_reason
        """
        return any(
            choice.get("finish_reason") is not None
            for choice in self.choices
        )

    def get_content(self) -> Optional[str]:
        """Extract content from delta.

        Returns:
            Content string if present, None otherwise
        """
        if not self.choices:
            return None

        delta = self.choices[0].get("delta", {})
        return delta.get("content")
