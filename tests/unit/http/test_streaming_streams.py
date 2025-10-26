import asyncio
import types
import pytest

from src.rookie_agent.http.streaming import (
    SSEStream,
    AsyncSSEStream,
    SSEParser,
)


class FakeResponse:
    def __init__(self, lines):
        # lines: list of str or bytes
        self._lines = lines
        self.closed = False

    def iter_lines(self):
        for line in self._lines:
            yield line

    def close(self):
        self.closed = True


class FakeAsyncResponse:
    def __init__(self, lines):
        # lines: list of str or bytes
        self._lines = lines
        self.closed = False

    async def aiter_lines(self):
        for line in self._lines:
            # small await to simulate async iteration
            await asyncio.sleep(0)
            yield line

    async def aclose(self):
        self.closed = True


# ---------- SSEStream (sync) tests ----------

def test_sse_stream_basic_iteration_and_close():
    lines = [
        "data: hello",
        "",
        "data: world",
        "",
        "data: [DONE]",
        "",
    ]
    resp = FakeResponse(lines)
    events = []
    stream = SSEStream(resp)
    for evt in stream:
        events.append(evt)
    # Should close response even on break
    assert resp.closed is True
    # DONE event is not yielded
    assert all(not e.is_done for e in events)
    assert [e.data for e in events] == ["hello", "world"]


def test_sse_stream_decodes_bytes_and_stops_on_done():
    lines = [
        b"data: first",
        b"",
        b"data: second",
        b"",
        b"data: [DONE]",
        b"",
        b"data: after",  # should not be consumed
        b"",
    ]
    resp = FakeResponse(lines)
    events = list(SSEStream(resp))
    # response closed
    assert resp.closed is True
    # only first two yielded, DONE stops
    assert [e.data for e in events] == ["first", "second"]


# ---------- AsyncSSEStream tests ----------
@pytest.mark.asyncio
async def test_async_sse_stream_basic_iteration_and_close():
    lines = [
        "data: alpha",
        "",
        "data: beta",
        "",
        "data: [DONE]",
        "",
    ]
    resp = FakeAsyncResponse(lines)
    events = []
    async for evt in AsyncSSEStream(resp):
        events.append(evt)
    # closed after iteration
    assert resp.closed is True
    assert [e.data for e in events] == ["alpha", "beta"]
    assert all(not e.is_done for e in events)


@pytest.mark.asyncio
async def test_async_sse_stream_decodes_bytes_and_stops_on_done():
    lines = [
        b"data: one",
        b"",
        b"data: two",
        b"",
        b"data: [DONE]",
        b"",
        b"data: after",
        b"",
    ]
    resp = FakeAsyncResponse(lines)
    data = []
    async for evt in AsyncSSEStream(resp):
        data.append(evt.data)
    assert resp.closed is True
    assert data == ["one", "two"]


# ---------- Parser edge cases ----------

def test_parser_removes_only_one_leading_space_after_colon():
    parser = SSEParser()
    events = list(parser.parse_lines([
        "data:  leading",  # two spaces -> remove one => leading with one space
        "",
    ]))
    assert len(events) == 1
    assert events[0].data == " leading"

    # three spaces -> remove one -> keep two
    events = list(parser.parse_lines([
        "data:   leading",
        "",
    ]))
    assert len(events) == 1
    assert events[0].data == "  leading"


def test_parser_flush_without_trailing_empty_line():
    parser = SSEParser()
    # No trailing empty line; should still flush accumulated event
    events = list(parser.parse_lines([
        "data: tailonly",
    ]))
    assert len(events) == 1
    assert events[0].data == "tailonly"


def test_parser_ignores_invalid_lines_without_colon():
    parser = SSEParser()
    events = list(parser.parse_lines([
        "invalid",  # ignored
        "data: ok",
        "",
    ]))
    assert len(events) == 1
    assert events[0].data == "ok"