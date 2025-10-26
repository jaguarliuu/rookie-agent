"""SSE (Server-Sent Events) streaming support.

This module provides utilities for handling Server-Sent Events (SSE),
commonly used for streaming responses from LLM APIs.
"""

import logging
from typing import Iterator, Optional, Dict, Any, AsyncIterator
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SSEEvent:
    """Represents a single Server-Sent Event.

    SSE格式说明:
    - data: 事件数据，可以有多行
    - event: 事件类型，可选
    - id: 事件ID，可选
    - retry: 重连时间（毫秒），可选

    Examples:
        >>> event = SSEEvent(data='{"message": "Hello"}', event="message")
        >>> event.data
        '{"message": "Hello"}'
    """

    data: str
    event: Optional[str] = None
    id: Optional[str] = None
    retry: Optional[int] = None

    def __str__(self) -> str:
        """Convert event to SSE format string."""
        lines = []

        if self.event:
            lines.append(f"event: {self.event}")

        if self.id:
            lines.append(f"id: {self.id}")

        if self.retry is not None:
            lines.append(f"retry: {self.retry}")

        # Data can be multiline
        for line in self.data.split('\n'):
            lines.append(f"data: {line}")

        lines.append('')  # Empty line to end event
        return '\n'.join(lines)

    @property
    def is_done(self) -> bool:
        """Check if this is a done event (often marked with [DONE])."""
        return self.data.strip() == '[DONE]'


class SSEParser:
    """Parser for Server-Sent Events stream.

    SSE协议规范:
    1. 每个事件由空行分隔
    2. 每行格式为 "field: value"
    3. 注释行以冒号开头
    4. data字段可以出现多次（多行数据）

    Examples:
        >>> parser = SSEParser()
        >>> for event in parser.parse_lines(lines):
        ...     print(event.data)
    """

    def __init__(self) -> None:
        """Initialize SSE parser."""
        self._reset_event()

    def _reset_event(self) -> None:
        """Reset current event state."""
        self._current_data: list[str] = []
        self._current_event: Optional[str] = None
        self._current_id: Optional[str] = None
        self._current_retry: Optional[int] = None

    def parse_line(self, line: str) -> Optional[SSEEvent]:
        """Parse a single line of SSE data.

        Args:
            line: A line from the SSE stream

        Returns:
            SSEEvent if an event is complete, None otherwise
        """
        line = line.rstrip('\n\r')

        # Empty line marks end of event
        if not line:
            if self._current_data or self._current_event:
                event = SSEEvent(
                    data='\n'.join(self._current_data),
                    event=self._current_event,
                    id=self._current_id,
                    retry=self._current_retry,
                )
                self._reset_event()
                return event
            return None

        # Comment line (ignore)
        if line.startswith(':'):
            return None

        # Parse field: value
        if ':' not in line:
            # Invalid line format, ignore
            logger.debug(f"Invalid SSE line format: {line}")
            return None

        field, _, value = line.partition(':')
        # Remove at most one leading space after colon, per SSE spec
        if value.startswith(' '):
            value = value[1:]

        # Handle different fields
        if field == 'data':
            self._current_data.append(value)
        elif field == 'event':
            self._current_event = value
        elif field == 'id':
            self._current_id = value
        elif field == 'retry':
            try:
                self._current_retry = int(value)
            except ValueError:
                logger.warning(f"Invalid retry value: {value}")
        else:
            logger.debug(f"Unknown SSE field: {field}")

        return None

    def parse_lines(self, lines: Iterator[str]) -> Iterator[SSEEvent]:
        """Parse multiple lines of SSE data.

        Args:
            lines: Iterator of lines from SSE stream

        Yields:
            SSEEvent objects as they are parsed

        Examples:
            >>> lines = [
            ...     "event: message",
            ...     "data: Hello",
            ...     "",
            ...     "data: World",
            ...     ""
            ... ]
            >>> parser = SSEParser()
            >>> events = list(parser.parse_lines(iter(lines)))
            >>> len(events)
            2
        """
        for line in lines:
            event = self.parse_line(line)
            if event is not None:
                yield event

        # Flush any remaining event
        if self._current_data or self._current_event:
            yield SSEEvent(
                data='\n'.join(self._current_data),
                event=self._current_event,
                id=self._current_id,
                retry=self._current_retry,
            )


class SSEStream:
    """Wrapper for SSE streaming response.

    提供便捷的SSE流式响应处理接口。

    Examples:
        >>> # Synchronous usage
        >>> with client.stream_get(url) as stream:
        ...     for event in stream:
        ...         print(event.data)
    """

    def __init__(self, response: Any) -> None:
        """Initialize SSE stream.

        Args:
            response: httpx.Response object with streaming enabled
        """
        self.response = response
        self.parser = SSEParser()

    def __enter__(self) -> "SSEStream":
        """Context manager entry."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit."""
        self.close()

    def close(self) -> None:
        """Close the underlying response."""
        if hasattr(self.response, 'close'):
            self.response.close()

    def __iter__(self) -> Iterator[SSEEvent]:
        """Iterate over SSE events.

        Yields:
            SSEEvent objects from the stream
        """
        try:
            for line in self.response.iter_lines():
                # Be tolerant of bytes in case upstream yields bytes
                if isinstance(line, (bytes, bytearray)):
                    try:
                        line = line.decode('utf-8')
                    except Exception:
                        line = line.decode('utf-8', 'ignore')
                event = self.parser.parse_line(line)
                if event is not None:
                    logger.debug(f"Received SSE event: {event.event or 'message'}")

                    # Stop on [DONE] event
                    if event.is_done:
                        logger.debug("Received [DONE] event, closing stream")
                        break

                    yield event
        finally:
            self.close()


class AsyncSSEStream:
    """Async wrapper for SSE streaming response.

    异步版本的SSE流式响应处理。

    Examples:
        >>> # Asynchronous usage
        >>> async with client.stream_get(url) as stream:
        ...     async for event in stream:
        ...         print(event.data)
    """

    def __init__(self, response: Any) -> None:
        """Initialize async SSE stream.

        Args:
            response: httpx.Response object with streaming enabled
        """
        self.response = response
        self.parser = SSEParser()

    async def __aenter__(self) -> "AsyncSSEStream":
        """Async context manager entry."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        await self.close()

    async def close(self) -> None:
        """Close the underlying response."""
        if hasattr(self.response, 'aclose'):
            await self.response.aclose()

    async def __aiter__(self) -> AsyncIterator[SSEEvent]:
        """Async iterate over SSE events.

        Yields:
            SSEEvent objects from the stream
        """
        try:
            async for line in self.response.aiter_lines():
                # Be tolerant of bytes in case upstream yields bytes
                if isinstance(line, (bytes, bytearray)):
                    try:
                        line = line.decode('utf-8')
                    except Exception:
                        line = line.decode('utf-8', 'ignore')
                event = self.parser.parse_line(line)
                if event is not None:
                    logger.debug(f"Received SSE event: {event.event or 'message'}")

                    # Stop on [DONE] event
                    if event.is_done:
                        logger.debug("Received [DONE] event, closing stream")
                        break

                    yield event
        finally:
            await self.close()
