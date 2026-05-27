"""feat-002 单元测试 — EventBus 发布订阅与取消订阅。"""
from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from tuicode.bus import EventBus
from tuicode.events import (
    AgentMessage,
    CursorMoved,
    FileModified,
    FileOpened,
    GitStatusChanged,
    SelectionChanged,
    TerminalOutput,
    ToolCallRequested,
)


# ── 辅助工具 ──────────────────────────────────────────────────────────────────

def make_collector(results: list) -> object:
    def handler(event):
        results.append(event)
    return handler


# ── 基础发布订阅 ──────────────────────────────────────────────────────────────

class TestSubscribeAndPublish:
    def test_file_opened(self):
        bus = EventBus()
        received = []
        bus.subscribe(FileOpened, received.append)
        event = FileOpened(path=Path("/a/b.py"))
        bus.publish(event)
        assert received == [event]

    def test_file_modified(self):
        bus = EventBus()
        received = []
        bus.subscribe(FileModified, received.append)
        event = FileModified(path=Path("/a/b.py"), changes="- old\n+ new")
        bus.publish(event)
        assert received == [event]

    def test_cursor_moved(self):
        bus = EventBus()
        received = []
        bus.subscribe(CursorMoved, received.append)
        event = CursorMoved(file=Path("/a/b.py"), line=10, col=4)
        bus.publish(event)
        assert received == [event]

    def test_selection_changed(self):
        bus = EventBus()
        received = []
        bus.subscribe(SelectionChanged, received.append)
        event = SelectionChanged(
            file=Path("/a/b.py"),
            start_line=1, start_col=0,
            end_line=3, end_col=5,
            text="hello",
        )
        bus.publish(event)
        assert received == [event]

    def test_terminal_output(self):
        bus = EventBus()
        received = []
        bus.subscribe(TerminalOutput, received.append)
        event = TerminalOutput(session_id="bash-1", text="$ ls\nfoo bar\n")
        bus.publish(event)
        assert received == [event]

    def test_agent_message(self):
        bus = EventBus()
        received = []
        bus.subscribe(AgentMessage, received.append)
        event = AgentMessage(agent_id="claude", content="Hello!")
        bus.publish(event)
        assert received == [event]

    def test_tool_call_requested(self):
        bus = EventBus()
        received = []
        bus.subscribe(ToolCallRequested, received.append)
        event = ToolCallRequested(
            agent_id="claude",
            tool="write_file",
            args={"path": "/a/b.py", "content": "x=1"},
            call_id="call-001",
        )
        bus.publish(event)
        assert received == [event]

    def test_git_status_changed(self):
        bus = EventBus()
        received = []
        bus.subscribe(GitStatusChanged, received.append)
        event = GitStatusChanged(
            changed_files=("src/foo.py",),
            branch="main",
            ahead=2,
        )
        bus.publish(event)
        assert received == [event]


# ── 注册顺序 ──────────────────────────────────────────────────────────────────

class TestOrdering:
    def test_handlers_called_in_registration_order(self):
        bus = EventBus()
        order = []
        bus.subscribe(FileOpened, lambda e: order.append("first"))
        bus.subscribe(FileOpened, lambda e: order.append("second"))
        bus.subscribe(FileOpened, lambda e: order.append("third"))
        bus.publish(FileOpened(path=Path("/x")))
        assert order == ["first", "second", "third"]

    def test_multiple_subscribers_each_receive_event(self):
        bus = EventBus()
        a, b = [], []
        bus.subscribe(TerminalOutput, a.append)
        bus.subscribe(TerminalOutput, b.append)
        event = TerminalOutput(session_id="s", text="hi")
        bus.publish(event)
        assert a == [event]
        assert b == [event]


# ── 取消订阅 ──────────────────────────────────────────────────────────────────

class TestUnsubscribe:
    def test_unsubscribe_stops_delivery(self):
        bus = EventBus()
        received = []
        unsub = bus.subscribe(FileOpened, received.append)
        bus.publish(FileOpened(path=Path("/a")))
        assert len(received) == 1

        unsub()
        bus.publish(FileOpened(path=Path("/b")))
        assert len(received) == 1  # 第二次发布不再收到

    def test_double_unsubscribe_is_safe(self):
        bus = EventBus()
        unsub = bus.subscribe(FileOpened, lambda e: None)
        unsub()
        unsub()  # 不应抛出

    def test_unsubscribe_only_removes_own_handler(self):
        bus = EventBus()
        a, b = [], []
        unsub_a = bus.subscribe(FileOpened, a.append)
        bus.subscribe(FileOpened, b.append)

        unsub_a()
        bus.publish(FileOpened(path=Path("/x")))
        assert a == []
        assert len(b) == 1


# ── 隔离性 ────────────────────────────────────────────────────────────────────

class TestIsolation:
    def test_different_event_types_do_not_cross(self):
        bus = EventBus()
        file_events, git_events = [], []
        bus.subscribe(FileOpened, file_events.append)
        bus.subscribe(GitStatusChanged, git_events.append)

        bus.publish(FileOpened(path=Path("/a")))
        assert len(file_events) == 1
        assert len(git_events) == 0

        bus.publish(GitStatusChanged(branch="main"))
        assert len(file_events) == 1
        assert len(git_events) == 1

    def test_no_subscribers_publish_is_safe(self):
        bus = EventBus()
        bus.publish(AgentMessage(agent_id="x", content="y"))  # 不应抛出


# ── async handler ─────────────────────────────────────────────────────────────

class TestAsyncHandlers:
    def test_async_handler_scheduled(self):
        bus = EventBus()
        received = []

        async def async_handler(event):
            received.append(event)

        async def run():
            bus.subscribe(FileOpened, async_handler)
            event = FileOpened(path=Path("/async"))
            bus.publish(event)
            await asyncio.sleep(0)  # 让 create_task 执行
            return received

        result = asyncio.run(run())
        assert len(result) == 1
        assert result[0].path == Path("/async")
