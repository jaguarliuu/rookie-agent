"""Tests for SSE streaming functionality."""

import pytest
from rookie_agent.http.streaming import SSEEvent, SSEParser


class TestSSEEvent:
    """Tests for SSEEvent dataclass."""

    def test_basic_event(self):
        """Test creating a basic event."""
        event = SSEEvent(data="Hello, World!")
        assert event.data == "Hello, World!"
        assert event.event is None
        assert event.id is None
        assert event.retry is None

    def test_full_event(self):
        """Test creating an event with all fields."""
        event = SSEEvent(
            data='{"message": "test"}',
            event="message",
            id="123",
            retry=3000
        )
        assert event.data == '{"message": "test"}'
        assert event.event == "message"
        assert event.id == "123"
        assert event.retry == 3000

    def test_multiline_data(self):
        """Test event with multiline data."""
        event = SSEEvent(data="line1\nline2\nline3")
        assert event.data == "line1\nline2\nline3"

    def test_is_done(self):
        """Test is_done property."""
        done_event = SSEEvent(data="[DONE]")
        assert done_event.is_done is True

        normal_event = SSEEvent(data="some data")
        assert normal_event.is_done is False

        # Test with whitespace
        done_with_space = SSEEvent(data="  [DONE]  ")
        assert done_with_space.is_done is True

    def test_str_format(self):
        """Test converting event to SSE format string."""
        event = SSEEvent(
            data="Hello",
            event="greeting",
            id="1"
        )
        result = str(event)
        assert "event: greeting" in result
        assert "id: 1" in result
        assert "data: Hello" in result
        assert result.endswith("\n")


class TestSSEParser:
    """Tests for SSEParser."""

    def test_parse_simple_event(self):
        """Test parsing a simple event."""
        parser = SSEParser()

        # Parse lines
        event = parser.parse_line("data: Hello")
        assert event is None  # Not complete yet

        event = parser.parse_line("")  # Empty line completes event
        assert event is not None
        assert event.data == "Hello"

    def test_parse_multiline_data(self):
        """Test parsing multiline data."""
        parser = SSEParser()

        parser.parse_line("data: line1")
        parser.parse_line("data: line2")
        parser.parse_line("data: line3")
        event = parser.parse_line("")

        assert event is not None
        assert event.data == "line1\nline2\nline3"

    def test_parse_full_event(self):
        """Test parsing event with all fields."""
        parser = SSEParser()

        parser.parse_line("event: update")
        parser.parse_line("id: 42")
        parser.parse_line("retry: 5000")
        parser.parse_line("data: test data")
        event = parser.parse_line("")

        assert event is not None
        assert event.event == "update"
        assert event.id == "42"
        assert event.retry == 5000
        assert event.data == "test data"

    def test_parse_comment_line(self):
        """Test that comment lines are ignored."""
        parser = SSEParser()

        event = parser.parse_line(": this is a comment")
        assert event is None

        parser.parse_line("data: actual data")
        event = parser.parse_line("")

        assert event is not None
        assert event.data == "actual data"

    def test_parse_invalid_retry(self):
        """Test handling invalid retry value."""
        parser = SSEParser()

        parser.parse_line("retry: not-a-number")
        parser.parse_line("data: test")
        event = parser.parse_line("")

        assert event is not None
        assert event.retry is None  # Invalid retry should be ignored

    def test_parse_lines_iterator(self):
        """Test parsing multiple events from iterator."""
        lines = [
            "event: msg1",
            "data: First message",
            "",
            "event: msg2",
            "data: Second message",
            "",
            "data: [DONE]",
            ""
        ]

        parser = SSEParser()
        events = list(parser.parse_lines(iter(lines)))

        assert len(events) == 3
        assert events[0].event == "msg1"
        assert events[0].data == "First message"
        assert events[1].event == "msg2"
        assert events[1].data == "Second message"
        assert events[2].data == "[DONE]"
        assert events[2].is_done is True

    def test_parse_field_with_colon_in_value(self):
        """Test parsing field with colon in the value."""
        parser = SSEParser()

        parser.parse_line("data: https://example.com:8080/path")
        event = parser.parse_line("")

        assert event is not None
        assert event.data == "https://example.com:8080/path"

    def test_parse_empty_data(self):
        """Test parsing event with empty data."""
        parser = SSEParser()

        parser.parse_line("data:")
        event = parser.parse_line("")

        assert event is not None
        assert event.data == ""

    def test_multiple_events_same_parser(self):
        """Test parsing multiple events with same parser instance."""
        parser = SSEParser()

        # First event
        parser.parse_line("data: Event 1")
        event1 = parser.parse_line("")
        assert event1.data == "Event 1"

        # Second event
        parser.parse_line("data: Event 2")
        event2 = parser.parse_line("")
        assert event2.data == "Event 2"

        # Events should be independent
        assert event1.data != event2.data

    def test_parse_openai_style_sse(self):
        """Test parsing OpenAI-style SSE events."""
        lines = [
            'data: {"id":"1","object":"chat.completion.chunk","choices":[{"delta":{"content":"Hello"}}]}',
            "",
            'data: {"id":"2","object":"chat.completion.chunk","choices":[{"delta":{"content":" World"}}]}',
            "",
            "data: [DONE]",
            ""
        ]

        parser = SSEParser()
        events = list(parser.parse_lines(iter(lines)))

        assert len(events) == 3
        assert '{"id":"1"' in events[0].data
        assert '{"id":"2"' in events[1].data
        assert events[2].is_done is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
