"""feat-009 测试 — AgentAdapter Protocol 完整定义 + mock 实现类型检查。"""
from __future__ import annotations

import asyncio
from typing import AsyncIterator

import pytest

from tuicode.agent_protocol import (
    AgentAdapter,
    AgentCapabilities,
    Chunk,
    Context,
    Session,
    ToolCall,
    ToolResult,
)


# ── Mock 实现 ─────────────────────────────────────────────────────────────────

class MockAgentAdapter:
    """最小化 mock 实现，用于验证 Protocol 接口可被正确实现。"""

    agent_id: str = "mock-agent"
    display_name: str = "Mock Agent"
    capabilities: AgentCapabilities = AgentCapabilities()

    async def start_session(self, ctx: Context) -> Session:
        return Session(session_id="mock-session-001", agent_id=self.agent_id)

    async def send_message(self, session: Session, content: str) -> None:
        pass

    async def stream_response(self, session: Session) -> AsyncIterator[Chunk]:
        async def _gen():
            yield Chunk(text="Hello ")
            yield Chunk(text="world!", is_done=True)
        return _gen()

    async def handle_tool_call(self, call: ToolCall) -> ToolResult:
        return ToolResult(call_id=call.call_id, approved=True, output="ok")

    async def stop_session(self, session: Session) -> None:
        pass


# ── Protocol 结构检查 ─────────────────────────────────────────────────────────

class TestProtocolDefinition:
    def test_mock_satisfies_runtime_checkable_protocol(self):
        adapter = MockAgentAdapter()
        assert isinstance(adapter, AgentAdapter)

    def test_protocol_requires_all_attributes(self):
        class Incomplete:
            agent_id = "x"
            # 缺少 display_name / capabilities / 方法

        obj = Incomplete()
        assert not isinstance(obj, AgentAdapter)

    def test_capabilities_defaults(self):
        caps = AgentCapabilities()
        assert caps.streaming is True
        assert caps.tool_use is True
        assert caps.multi_turn is True


# ── Mock 行为验证 ─────────────────────────────────────────────────────────────

class TestMockAdapter:
    def test_start_session_returns_session(self):
        async def run():
            adapter = MockAgentAdapter()
            ctx = Context()
            session = await adapter.start_session(ctx)
            assert isinstance(session, Session)
            assert session.agent_id == "mock-agent"
            return session

        asyncio.run(run())

    def test_send_message_does_not_raise(self):
        async def run():
            adapter = MockAgentAdapter()
            session = Session(session_id="s", agent_id="mock-agent")
            await adapter.send_message(session, "hello")

        asyncio.run(run())

    def test_stream_response_yields_chunks(self):
        async def run():
            adapter = MockAgentAdapter()
            session = Session(session_id="s", agent_id="mock-agent")
            gen = await adapter.stream_response(session)
            chunks = [c async for c in gen]
            assert len(chunks) == 2
            assert chunks[0].text == "Hello "
            assert chunks[1].is_done is True
            return chunks

        asyncio.run(run())

    def test_handle_tool_call_approved(self):
        async def run():
            adapter = MockAgentAdapter()
            call = ToolCall(call_id="c1", tool_name="read_file", args={"path": "/a"})
            result = await adapter.handle_tool_call(call)
            assert isinstance(result, ToolResult)
            assert result.approved is True
            assert result.call_id == "c1"

        asyncio.run(run())

    def test_stop_session_does_not_raise(self):
        async def run():
            adapter = MockAgentAdapter()
            session = Session(session_id="s", agent_id="mock-agent")
            await adapter.stop_session(session)

        asyncio.run(run())


# ── 数据类型完整性 ────────────────────────────────────────────────────────────

class TestDataTypes:
    def test_context_defaults(self):
        ctx = Context()
        assert ctx.active_file is None
        assert ctx.selection_text == ""
        assert ctx.recent_diffs == []

    def test_chunk_defaults(self):
        chunk = Chunk()
        assert chunk.text == ""
        assert chunk.is_tool_call is False
        assert chunk.is_done is False

    def test_tool_result_error_case(self):
        result = ToolResult(call_id="c2", approved=False, error="rejected by user")
        assert result.approved is False
        assert result.error == "rejected by user"
